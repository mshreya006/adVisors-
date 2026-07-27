import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import List, Dict, Any
import config

class GNewsClient:
    """Client for GNews.io. Serves as fallback client when NewsAPI is unavailable."""
    def __init__(self):
        self.session = requests.Session()
        retry = Retry(
            total=config.RETRY_COUNT,
            connect=config.RETRY_COUNT,
            read=config.RETRY_COUNT,
            backoff_factor=config.RETRY_BACKOFF_FACTOR,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def fetch_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches articles matching keywords from GNews search endpoint.
        Combines keywords with OR to minimize API hits.
        """
        if not config.GNEWS_KEY:
            raise ValueError("GNews API Key is missing. Fallback cannot run.")

        # GNews supports OR syntax. Let's combine keywords to fetch in one request.
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # limit keywords to prevent query length errors
        
        try:
            response = self.session.get(
                'https://gnews.io/api/v4/search',
                params={
                    'q': query,
                    'lang': 'en',
                    'max': 100,
                    'apikey': config.GNEWS_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            articles = response.json().get('articles', [])
            return self._normalize_articles(articles)
        except requests.exceptions.RequestException as e:
            raise e

    def fetch_top_headlines(self) -> List[Dict[str, Any]]:
        """Fetches top US headlines from GNews."""
        if not config.GNEWS_KEY:
            raise ValueError("GNews API Key is missing. Fallback cannot run.")
        try:
            response = self.session.get(
                'https://gnews.io/api/v4/top-headlines',
                params={
                    'category': 'general',
                    'lang': 'en',
                    'country': 'us',
                    'max': 5,
                    'apikey': config.GNEWS_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            articles = response.json().get('articles', [])
            return self._normalize_articles(articles)
        except requests.exceptions.RequestException as e:
            raise e

    def _normalize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Helper to convert GNews fields to match NewsAPI schema."""
        normalized = []
        for art in articles:
            source_name = "Unknown Source"
            if 'source' in art and isinstance(art['source'], dict):
                source_name = art['source'].get('name', 'Unknown Source')
                
            norm = {
                'url': art.get('url', ''),
                'title': art.get('title', 'No Title'),
                'description': art.get('description', 'No description available'),
                'publishedAt': art.get('publishedAt', ''),
                'source': art.get('source', {}),
                'source_name': source_name,
                'content': art.get('content', '')
            }
            normalized.append(norm)
        return normalized
