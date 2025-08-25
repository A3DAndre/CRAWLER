"""
Data models for search results and documents.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json

@dataclass
class SearchResult:
    """Represents a search result from vector store."""
    
    id: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'source': self.source,
            'score': self.score,
            'metadata': self.metadata
        }
    
    def to_md(self) -> str:
        """Formats the result to markdown with source score and metadata at the top and full content at the bottom"""
        formatted = f"### {self.source}\n\n"
        formatted += f"**Score:** {self.score}\n\n"
        formatted += f"**Metadata:** {json.dumps(self.metadata, indent=2)}\n\n"
        formatted += f"**Content:**\n{self.content}\n"
        return formatted

    def __str__(self) -> str:
        return f"SearchResult(id={self.id}, content={self.content[:50]}, source={self.source}, score={self.score})"

@dataclass 
class Document:
    """Represents a complete document retrieved from vector store."""
    
    id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    chunks: Optional[List['Chunk']] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        result = {
            'id': self.id,
            'content': self.content,
            'source': self.source,
            'metadata': self.metadata
        }
        
        if self.chunks:
            result['chunks'] = [chunk.to_dict() for chunk in self.chunks]
            
        return result