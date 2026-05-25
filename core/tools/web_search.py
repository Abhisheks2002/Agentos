"""Web Search Tool - Day 8 Implementation.

This module provides web search functionality for AgentOS agents.
Integrates with the Tool Registry for function calling.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to import requests, fall back to urllib if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.request
    import urllib.parse
    import urllib.error


class WebSearchTool:
    """Web search tool with function calling support."""

    def __init__(self, api_key: str = None, search_engine: str = "ddg"):
        """Initialize the web search tool.

        Args:
            api_key: Optional API key for premium search services
            search_engine: Search engine to use (ddg, google, bing)
        """
        self.api_key = api_key
        self.search_engine = search_engine
        self.default_limit = 10
        self.session = None

        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def search(self, query: str, limit: int = None, **kwargs) -> Dict[str, Any]:
        """Perform a web search.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            Dictionary with search results and metadata
        """
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Query cannot be empty",
                "results": []
            }

        limit = limit or self.default_limit

        try:
            if self.search_engine == "ddg":
                results = self._search_duckduckgo(query, limit)
            elif self.search_engine in ["google", "bing"]:
                results = self._search_api(query, limit)
            else:
                results = self._search_duckduckgo(query, limit)

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def _search_duckduckgo(self, query: str, limit: int) -> List[Dict]:
        """Search using DuckDuckGo HTML API.

        Args:
            query: Search query
            limit: Result limit

        Returns:
            List of search results
        """
        results = []

        if REQUESTS_AVAILABLE and self.session:
            # Use requests for HTML scraping
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query, "b": ""}

            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()

            # Parse results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            for result in soup.select('.result'):
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get_text(strip=True) if link_elem else "",
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })

                    if len(results) >= limit:
                        break
        else:
            # Fallback to simple URL-based search using urllib
            encoded_query = urllib.parse.quote(query)
            url = f"https://duckduckgo.com/?q={encoded_query}&format=json"

            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = data.get('Results', [])[:limit]

        return results

    def _search_api(self, query: str, limit: int) -> List[Dict]:
        """Search using API (Google/Bing).

        Args:
            query: Search query
            limit: Result limit

        Returns:
            List of search results
        """
        # Placeholder for API-based search
        # Would require API key for Google Custom Search or Bing Search API
        logger.warning(f"Search engine {self.search_engine} requires API configuration")
        return []

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get the tool definition for function calling.

        Returns:
            Tool definition dictionary compatible with OpenAI function calling
        """
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information. Use this when you need current information, news, or facts that may not be in your training data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query string. Be specific and include relevant keywords."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the web search tool with given parameters.

        Args:
            params: Parameters containing query and optional limit

        Returns:
            Search results dictionary
        """
        query = params.get("query", "")
        limit = params.get("limit", self.default_limit)

        return self.search(query, limit)


# Default instance for easy import
_default_search_tool = None


def get_search_tool() -> WebSearchTool:
    """Get or create the default search tool instance.

    Returns:
        WebSearchTool instance
    """
    global _default_search_tool
    if _default_search_tool is None:
        _default_search_tool = WebSearchTool()
    return _default_search_tool


def search_web(query: str, limit: int = 10) -> Dict[str, Any]:
    """Convenience function for web search.

    Args:
        query: Search query
        limit: Result limit

    Returns:
        Search results
    """
    tool = get_search_tool()
    return tool.search(query, limit)