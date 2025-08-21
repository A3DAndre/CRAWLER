"""
Abstract base class for file processors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.chunk import Chunk
from stores.abs import VectorStore

class Processor(ABC):
    """Abstract base class for file processors."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    @property
    @abstractmethod
    def supported_file_types(self) -> List[str]:
        """
        List of file extensions this processor supports.
        
        Returns:
            List of file extensions (e.g., ['.md', '.markdown'])
        """
        pass
    
    @abstractmethod
    def chunkify_file(self, content: str, file_path: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Split file content into chunks.
        
        Args:
            content: Raw file content
            file_path: Path to the file
            metadata: File metadata
            
        Returns:
            List of content chunks
        """
        pass
    
    def process_file(self, content: str, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Process a file: chunkify and save to vector store.
        
        Args:
            content: Raw file content
            file_path: Path to the file
            metadata: File metadata
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Validate inputs
            if not content or not content.strip():
                return False
            
            if not self.supports_file(file_path):
                return False
            
            # Create chunks
            chunks = self.chunkify_file(content, file_path, metadata)
            
            if not chunks:
                return False
            
            # Save chunks to vector store
            saved_ids = self.vector_store.save_chunks(chunks)
            
            # Consider successful if more than half of chunks were saved
            success_rate = len(saved_ids) / len(chunks)
            return success_rate > 0.5
            
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger(__name__)
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return False
    
    def supports_file(self, file_path: str) -> bool:
        """
        Check if this processor supports the given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if supported, False otherwise
        """
        import os
        extension = os.path.splitext(file_path)[1].lower()
        return extension in self.supported_file_types
    
    def clean_content(self, content: str) -> str:
        """
        Clean content before processing.
        Default implementation - can be overridden.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        # Remove excessive whitespace but preserve structure
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove excessive empty lines (more than 2 consecutive)
        result_lines = []
        empty_count = 0
        
        for line in cleaned_lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)
        
        return '\n'.join(result_lines)