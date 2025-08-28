from typing import Any, Callable, Protocol
import boto3
import json
import time
from boto3.session import Session

# Define the type for IAM statement dictionaries
IamStatement = dict[str, Any]

# Protocol for statement functions - more flexible than Callable
class StatementFunction(Protocol):
    def __call__(self, region: str, account_id: str) -> IamStatement:
        ...

# Alternative: Using Callable type annotation
StatementCallable = Callable[[str, str], IamStatement]

class StmtIAM:
    """IAM Statement builder class with proper typing"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def query_s3_vectors(bucket_name: str, index_name: str) -> StatementFunction:
        """Returns a function that generates S3 vectors query statement"""
        def stmt(region: str, account_id: str) -> IamStatement:
            return {
                "Sid": "S3VectorsQueryAccess",
                "Effect": "Allow",
                "Action": [
                    "s3vectors:QueryVectors",
                    "s3vectors:GetVectors",
                    "s3vectors:ListVectors"
                ],
                "Resource": [
                    f"arn:aws:s3vectors:{region}:{account_id}:bucket/{bucket_name}/index/{index_name}"
                ]
            }
        return stmt
    
    @staticmethod
    def s3_bucket_access(bucket_name: str) -> StatementFunction:
        """Returns a function that generates S3 bucket access statement"""
        def stmt(region: str, account_id: str) -> IamStatement:
            return {
                "Sid": "S3BucketAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        return stmt
    
    @staticmethod
    def lambda_invoke_function(function_name: str) -> StatementFunction:
        """Returns a function that generates Lambda invoke statement"""
        def stmt(region: str, account_id: str) -> IamStatement:
            return {
                "Sid": "LambdaInvokeAccess",
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": [
                    f"arn:aws:lambda:{region}:{account_id}:function:{function_name}"
                ]
            }
        return stmt
    
    @staticmethod
    def base_agentcore_stmts(agent_name: str, region: str, account_id: str):
        return [
                  {
                "Sid": "BedrockPermissions",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                "Resource": [
                    f"arn:aws:ecr:{region}:{account_id}:repository/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogGroups"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": "*"
            },
            {
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets"
                ],
             "Resource": [ "*" ]
             },
             {
                "Effect": "Allow",
                "Resource": "*",
                "Action": "cloudwatch:PutMetricData",
                "Condition": {
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore"
                    }
                }
            },
            {
                "Sid": "GetAgentAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                "Resource": [
                  f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                  f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/{agent_name}-*"
                ]
            },
            ]
