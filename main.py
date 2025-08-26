#!/usr/bin/env python3
"""
Main entry point for GitHub repository crawler and embedder.
Demonstrates dependency injection configuration pattern.
"""
from dotenv import load_dotenv
load_dotenv()
import sys
import os

from crawler.crawler import GitHubCrawler
from stores.s3_vector import S3VectorStore
from processors.abs import Processor
from processors.markdown import MarkdownProcessor
from processors.not_implemented import (
    PythonNotImplementedProcessor,
    JavaScriptNotImplementedProcessor,
    JSONNotImplementedProcessor,
    YAMLNotImplementedProcessor,
    TextNotImplementedProcessor,
    ConfigNotImplementedProcessor
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
def validate_environment():
    """Validate required environment variables."""
    required_env_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set the following environment variables:")
        for var in missing_vars:
            logger.error(f"  export {var}=your_value")
        return False
    
    # Optional but recommended
    optional_vars = ['GITHUB_TOKEN']
    missing_optional = [var for var in optional_vars if not os.environ.get(var)]
    
    if missing_optional:
        logger.warning(f"Optional environment variables not set: {', '.join(missing_optional)}")
        logger.warning("Consider setting GITHUB_TOKEN for higher API rate limits")
    
    return True


def main():
    if not validate_environment():
        sys.exit(1)
    try:
        repo_url = "https://github.com/A3Data/a3wiki-backup"
        branch = "main"
        max_files = 100
        vector_store = S3VectorStore(bucket_name="a3wiki", index_name="github2")
        
        processors = [
            # Implemented processors
            MarkdownProcessor(vector_store),
            
            # Not yet implemented processors (will log and skip)
            PythonNotImplementedProcessor(vector_store),
            JavaScriptNotImplementedProcessor(vector_store),
            JSONNotImplementedProcessor(vector_store),
            YAMLNotImplementedProcessor(vector_store),
            TextNotImplementedProcessor(vector_store),
            ConfigNotImplementedProcessor(vector_store),
        ]
        logger.info("Initializing crawler...")
        crawler = GitHubCrawler(
            processors=processors,
            branch=branch,
            max_files=max_files
        )
                
        # Show configuration
        logger.info(f"Configuration:")
        logger.info(f"  Repository: {repo_url}")
        logger.info(f"  Branch: {branch}")
        logger.info(f"  Max Files: {max_files or 'unlimited'}")
        logger.info(f"  Supported Extensions: {crawler.get_supported_extensions()}")
        

        
        # Start crawling
        logger.info(f"Starting crawl of repository: {repo_url}")
        results = crawler.crawl_repository(repo_url)
        
        # Print results
        logger.info("=" * 60)
        logger.info("CRAWLING COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"Total files processed: {results['total_files']}")
        logger.info(f"Successfully embedded: {results['successful_embeddings']}")
        logger.info(f"Failed embeddings: {results['failed_embeddings']}")
        logger.info(f"Skipped files: {results['skipped_files']}")
        
        if results['errors']:
            logger.warning(f"Encountered {len(results['errors'])} errors:")
            for i, error in enumerate(results['errors'][:10]):  # Show first 10 errors
                logger.warning(f"  {i+1}. {error}")
            
            if len(results['errors']) > 10:
                logger.warning(f"  ... and {len(results['errors']) - 10} more errors")
        
        # Calculate success rate
        if results['total_files'] > 0:
            success_rate = results['successful_embeddings'] / results['total_files'] * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        # Exit with appropriate code
        if results['successful_embeddings'] > 0:
            logger.info("Crawling completed successfully!")
            sys.exit(0)
        else:
            logger.error("No files were successfully processed!")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        logger.error("Check your configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
