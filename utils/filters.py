from typing import List, Dict, Any, Union
import config
from database.models import Article

def contains_negative_keywords(title: str, description: str) -> bool:
    """
    Checks if the title or description of an article contains any negative keywords
    specified in the configuration.
    """
    title_lower = (title or "").lower()
    desc_lower = (description or "").lower()
    
    for neg_keyword in config.NEGATIVE_KEYWORDS:
        neg_kw_lower = neg_keyword.lower()
        if neg_kw_lower in title_lower or neg_kw_lower in desc_lower:
            return True
    return False

def filter_negative_news(articles: List[Union[Dict[str, Any], Article]]) -> List[Union[Dict[str, Any], Article]]:
    """
    Filters out articles containing negative/tragic/sensitive keywords.
    Accepts both raw API article dicts and structured Article objects.
    """
    filtered = []
    for art in articles:
        if isinstance(art, dict):
            title = art.get('title', '')
            description = art.get('description', '')
        else:
            title = art.title
            description = art.description
            
        if not contains_negative_keywords(title, description):
            filtered.append(art)
    return filtered
