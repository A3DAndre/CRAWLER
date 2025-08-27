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

        boto3_response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": "Me conte sobre o buora?"}),
        )
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
        sys.exit(1)
        
    if "text/event-stream" in boto3_response.get("contentType", ""):
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                print(line)
                # if line.startswith("data: "):
                    # line = line[6:]
                    # content.append(line)
        # print("\n".join(content))1
        # display(Markdown("\n".join(content)))
    else:
        try:
            events = []
            for event in boto3_response.get("response", []):
                events.append(event)
        except Exception as e:
            events = [f"Error reading EventStream: {e}"]
        # display(Markdown(json.loads(events[0].decode("utf-8"))))
        print(json.loads(events[0].decode("utf-8")))
        
if __name__ == "__main__":
    asyncio.run(main())