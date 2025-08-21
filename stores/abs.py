"""
Abstract base class for vector stores.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from models.chunk import Chunk
from models.document import SearchResult, Document

class VectorStore(ABC):
    """Abstract base class for vector storage implementations."""
    
    @abstractmethod
    def save_chunks(self, chunks: List[Chunk]) -> List[str]:
        """
        Save multiple chunks to the vector store.
        
        Args:
            chunks: List of chunks to save
            
        Returns:
            List of IDs of saved chunks
            
        Raises:
            Exception: If saving fails
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search for similar content using vector similarity.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of search results ordered by similarity score
            
        Raises:
            Exception: If search fails
        """
        pass
    
    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            Document if found, None otherwise
            
        Raises:
            Exception: If retrieval fails
        """
        pass
    
    @abstractmethod
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for given text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            Exception: If embedding creation fails
        """
        pass
    
    def save_chunk(self, chunk: Chunk) -> str:
        """
        Save a single chunk (convenience method).
        
        Args:
            chunk: Chunk to save
            
        Returns:
            ID of saved chunk
        """
        ids = self.save_chunks([chunk])
        return ids[0] if ids else None