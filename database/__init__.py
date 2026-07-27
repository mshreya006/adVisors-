# Database module package init
from database.database import (
    init_db,
    insert_or_replace_articles,
    get_cached_articles,
    get_bookmarked_articles,
    set_bookmark_status,
    add_search_history,
    get_search_history
)
from database.models import Article
