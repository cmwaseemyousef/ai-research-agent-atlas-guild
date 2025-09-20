"""
Web Search Tool using Tavily API
Finds relevant sources for research queries
"""

import os
import logging
from typing import List, Dict, Optional
from tavily import TavilyClient

logger = logging.getLogger(__name__)

class SearchTool:
    """Tool for searching the web using Tavily API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search tool
        
        Args:
            api_key: Tavily API key (if not provided, will use environment variable)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Tavily API key is required. Set TAVILY_API_KEY environment variable.")
        
        self.client = TavilyClient(api_key=self.api_key)
    
    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search for relevant sources
        
        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 3)
            
        Returns:
            List of search results with URL, title, and snippet
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Use Tavily's search API with specific parameters
            response = self.client.search(
                query=query,
                search_depth="advanced",  # More thorough search
                max_results=max_results,
                include_answer=False,  # We'll generate our own summary
                include_raw_content=False  # We'll extract content ourselves
            )
            
            results = []
            for item in response.get('results', []):
                result = {
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('content', ''),
                    'published_date': item.get('published_date', ''),
                    'score': item.get('score', 0.0)
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise Exception(f"Search failed: {str(e)}")
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and accessible
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears valid, False otherwise
        """
        if not url:
            return False
            
        # Basic URL validation
        valid_schemes = ['http://', 'https://']
        if not any(url.startswith(scheme) for scheme in valid_schemes):
            return False
            
        # Check for common invalid patterns
        invalid_patterns = ['javascript:', 'mailto:', 'tel:', 'ftp://']
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False
            
        return True