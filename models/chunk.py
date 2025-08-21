"""
Data models for document chunks.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid

@dataclass
class Chunk:
    """Represents a chunk of content from a document."""
    
    content: str
    source: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate chunk ID if not provided."""
        if self.chunk_id is None:
            self.chunk_id = str(uuid.uuid4())
    
    @property
    def size(self) -> int:
        """Get chunk size in characters."""
        return len(self.content)
    
    @property
    def word_count(self) -> int:
        """Get chunk word count."""
        return len(self.content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'source': self.source,
            'size': self.size,
            'word_count': self.word_count,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chunk':
        """Create chunk from dictionary."""
        return cls(
            chunk_id=data.get('chunk_id'),
            content=data['content'],
            source=data['source'],
            metadata=data.get('metadata', {})
        )