"""
S3 Vector Store implementation using AWS Bedrock and S3 Vectors.
"""

import os
import json
import boto3
import nanoid
from typing import List, Optional, Dict, Any
from stores.abs import VectorStore
from models.chunk import Chunk
from models.document import SearchResult, Document
from utils.logger import setup_logger

logger = setup_logger(__name__)

class S3VectorStore(VectorStore):
    """S3 Vector Store implementation."""

    def __init__(self, bucket_name: str, index_name: str, embedding_model_id: str = "amazon.titan-embed-text-v2:0", embedding_dimensions: int = 1024):
        self.bucket_name = bucket_name
        self.index_name = index_name
        
        # Configuration from environment
        self.embedding_model_id = embedding_model_id
        self.embedding_dimensions = embedding_dimensions
        
        # AWS credentials
        self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", "us-east-2")
         
        # Initialize AWS clients
        self._init_clients()
        
        logger.info(f"S3VectorStore initialized - Bucket: {bucket_name}, Index: {index_name}")
    
    def _init_clients(self):
        """Initialize AWS clients."""
        # Bedrock client for embeddings
        
        # S3 vectors client
        if self.aws_access_key_id and self.aws_secret_access_key:
            logger.info("Using AWS credentials from environment variables")
            self.s3vectors_client = boto3.client(
                "s3vectors",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
        else:
            logger.info("Using AWS default credentials")
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region
            )
            self.s3vectors_client = boto3.client(
                "s3vectors",
                region_name=self.aws_region
            )
    
    def _generate_id(self) -> str:
        """Generate unique ID for resources."""
        return nanoid.generate(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", size=21)
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for given text."""
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps({
                    "inputText": text
                })
            )
            
            model_response = json.loads(response.get("body").read())
            embedding = model_response.get("embedding")
            
            if not embedding:
                raise ValueError("No embedding returned from Bedrock")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def save_chunks(self, chunks: List[Chunk]) -> List[str]:
        """Save multiple chunks to S3 vectors using put_vectors for batch operation."""
        vectors_to_put = []
        saved_ids = []

        for chunk in chunks:
            try:
                # Generate ID if not provided
                chunk_id = chunk.source
                
                # Create embedding
                embedding = self.create_embedding(chunk.content)
                
                # Prepare metadata
                metadata = {
                    **chunk.metadata,
                    "content":  chunk.content,
                    "chunk_size": chunk.size,
                    # "word_count": chunk.word_count,
                    "source": chunk.source
                }

                vectors_to_put.append({
                    "key": chunk_id,
                    "data": {"float32": embedding},
                    "metadata": metadata
                })
                saved_ids.append(chunk_id)
                logger.debug(f"Prepared chunk {chunk_id} from {chunk.source} for batch insertion.")

            except Exception as e:
                logger.error(f"Error preparing chunk from {chunk.source}: {str(e)}")
                continue
        
        if not vectors_to_put:
            logger.warning("No vectors to save.")
            return []

        try:
            self.s3vectors_client.put_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                vectors=vectors_to_put
            )
            logger.info(f"Successfully saved {len(saved_ids)}/{len(chunks)} chunks using put_vectors.")
        except Exception as e:
            logger.error(f"Error saving chunks with put_vectors: {str(e)}")
            # Depending on requirements, we might want to return which ones failed.
            # For now, returning empty list on batch failure.
            return []

        return saved_ids
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for similar content using vector similarity."""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            
            # Search vectors
            response = self.s3vectors_client.query_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                queryVector={"float32": query_embedding},
                topK=limit,
                returnDistance=True,
                returnMetadata=True
            )
            
            # Process results
            results = []
            for vector_result in response.get("vectors", []):
                metadata = vector_result.get("metadata", {})
                
                result = SearchResult(
                    id=vector_result.get("vectorId", ""),
                    content=metadata.get("content", ""),
                    source=metadata.get("source", ""),
                    score=1.0 - vector_result.get("distance", 1.0),  # Convert distance to similarity
                    metadata=metadata
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by its ID."""
        try:
            # Note: S3 vectors doesn't have a direct get_by_id method
            # This is a simplified implementation - in practice you might need
            # to store document metadata separately or use a different approach
            
            # For now, we'll return None and log that this needs implementation
            logger.warning(f"get_by_id not fully implemented for S3 vectors: {document_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Check if the vector store is accessible."""
        try:
            # Try to make a simple query to test connectivity
            test_embedding = self.create_embedding("test")
            print("test", test_embedding)
            return test_embedding is not None
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False