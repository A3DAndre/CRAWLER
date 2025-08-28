from typing import Any, Callable, Protocol
import boto3
import json
import time
from boto3.session import Session
from aws.iam_stmt import IamStatement, StmtIAM, StatementFunction

def create_role_policy(agent_name: str, stmt_fns: list[StatementFunction] = None) -> dict[str, Any]:
    """
    Create a role policy with dynamic statements
    
    Args:
        agent_name: Name of the agent
        stmt_fns: List of statement functions that take (region, account_id) and return IAM statements
    
    Returns:
        Complete IAM role policy document
    """
    if stmt_fns is None:
        stmt_fns = []
    
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    
    # Base policy statements
    base_statements: list[IamStatement] = StmtIAM.base_agentcore_stmts(agent_name,region, account_id)
    
    role_policy: dict[str, Any] = {
        "Version": "2012-10-17",
        "Statement": base_statements.copy()
    }
    
    # Add dynamic statements by calling each function
    for stmt_fn in stmt_fns:
        dynamic_statement = stmt_fn(region, account_id)
        role_policy["Statement"].append(dynamic_statement)
    
    return role_policy

def create_assume_role_policy(account_id: str, region: str) -> dict[str, Any]:
    """Create assume role policy document"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": f"{account_id}"
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    }
                }
            }
        ]
    }

def create_agentcore_role(agent_name: str, stmt_fns: list[StatementFunction] = None) -> dict[str, Any]:
    """
    Create an agentcore IAM role with dynamic statements
    
    Args:
        agent_name: Name of the agent
        stmt_fns: List of statement functions
    
    Returns:
        Created IAM role response
    """
    if stmt_fns is None:
        stmt_fns = []
        
    iam_client = boto3.client('iam')
    agentcore_role_name = f'agentcore-{agent_name}-role'
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    
    # Create policy documents
    role_policy = create_role_policy(agent_name, stmt_fns)
    assume_role_policy = create_assume_role_policy(account_id, region)
    
    assume_role_policy_json = json.dumps(assume_role_policy)
    role_policy_json = json.dumps(role_policy)
    
    # Create or recreate the IAM role
    try:
        agentcore_iam_role = iam_client.create_role(
            RoleName=agentcore_role_name,
            AssumeRolePolicyDocument=assume_role_policy_json
        )
        time.sleep(10)
    except iam_client.exceptions.EntityAlreadyExistsException:
        print("Role already exists -- deleting and creating it again")
        # Clean up existing policies
        policies = iam_client.list_role_policies(
            RoleName=agentcore_role_name,
            MaxItems=100
        )
        for policy_name in policies['PolicyNames']:
            iam_client.delete_role_policy(
                RoleName=agentcore_role_name,
                PolicyName=policy_name
            )
        # Delete and recreate role
        iam_client.delete_role(RoleName=agentcore_role_name)
        agentcore_iam_role = iam_client.create_role(
            RoleName=agentcore_role_name,
            AssumeRolePolicyDocument=assume_role_policy_json
        )
    
    # Attach the policy
    try:
        iam_client.put_role_policy(
            PolicyDocument=role_policy_json,
            PolicyName="AgentCorePolicy",
            RoleName=agentcore_role_name
        )
    except Exception as e:
        print(f"Error attaching policy: {e}")
    
    return agentcore_iam_role

# Usage examples:
if __name__ == "__main__":
    # Create statement functions
    s3_vectors_stmt = StmtIAM.query_s3_vectors("my-bucket", "my-index")
    s3_bucket_stmt = StmtIAM.s3_bucket_access("my-bucket")
    lambda_stmt = StmtIAM.lambda_invoke_function("my-function")
    
    # Create role with dynamic statements
    statements: list[StatementFunction] = [
        s3_vectors_stmt,
        s3_bucket_stmt,
        lambda_stmt
    ]
    
    role = create_agentcore_role("my-agent", statements)
    print(f"Created role: {role['Role']['RoleName']}")