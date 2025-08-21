"""
Placeholder processor for file types that are not yet implemented.
"""

from typing import List, Dict, Any
from processors.abs import Processor
from models.chunk import Chunk
from stores.abs import VectorStore
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NotImplementedProcessor(Processor):
    """Processor that handles unsupported file types by logging them."""
    
    def __init__(self, vector_store: VectorStore, file_types: List[str]):
        super().__init__(vector_store)
        self._file_types = file_types
    
    @property
    def supported_file_types(self) -> List[str]:
        """Return the file types this processor is configured to handle."""
        return self._file_types
    
    def chunkify_file(self, content: str, file_path: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Return empty list and log that file type is not implemented."""
        import os
        extension = os.path.splitext(file_path)[1].lower()
        logger.info(f"File type '{extension}' not implemented, skipping: {file_path}")
        return []
    
    def process_file(self, content: str, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Override to avoid error logging for expected non-implementation."""
        import os
        extension = os.path.splitext(file_path)[1].lower()
        logger.debug(f"Skipping {extension} file (not implemented): {file_path}")
        return True  # Return True to indicate this is expected behavior

# Common file type configurations
class TerraformNotImplementedProcessor(NotImplementedProcessor):
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, [".tf"])

class PythonNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for Python file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.py', '.pyx', '.pyi'])

class JavaScriptNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for JavaScript file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.js', '.jsx', '.ts', '.tsx'])

class JSONNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for JSON file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.json', '.jsonl'])

class YAMLNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for YAML file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.yml', '.yaml'])

class TextNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for plain text file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.txt', '.text'])

class ConfigNotImplementedProcessor(NotImplementedProcessor):
    """Placeholder for configuration file processing."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store, ['.ini', '.cfg', '.conf', '.toml'])