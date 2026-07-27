import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import List, Dict, Any
import config

class NewsAPIClient:
    """Client for NewsAPI.org. Implements resilient requests and session sharing."""
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
        """Fetches articles matching a list of keywords from NewsAPI everything endpoint."""
        all_articles = []
        if not config.NEWSAPI_KEY:
            raise ValueError("NewsAPI Key is missing.")

        for keyword in keywords:
            try:
                response = self.session.get(
                    'https://newsapi.org/v2/everything',
                    params={
                        'q': keyword,
                        'language': 'en',
                        'pageSize': 100,
                        'apiKey': config.NEWSAPI_KEY
                    },
                    timeout=10
                )
                response.raise_for_status()
                articles = response.json().get('articles', [])
                
                # Normalize source format if needed
                for art in articles:
                    if 'source' in art and isinstance(art['source'], dict):
                        art['source_name'] = art['source'].get('name', 'Unknown Source')
                    else:
                        art['source_name'] = 'Unknown Source'
                        
                all_articles.extend(articles)
                if len(all_articles) >= 100:
                    break
            except requests.exceptions.RequestException as e:
                raise e
        return all_articles[:100]

    def fetch_top_headlines(self) -> List[Dict[str, Any]]:
        """Fetches top US headlines from NewsAPI."""
        if not config.NEWSAPI_KEY:
            raise ValueError("NewsAPI Key is missing.")
        try:
            response = self.session.get(
                'https://newsapi.org/v2/top-headlines',
                params={
                    'country': 'us',
                    'pageSize': 5,
                    'apiKey': config.NEWSAPI_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            articles = response.json().get('articles', [])
            for art in articles:
                if 'source' in art and isinstance(art['source'], dict):
                    art['source_name'] = art['source'].get('name', 'Unknown Source')
                else:
                    art['source_name'] = 'Unknown Source'
            return articles
        except requests.exceptions.RequestException as e:
            raise e
