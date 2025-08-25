"""
GitHub repository crawler with dependency injection for processors.
"""

import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
from crawler.github import GitHub
from processors.abs import Processor
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GitHubCrawler:
    """Crawls GitHub repositories using configurable processors."""
    
    def __init__(self, processors: List[Processor], branch: str = "main", max_files: int = 100):
        self.github = GitHub()
        self.processors = processors
        self.branch = branch
        self.max_files = max_files
        
        # Build file type to processor mapping
        self.processor_map = {}
        for processor in processors:
            for file_type in processor.supported_file_types:
                self.processor_map[file_type] = processor
        
        self.stats = {
            'total_files': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'skipped_files': 0,
            'errors': []
        }
        
        logger.info(f"GitHubCrawler initialized with {len(processors)} processors")
        logger.info(f"Supported file types: {list(self.processor_map.keys())}")
    
    def _parse_repo_url(self, repo_url: str) -> tuple:
        """Parse GitHub repository URL to extract owner and repo name."""
        parsed = urlparse(repo_url)
        if parsed.hostname != 'github.com':
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub repository path: {parsed.path}")
        
        return path_parts[0], path_parts[1]
    
    def _get_file_processor(self, file_path: str) -> Optional[Processor]:
        """Get appropriate processor for file based on extension."""
        extension = os.path.splitext(file_path)[1].lower()
        return self.processor_map.get(extension)
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on path patterns."""
        skip_patterns = [
            '.git/',
            'node_modules/',
            '__pycache__/',
            '.pytest_cache/',
            'venv/',
            'env/',
            '.env',
            'package-lock.json',
            'yarn.lock',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        return any(pattern in file_path for pattern in skip_patterns)
    
    def process_file(self, file_info: dict, repo_info: dict) -> bool:
        """Process a single file using appropriate processor."""
        file_path = file_info['path']
        
        try:
            # Skip if file should be ignored
            if self._should_skip_file(file_path):
                logger.debug(f"Skipping file due to skip pattern: {file_path}")
                self.stats['skipped_files'] += 1
                return True
            
            # Get appropriate processor
            processor = self._get_file_processor(file_path)
            if not processor:
                logger.debug(f"No processor available for file: {file_path}")
                self.stats['skipped_files'] += 1
                return True
            
            # Get file content
            content = self.github.get_file_content(
                repo_info['owner'], 
                repo_info['name'], 
                file_path, 
                self.branch
            )
            
            if not content:
                logger.warning(f"Empty content for file: {file_path}")
                self.stats['skipped_files'] += 1
                return True
            
            # Create file metadata
            metadata = {
                'file_path': file_path,
                # 'repository': f"{repo_info['owner']}/{repo_info['name']}",
                # 'branch': self.branch,
                # 'file_size': len(content),
                # 'file_type': os.path.splitext(file_path)[1].lower(),
                'sha': file_info.get('sha', ''),
                'github_url': f"https://github.com/{repo_info['owner']}/{repo_info['name']}/blob/{self.branch}/{file_path}"
            }
            
            # Process the file
            success = processor.process_file(content, file_path, metadata)
            
            if success:
                self.stats['successful_embeddings'] += 1
                logger.info(f"Successfully processed: {file_path}")
            else:
                self.stats['failed_embeddings'] += 1
                logger.warning(f"Failed to process: {file_path}")
                
            return success
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            self.stats['failed_embeddings'] += 1
            return False
    
    def crawl_repository(self, repo_url: str) -> dict:
        """Crawl entire repository and process all eligible files."""
        try:
            # Parse repository URL
            owner, repo_name = self._parse_repo_url(repo_url)
            repo_info = {'owner': owner, 'name': repo_name}
            
            logger.info(f"Crawling repository: {owner}/{repo_name} (branch: {self.branch})")
            
            # Get repository info first
            repo_data = self.github.get_repository_info(owner, repo_name)
            if repo_data:
                logger.info(f"Repository: {repo_data.get('full_name')} - {repo_data.get('description', 'No description')}")
                logger.info(f"Stars: {repo_data.get('stargazers_count', 0)}, Language: {repo_data.get('language', 'Unknown')}")
            
            # Get repository files
            files = self.github.get_repository_files(owner, repo_name, self.branch)
            
            if not files:
                logger.warning("No files found in repository")
                return self.stats
            
            logger.info(f"Found {len(files)} files in repository")
            
            # Apply file limit
            files_to_process = files[:self.max_files] if self.max_files else files
            
            if len(files_to_process) < len(files):
                logger.info(f"Processing limited to first {len(files_to_process)} files (max_files={self.max_files})")
            
            # Process files
            for i, file_info in enumerate(files_to_process):
                self.stats['total_files'] += 1
                
                if i % 10 == 0:
                    logger.info(f"Processing file {i+1}/{len(files_to_process)}: {file_info['path']}")
                
                self.process_file(file_info, repo_info)
                
                # Log progress periodically
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(files_to_process)} files processed")
                    logger.info(f"  Successful: {self.stats['successful_embeddings']}, "
                              f"Failed: {self.stats['failed_embeddings']}, "
                              f"Skipped: {self.stats['skipped_files']}")
            
            logger.info("Repository crawling completed")
            return self.stats
            
        except Exception as e:
            error_msg = f"Error crawling repository {repo_url}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return self.stats
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        return list(self.processor_map.keys())
    
    def get_processor_for_file(self, file_path: str) -> Optional[str]:
        """Get processor class name for a given file."""
        processor = self._get_file_processor(file_path)
        return processor.__class__.__name__ if processor else None