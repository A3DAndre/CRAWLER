"""
Markdown file processor with intelligent chunking.
"""

import os
import re
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from processors.abs import Processor
from models.chunk import Chunk
from stores.abs import VectorStore
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MarkdownProcessor(Processor):
    """Processor for Markdown files."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store)
        
        # Configuration
        chunk_size = int(os.environ.get("CHUNK_SIZE", "1024"))
        chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ".",     # Sentences
                " ",     # Words
                ""       # Characters
            ]
        )
    
    @property
    def supported_file_types(self) -> List[str]:
        """Supported markdown file extensions."""
        return ['.md', '.markdown', '.mdown', '.mkd', '.mdx']
    
    def extract_frontmatter(self, content: str) -> tuple[str, Dict[str, Any]]:
        """Extract YAML frontmatter and return content without it."""
        frontmatter_data = {}
        
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter_content = frontmatter_match.group(1)
            # Remove frontmatter from content
            content = content[frontmatter_match.end():]
            
            # Try to parse YAML (simplified - you might want to use PyYAML)
            for line in frontmatter_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter_data[key.strip()] = value.strip().strip('"\'')
        
        return content, frontmatter_data
    
    def extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract markdown headers from content."""
        headers = []
        header_matches = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        for level_marks, text in header_matches:
            headers.append({
                'level': len(level_marks),
                'text': text.strip(),
                'anchor': re.sub(r'[^\w\s-]', '', text.lower()).replace(' ', '-')
            })
        
        return headers
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze markdown content and extract metadata."""
        analysis = {
            'code_blocks': len(re.findall(r'```[\s\S]*?```', content)),
            'inline_code': len(re.findall(r'`[^`\n]+`', content)),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'images': len(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)),
            'tables': len(re.findall(r'\|.*\|', content)),
            'lists': len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE)),
            'numbered_lists': len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE))
        }
        
        return analysis
    
    def preprocess_content(self, content: str) -> str:
        """Clean and preprocess markdown content."""
        # Clean content using base method
        content = self.clean_content(content)
        
        # Normalize headers spacing
        content = re.sub(r'\n{3,}(#{1,6})', r'\n\n\1', content)
        
        # Normalize code blocks
        content = re.sub(r'\n{3,}```', r'\n\n```', content)
        content = re.sub(r'```\n{3,}', r'```\n\n', content)
        
        # Clean up table formatting
        content = re.sub(r'\n{2,}(\|)', r'\n\1', content)
        
        return content.strip()
    
    def chunkify_file(self, content: str, file_path: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Split markdown file into chunks."""
        try:
            # Extract frontmatter
            content_without_fm, frontmatter = self.extract_frontmatter(content)
            
            # Preprocess content
            processed_content = self.preprocess_content(content_without_fm)
            
            
            # Split into chunks
            text_chunks = self.text_splitter.split_text(processed_content)
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                if not chunk_text.strip():
                    continue
                
                # Find headers in this chunk
                chunk_headers = self.extract_headers(chunk_text)
                
                # Create chunk metadata
                chunk_metadata = {
                    **metadata,
                    'chunk_index': i,
                    # 'total_chunks': len(text_chunks),
                    # 'file_type': 'markdown',
                    # 'frontmatter': frontmatter,
                    # 'document_headers': headers,
                    # 'chunk_headers': chunk_headers,
                    # 'content_analysis': analysis,
                    # 'has_code': '```' in chunk_text or '`' in chunk_text,
                    # 'has_links': '[' in chunk_text and '](' in chunk_text,
                    # 'has_images': '![' in chunk_text,
                    # 'main_title': headers[0]['text'] if headers else None
                }
                
                # Create chunk with source reference
                chunk_source = f"{file_path}#chunk-{i}"
                
                chunk = Chunk(
                    content=chunk_text.strip(),
                    source=chunk_source,
                    metadata=chunk_metadata
                )
                
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking markdown file {file_path}: {str(e)}")
            return []