import requests
import urllib.parse
import json
import os
import boto3
from boto3.session import Session

# Configuration Constants
boto_session = Session()
region = boto_session.region_name
REGION_NAME = region
ssm_client = boto3.client('ssm', region_name=region)
agent_arn_response = ssm_client.get_parameter(Name='/agent_a3_wiki_agentcore/runtime/agent_arn')
agent_arn = agent_arn_response['Parameter']['Value']
print(f"Retrieved Agent ARN: {agent_arn}")
# === Agent Invocation Demo ===
invoke_agent_arn =agent_arn
print(f"Using Agent ARN from environment: {invoke_agent_arn}")
# 
secrets_client = boto3.client('secretsmanager', region_name=region)
response = secrets_client.get_secret_value(SecretId='/agent_a3_wiki_agentcore/cognito/credentials')
secret_value = response['SecretString']
parsed_secret = json.loads(secret_value)
bearer_token = parsed_secret['bearer_token']
# bearer_token = "eyJraWQiOiJidlRrekNIZWk0V09md0pzTFwvTTBqUnJQU1RhZkJmOFNSblc5Z3JOUDZHRT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI5OGYxZTM3MC00MGIxLTcwMTAtNTk0YS04YTY3NGViMDdjOGEiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9SM05seXZJOU8iLCJjbGllbnRfaWQiOiI0YXMxNGx1OThjbXZuMjE0ZDVlN2drdmZ1NiIsIm9yaWdpbl9qdGkiOiJiNWM5NTM2ZS05MjJhLTQ2OTUtODMyNy1hZTlhMDc2Zjc0ZGUiLCJldmVudF9pZCI6IjBiODJlMGFiLWIzYWItNGE5ZS04ZmU2LTdhMGVkZTVlZWMzNSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3NTY0MDcyMTksImV4cCI6MTc1NjQxMDgxOSwiaWF0IjoxNzU2NDA3MjE5LCJqdGkiOiIwMTQ4ZTI5ZC0xYmQ0LTQ2ZmQtYjU1My1lMTQ5MThiYTllZDIiLCJ1c2VybmFtZSI6InRlc3R1c2VyIn0.1sm_W0NWEJ7TQxZg_Wh_Cpl2Sjj3TRremSSEWZCvFAem9GpADL_zVN6kylkIqGidScMJaNIF9g9cr6pRI6awQoEQyLDByME4qHAvCbPxalml5yyWOvxQ6C_BcIE-r6EiJRzwJOmq57c89vJ5dxvhXm0qwo7Nis6AQhRbrjqx5TBaiQsAZxcaVOpd7XxH1Chiw8U62vHw428HJ4gyfyX4o8DMi2DPP5ukMRXfo2wcTahfMi7_uWc6AphO79D87QPebkHlEAwXLaIFATrxgC3QxK5AY37PtkMI45z75x_Iaruna9kWCryj9LmTFcCOzHgGydIUj_k4RbbWAXuGYN1CKw"
print("✓ Retrieved bearer token from Secrets Manager")
auth_token = bearer_token
# URL encode the agent ARN
print(auth_token)
escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')

# Construct the URL
url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"

# Set up headers
headers = {
    "Authorization": f"Bearer {auth_token}",
    "X-Amzn-Trace-Id": "testsession12321873872837827387232787327", 
    "Content-Type": "application/json",
    "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": "testsession12321873872837827387232787327"
}

# Enable verbose logging for requests
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

invoke_response = requests.post(
    url,
    headers=headers,
    data=json.dumps({"prompt": "Me conte sobre a cli de templates?"})
)

# Print response in a safe manner
print(f"Status Code: {invoke_response.status_code}")
print(f"Response Headers: {dict(invoke_response.headers)}")

print(invoke_response.text)
# Handle response based on status code
# if invoke_response.status_code == 200:
#     response_data = invoke_response.json()
#     print("Response JSON:")
#     print(json.dumps(response_data, indent=2))  
# elif invoke_response.status_code >= 400:
#     print(f"Error Response ({invoke_response.status_code}):")
#     error_data = invoke_response.json()
#     print(json.dumps(error_data, indent=2))
    
# else:
#     print(f"Unexpected status code: {invoke_response.status_code}")
#     print("Response text:")
#     print(invoke_response.text[:500])