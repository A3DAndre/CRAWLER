import boto3
from boto3.session import Session
import asyncio
import boto3
import json
import sys
# from IPython.display import Markdown, display

async def main():
    boto_session = Session()
    region = boto_session.region_name

    try:
        ssm_client = boto3.client('ssm', region_name=region)
        agent_arn_response = ssm_client.get_parameter(Name='/agent_a3_wiki_agentcore/runtime/agent_arn')
        agent_arn = agent_arn_response['Parameter']['Value']
        print(f"Retrieved Agent ARN: {agent_arn}")
        
        agentcore_client = boto3.client(
            'bedrock-agentcore',
            region_name=region
        )

        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": "Me conte sobre o buora?"}),
        )
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        sys.exit(1)
    print(response)
    # Process and print the response
    if "text/event-stream" in response.get("contentType", ""):
    
        # Handle streaming response
        content = []
        for line in response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)
        print("\nComplete response:", "\n".join(content))

    elif response.get("contentType") == "application/json":
        # Handle standard JSON response
        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        print(json.loads(''.join(content)))
    
    else:
        # Print raw response for other content types
        print(response)
        
if __name__ == "__main__":
    asyncio.run(main())