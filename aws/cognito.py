from typing import Any
import boto3
import json
import time
from boto3.session import Session
import os
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import time

POOL_NAME = "MCPServerPool"
POOL_CLIENT_NAME = "MCPServerPoolClient"

TEST_USERNAME = "testuser"
TEST_PASSWORD = "MyPassword123!"

def reauthenticate_user(client_id):
    boto_session = Session()
    region = boto_session.region_name
    cognito_client = boto3.client('cognito-idp', region_name=region)
    print("Reauthenticating user...")
    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': TEST_USERNAME,
            'PASSWORD': TEST_PASSWORD
        }
    )
    bearer_token = auth_response['AuthenticationResult']['AccessToken']
    return bearer_token

def is_token_valid(bearer_token):
    boto_session = Session()
    region = boto_session.region_name
    cognito_client = boto3.client('cognito-idp', region_name=region)    
    try:
        cognito_client.get_user(AccessToken=bearer_token)
        return True
    except cognito_client.exceptions.NotAuthorizedException:
        return False

def setup_cognito(agent_name: str):
    try:
        cognito_config =  get_cognito_config(agent_name)
        if cognito_config is not None:
            return cognito_config
    except Exception as e:
        print(f"Error: {e}")
    try:
        cognito_config = create_cognito_config(agent_name)   
        return cognito_config
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_cognito_config(agent_name:str):
    boto_session = Session()
    region = boto_session.region_name
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    secrets_client = boto3.client('secretsmanager', region_name=region)
     # Create User Pool
    user_pool_response = cognito_client.create_user_pool(
        PoolName=POOL_NAME,
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8
            }
        }
    )
    pool_id = user_pool_response['UserPool']['Id']
    # Create App Client
    app_client_response = cognito_client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName='MCPServerPoolClient',
        GenerateSecret=False,
        ExplicitAuthFlows=[
            'ALLOW_USER_PASSWORD_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH'
        ]
    )
    client_id = app_client_response['UserPoolClient']['ClientId']
    # Create User
    cognito_client.admin_create_user(
        UserPoolId=pool_id,
        Username=TEST_USERNAME,
        TemporaryPassword='Temp123!',
        MessageAction='SUPPRESS'
    )
    # Set Permanent Password
    cognito_client.admin_set_user_password(
        UserPoolId=pool_id,
        Username=TEST_USERNAME,
        Password=TEST_PASSWORD,
        Permanent=True
    )
    # Authenticate User and get Access Token
    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': TEST_USERNAME,
            'PASSWORD': TEST_PASSWORD
        }
    )
    bearer_token = auth_response['AuthenticationResult']['AccessToken']
    print(f"Pool id: {pool_id}")
    print(f"Discovery URL: https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration")
    print(f"Client ID: {client_id}")
    print(f"Bearer Token: {bearer_token}")
    
    cognito_config = {
        'pool_id': pool_id,
        'client_id': client_id,
        'bearer_token': bearer_token,
        'discovery_url':f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration"
    }
    save_cognito_config(agent_name, cognito_config)
    return cognito_config


def save_cognito_config(agent_name: str, cognito_config: dict[str, Any]):
    boto_session = Session()
    region = boto_session.region_name
    secrets_client = boto3.client('secretsmanager', region_name=region)
    print(f"Storing Cognito credentials for {agent_name}")
    try:
        cognito_credentials_response = secrets_client.create_secret(
            Name=f'/{agent_name}/cognito/credentials',
            Description=f'Cognito credentials for {agent_name}',
            SecretString=json.dumps(cognito_config)
        )
        print("✓ Cognito credentials stored in Secrets Manager")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.update_secret(
            SecretId=f'/{agent_name}/cognito/credentials',
            SecretString=json.dumps(cognito_config)
        )
        print("✓ Cognito credentials updated in Secrets Manager")
        
        
def get_cognito_config(agent_name: str):
    boto_session = Session()
    region = boto_session.region_name
    secrets_client = boto3.client('secretsmanager', region_name=region)

    try:
        # Get Existing User Pool
        existing_credentials_response = secrets_client.get_secret_value(
            SecretId=f'/{agent_name}/cognito/credentials'
        )
        existing_credentials: dict[str, Any] = json.loads(existing_credentials_response['SecretString'])

        bearer_token = existing_credentials.get('bearer_token')

        if (bearer_token is not None) and not is_token_valid(bearer_token):
            print("Config found but Bearer token is invalid.")
            bearer_token = reauthenticate_user(existing_credentials['client_id'])
            
            if not is_token_valid(bearer_token):
                print("Re-authentication failed, please check credentials.")
                return None
            
            existing_credentials['bearer_token'] = bearer_token
            save_cognito_config(agent_name, existing_credentials)

        return existing_credentials
    except secrets_client.exceptions.ResourceNotFoundException:
        print("No existing Cognito credentials found.")
        return None