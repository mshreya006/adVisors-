from difflib import SequenceMatcher
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from typing import List, Dict, Any, Union
import logging
from database.models import Article

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """
    Normalizes a URL by removing tracking query parameters (like utm_*),
    trailing slashes, and protocol schemes (http/https mismatch), 
    and www subdomains.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.lower())
        # Remove tracking parameters
        query_parts = []
        if parsed.query:
            for q in parsed.query.split('&'):
                if not any(q.startswith(prefix) for prefix in ['utm_', 'fbclid', 'gclid', 'ref']):
                    query_parts.append(q)
                    
        new_query = '&'.join(query_parts)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
            
        # Reconstruct URL without scheme to handle http vs https mismatch, and normalize trailing slash
        path = parsed.path
        if path.endswith('/'):
            path = path[:-1]
            
        normalized = urlunparse(('', netloc, path, parsed.params, new_query, ''))
        return normalized
    except Exception as e:
        logger.warning(f"Error normalizing URL {url}: {e}")
        return url.lower().strip()

def get_title_similarity(title1: str, title2: str) -> float:
    """Calculates similarity ratio between two titles using SequenceMatcher."""
    if not title1 or not title2:
        return 0.0
    return SequenceMatcher(None, title1.strip().lower(), title2.strip().lower()).ratio()

def parse_iso_timestamp(ts_str: str) -> datetime:
    """Safely parses ISO timestamp strings returned by APIs."""
    if not ts_str:
        return datetime.min
    try:
        # Standardize 'Z' to UTC offset for compatibility
        clean_ts = ts_str.replace('Z', '+00:00')
        # Some API responses might include space or other separators
        if ' ' in clean_ts:
            clean_ts = clean_ts.replace(' ', 'T')
        return datetime.fromisoformat(clean_ts)
    except Exception:
        return datetime.min

def is_duplicate(art1: Union[Dict[str, Any], Article], art2: Union[Dict[str, Any], Article], title_threshold: float = 0.85, time_window_hours: float = 4.0) -> bool:
    """
    Determines if two articles are duplicates based on:
    1. Exact URL normalization match.
    2. High title similarity.
    3. Moderate title similarity with very close publication timestamps.
    """
    # Extract fields based on type
    if isinstance(art1, dict):
        url1 = art1.get('url', '')
        title1 = art1.get('title', '')
        published1 = art1.get('publishedAt', art1.get('published_at', ''))
    else:
        url1 = art1.url
        title1 = art1.title
        published1 = art1.published_at

    if isinstance(art2, dict):
        url2 = art2.get('url', '')
        title2 = art2.get('title', '')
        published2 = art2.get('publishedAt', art2.get('published_at', ''))
    else:
        url2 = art2.url
        title2 = art2.title
        published2 = art2.published_at

    # Check 1: Normalized URL match
    if normalize_url(url1) == normalize_url(url2) and url1 != "":
        return True

    # Check 2: Title similarity
    title_sim = get_title_similarity(title1, title2)
    if title_sim >= title_threshold:
        return True

    # Check 3: Moderate title similarity + close timestamp
    if title_sim >= 0.70 and published1 and published2:
        dt1 = parse_iso_timestamp(published1)
        dt2 = parse_iso_timestamp(published2)
        if dt1 != datetime.min and dt2 != datetime.min:
            time_diff = abs((dt1 - dt2).total_seconds()) / 3600.0  # diff in hours
            if time_diff <= time_window_hours:
                return True

    return False

def remove_duplicate_articles(articles: List[Union[Dict[str, Any], Article]]) -> List[Union[Dict[str, Any], Article]]:
    """
    Removes duplicates from a list of articles while preserving the order of occurrence.
    """
    unique_articles = []
    for art in articles:
        duplicate_found = False
        for unique_art in unique_articles:
            if is_duplicate(art, unique_art):
                duplicate_found = True
                break
        if not duplicate_found:
            unique_articles.append(art)
    return unique_articles
