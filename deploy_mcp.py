import json
import os
import time

import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

from aws.cognito import setup_cognito

# from aws.iam import create_agentcore_role
from aws.helpers import create_agentcore_role
from aws.iam_stmt import Stmt

AGENT_NAME = "mcp_a3_wiki_agentcore"
ENTRYPOINT = "mcp/a3wiki/mcp_server.py"
REQUIRED_FILES: list[str] = [ENTRYPOINT, "requirements.txt"]
AUTH = True  # Enable authentication

IAM_STMTS = [Stmt.query_s3_vectors("a3wiki", "github2")]


def configure_auth():  # -> dict[str, dict[str, Any]]:
    print("Setting up Amazon Cognito user pool...", flush=True)
    cognito_config = setup_cognito(AGENT_NAME)
    if cognito_config is None:
        raise RuntimeError("Failed to set up Cognito configuration")
    print("Cognito setup completed ✓")
    print(f"User Pool ID: {cognito_config.get('user_pool_id', 'N/A')}")
    print(f"Client ID: {cognito_config.get('client_id', 'N/A')}")
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [cognito_config["client_id"]],
            "discoveryUrl": cognito_config["discovery_url"],
        }
    }
    return auth_config


def configure_agent():
    boto_session = Session()
    region = boto_session.region_name
    print(f"Using AWS region: {region}")

    agentcore_runtime = Runtime()

    print(f"Creating IAM role for {AGENT_NAME}...")
    agentcore_iam_role = create_agentcore_role(AGENT_NAME, IAM_STMTS)
    agentcore_iam_role_arn = agentcore_iam_role["Role"]["Arn"]
    print(f"IAM role created ✓")
    print(f"Role ARN: {agentcore_iam_role_arn}")

    if agentcore_iam_role_arn is None:
        raise ValueError("IAM role ARN is None")

    print("Configuring AgentCore Runtime...")

    response = agentcore_runtime.configure(
        entrypoint=ENTRYPOINT,
        # auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        protocol="MCP",
        authorizer_configuration=configure_auth() if AUTH else None,
        agent_name=AGENT_NAME,
        execution_role=agentcore_iam_role["Role"]["Arn"],
    )
    print("Configuration completed ✓")
    print(response)
    print("Launching MCP server to AgentCore Runtime...")
    print("This may take several minutes...")
    launch_result = agentcore_runtime.launch()
    print("Launch completed ✓")
    print(f"Agent ARN: {launch_result.agent_arn}")
    print(f"Agent ID: {launch_result.agent_id}")

    ssm_client = boto3.client("ssm", region_name=region)
    agent_arn_response = ssm_client.put_parameter(
        Name=f"/{AGENT_NAME}/runtime/agent_arn",
        Value=launch_result.agent_arn,
        Type="String",
        Description="Agent ARN for MCP server",
        Overwrite=True,
    )
    print("✓ Agent ARN stored in Parameter Store")
    print("\nConfiguration stored successfully!")
    print(f"Agent ARN: {launch_result.agent_arn}")


if __name__ == "__main__":
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            raise FileNotFoundError(f"Required file {file} not found")
    print("All required files found ✓")

    configure_agent()
