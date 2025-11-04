from typing import Any, Callable, Protocol
import boto3
import json
import time
from boto3.session import Session
from aws.iam_stmt import IamStatement, Stmt, StatementFunction

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
    account_id: str = boto3.client("sts").get_caller_identity()["Account"]
    
    stmts= Stmt.base_agentcore(agent_name)(region, account_id)

    for stmt_fn in stmt_fns:
        dynamic_statement = stmt_fn(region, account_id)
        stmts.extend(dynamic_statement)
    
    return {
        "Version": "2012-10-17",
        "Statement": stmts,
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
    assume_role_policy = Stmt.agent_core_assume_role(account_id)(region, account_id)[0]
    
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