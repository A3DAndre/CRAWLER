import asyncio
import boto3
import json
import sys
from boto3.session import Session
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    boto_session = Session()
    region = boto_session.region_name

    print(f"Using AWS region: {region}")

    try:
        ssm_client = boto3.client('ssm', region_name=region)
        agent_arn_response = ssm_client.get_parameter(Name='/mcp_server/runtime/agent_arn')
        agent_arn = agent_arn_response['Parameter']['Value']
        print(f"Retrieved Agent ARN: {agent_arn}")

        secrets_client = boto3.client('secretsmanager', region_name=region)
        response = secrets_client.get_secret_value(SecretId='mcp_server/cognito/credentials')
        secret_value = response['SecretString']
        parsed_secret = json.loads(secret_value)
        bearer_token = parsed_secret['bearer_token']
        print("✓ Retrieved bearer token from Secrets Manager")

    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        sys.exit(1)

    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    headers = {
        "authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    print(f"\nConnecting to: {mcp_url}")

    try:
        async with streamablehttp_client(mcp_url, headers, timeout=timedelta(seconds=120), terminate_on_close=False) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                print("\n🔄 Initializing MCP session...")
                await session.initialize()
                print("✓ MCP session initialized")

                print("\n🔄 Listing available tools...")
                tool_result = await session.list_tools()

                print("\n📋 Available MCP Tools:")
                print("=" * 50)
                for tool in tool_result.tools:
                    print(f"🔧 {tool.name}: {tool.description}")

                print("\n🧪 Testing MCP Tools:")
                print("=" * 50)

                # try:
                #     print("\n➕ Testing add_numbers(5, 3)...")
                #     add_result = await session.call_tool(
                #         name="add_numbers",
                #         arguments={"a": 5, "b": 3}
                #     )
                #     print(f"   Result: {add_result.content[0].text}")
                # except Exception as e:
                #     print(f"   Error: {e}")

                # try:
                #     print("\n✖️  Testing multiply_numbers(4, 7)...")
                #     multiply_result = await session.call_tool(
                #         name="multiply_numbers",
                #         arguments={"a": 4, "b": 7}
                #     )
                #     print(f"   Result: {multiply_result.content[0].text}")
                # except Exception as e:
                #     print(f"   Error: {e}")

                try:
                    print("\n👋 Testing greet_user('Alice')...")
                    greet_result = await session.call_tool(
                        name="greet_user",
                        arguments={"name": "Alice"}
                    )
                    print(f"   Result: {greet_result.content[0].text}")
                except Exception as e:
                    print(f"   Error: {e}")
                    
                try:
                    print("\n Testing A3Wiki Search Tool")
                    a3_wiki_result = await session.call_tool(
                        name="search_a3_wiki",
                        arguments={"query": "Buora Framework"}
                    )
                    print(f"   Result: {a3_wiki_result.content[0].text}")
                    print(f"   (truncated) Result: {a3_wiki_result.content[0].text[:500]}...")
                except Exception as e:
                    print(f"   Error: {e}")

                print("\n✅ MCP tool testing completed!")

    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
