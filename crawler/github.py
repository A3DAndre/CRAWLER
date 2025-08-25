"""
A client for interacting with the GitHub REST API.

This module provides a GitHub class to fetch repository information,
list files, and retrieve file content. It requires a GitHub Personal
Access Token to be set in the GITHUB_API_TOKEN environment variable.
"""

import os
import base64
import requests
from typing import List, Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GitHub:
    """
    A wrapper for the GitHub REST API to fetch repository information and files.
    
    Handles API authentication, requests, and error handling.
    """
    
    API_URL = "https://api.github.com"
    
    def __init__(self):
        """
        Initializes the GitHub API client.
        
        It retrieves the API token from environment variables and sets up a
        requests session with retry logic.
        
        Raises:
            ValueError: If the GITHUB_TOKEN environment variable is not set.
        """
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.error("GITHUB_TOKEN environment variable not set.")
            raise ValueError("GITHUB_TOKEN environment variable not set.")
            
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        self.session = self._create_session()
        logger.info("GitHub client initialized successfully.")

    def _create_session(self) -> requests.Session:
        """Creates a requests session with retry logic for robustness."""
        session = requests.Session()
        session.headers.update(self.headers)
        
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"HEAD", "GET", "OPTIONS"}
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """
        Makes a request to the GitHub API.

        Args:
            method: The HTTP method (e.g., 'GET').
            endpoint: The API endpoint (e.g., '/repos/owner/repo').
            **kwargs: Additional arguments for the requests method.

        Returns:
            The JSON response as a dictionary or list, or None if an error occurs.
        """
        url = f"{self.API_URL}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            # Check rate limiting
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 50:
                    logger.warning(f"Low GitHub API rate limit remaining: {remaining}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error for {url}: {e.response.status_code} {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
        
        return None

    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves basic information about a repository.

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.

        Returns:
            A dictionary containing repository information, or None on failure.
        """
        logger.debug(f"Fetching info for repository: {owner}/{repo}")
        endpoint = f"/repos/{owner}/{repo}"
        return self._request("GET", endpoint)

    def get_repository_files(self, owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all files in a repository recursively.

        This method uses the Git Trees API for efficient fetching of all files.

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            branch: The branch to crawl.

        Returns:
            A list of dictionaries, each representing a file, or an empty list on failure.
        """
        logger.info(f"Fetching file list for {owner}/{repo} on branch '{branch}'")
        
        # 1. Get the latest commit SHA for the given branch
        branch_info = self._request("GET", f"/repos/{owner}/{repo}/branches/{branch}")
        if not branch_info or 'commit' not in branch_info:
            logger.error(f"Could not find branch '{branch}' for repo {owner}/{repo}")
            return []
        
        commit_sha = branch_info['commit']['sha']
        logger.debug(f"Latest commit SHA for branch '{branch}' is {commit_sha}")
        
        # 2. Get the tree SHA from the commit
        commit_data = self._request("GET", f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
        if not commit_data or 'tree' not in commit_data:
            logger.error(f"Could not get commit data for SHA {commit_sha}")
            return []
        
        tree_sha = commit_data['tree']['sha']
        
        # 3. Get the file tree recursively
        tree_data = self._request("GET", f"/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1")
        if not tree_data or 'tree' not in tree_data:
            logger.error(f"Could not get file tree for SHA {tree_sha}")
            return []
            
        # 4. Filter for files ('blobs') only, excluding directories ('trees')
        files = [item for item in tree_data['tree'] if item.get('type') == 'blob']
        logger.info(f"Found {len(files)} files in {owner}/{repo}")
        
        return files

    def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> Optional[str]:
        """
        Retrieves the content of a specific file.

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            path: The full path to the file within the repository.
            ref: The branch, tag, or commit SHA.

        Returns:
            The decoded content of the file as a string, or None on failure.
        """
        logger.debug(f"Fetching content for file: {path} in {owner}/{repo}")
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        
        file_data = self._request("GET", endpoint, params=params)
        
        if not file_data or 'content' not in file_data:
            logger.warning(f"Could not retrieve content for file: {path}")
            return None
        
        if file_data.get('encoding') != 'base64':
            logger.warning(f"Unsupported encoding '{file_data.get('encoding')}' for file: {path}")
            return None
            
        try:
            # Content is base64 encoded, needs to be decoded.
            content_bytes = base64.b64decode(file_data['content'])
            # Decode bytes to string, ignoring errors for potential binary files.
            return content_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to decode content for file {path}: {e}")
            return None