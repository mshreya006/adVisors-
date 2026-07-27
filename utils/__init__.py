# Utilities package init
from utils.filters import contains_negative_keywords, filter_negative_news
from utils.duplicate_removal import (
    normalize_url,
    get_title_similarity,
    remove_duplicate_articles,
    is_duplicate
)
