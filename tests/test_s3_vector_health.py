import io
import json

import pytest

from stores.s3_vector import S3VectorStore


class FakeBedrockClientSuccess:
    def invoke_model(self, modelId=None, body=None):
        # parse requested dimensions if provided, else default to 8
        try:
            payload = json.loads(body)
            dims = int(payload.get("dimensions", 8))
        except Exception:
            dims = 8

        embedding = [0.01] * dims
        return {"body": io.BytesIO(json.dumps({"embedding": embedding}).encode())}


class FakeBedrockClientError:
    def invoke_model(self, *args, **kwargs):
        raise RuntimeError("bedrock unavailable")


class FakeS3VectorsClient:
    def create_vector(self, *args, **kwargs):
        return {}

    def query_vectors(self, *args, **kwargs):
        return {"vectors": []}


def make_fake_client(success: bool = True):
    def _client(service_name, **kwargs):
        if service_name == "bedrock-runtime":
            return FakeBedrockClientSuccess() if success else FakeBedrockClientError()
        if service_name == "s3vectors":
            return FakeS3VectorsClient()
        raise ValueError(f"Unexpected service: {service_name}")

    return _client


def test_health_check_success(monkeypatch):
    """health_check should return True when bedrock returns an embedding of correct size."""
    monkeypatch.setattr("stores.s3_vector.boto3.client", make_fake_client(success=True))

    store = S3VectorStore(bucket_name="test-bucket", index_name="test-index", embedding_dimensions=8)
    assert store.health_check() is True


def test_health_check_failure(monkeypatch):
    """health_check should return False when bedrock invocation fails."""
    monkeypatch.setattr("stores.s3_vector.boto3.client", make_fake_client(success=False))

    store = S3VectorStore(bucket_name="test-bucket", index_name="test-index", embedding_dimensions=8)
    assert store.health_check() is False
