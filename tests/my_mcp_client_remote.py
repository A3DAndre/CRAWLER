import asyncio
import json
import sys
from datetime import timedelta

import boto3
from boto3.session import Session
from mcp.client.streamable_http import streamablehttp_client

from mcp import ClientSession


async def main():
    boto_session = Session()
    region = boto_session.region_name

    print(f"Using AWS region: {region}")

    try:
        ssm_client = boto3.client("ssm", region_name=region)
        agent_arn_response = ssm_client.get_parameter(
            Name="/mcp_a3_wiki_agentcore/runtime/agent_arn"
        )
        agent_arn = agent_arn_response["Parameter"]["Value"]
        print(f"Retrieved Agent ARN: {agent_arn}")

        secrets_client = boto3.client("secretsmanager", region_name=region)
        response = secrets_client.get_secret_value(
            SecretId="mcp_a3_wiki_agentcore/cognito/credentials"
        )
        secret_value = response["SecretString"]
        parsed_secret = json.loads(secret_value)
        bearer_token = parsed_secret["bearer_token"]
        print("✓ Retrieved bearer token from Secrets Manager")

    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        sys.exit(1)

    if not agent_arn or not bearer_token:
        print("Error: AGENT_ARN or BEARER_TOKEN not retrieved properly")
        sys.exit(1)

    encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    headers = {
        "authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    print(f"\nConnecting to: {mcp_url}")
    print("Headers configured ✓")

    try:
        async with streamablehttp_client(
            mcp_url, headers, timeout=timedelta(seconds=120), terminate_on_close=False
        ) as (
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
                    print(f"🔧 {tool.name}")
                    print(f"   Description: {tool.description}")
                    if hasattr(tool, "inputSchema") and tool.inputSchema:
                        properties = tool.inputSchema.get("properties", {})
                        if properties:
                            print(f"   Parameters: {list(properties.keys())}")
                    print()

                print(f"✅ Successfully connected to MCP server!")
                print(f"Found {len(tool_result.tools)} tools available.")

    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print(f"Error detailds: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
