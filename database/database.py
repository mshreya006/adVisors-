import sqlite3
import os
from datetime import datetime, timedelta, timezone
import contextlib
from typing import List, Dict, Any
import config
from database.models import Article

@contextlib.contextmanager
def get_db_connection():
    """Context manager to safely open and close SQLite database connections."""
    db_path = config.DATABASE_PATH
    # Only create directories if not running in memory
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes the database schema if tables do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table to store articles and their AI classifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                source_name TEXT,
                published_at TEXT,
                predicted_industry TEXT,
                industry_confidence REAL,
                fake_news_prediction TEXT,
                fake_news_confidence REAL,
                is_bookmarked INTEGER DEFAULT 0,
                fetched_at TEXT NOT NULL
            )
        """)
        
        # Table to store user industry searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                industry TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()

def insert_or_replace_articles(articles: List[Article]):
    """
    Inserts a list of articles. If an article already exists (by URL), 
    updates its details but preserves its is_bookmarked status.
    """
    if not articles:
        return
        
    now_str = datetime.now(timezone.utc).isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for article in articles:
            fetched_at = article.fetched_at if article.fetched_at else now_str
            
            cursor.execute("""
                INSERT INTO articles (
                    url, title, description, source_name, published_at, 
                    predicted_industry, industry_confidence, 
                    fake_news_prediction, fake_news_confidence, 
                    is_bookmarked, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    source_name = excluded.source_name,
                    published_at = excluded.published_at,
                    predicted_industry = excluded.predicted_industry,
                    industry_confidence = excluded.industry_confidence,
                    fake_news_prediction = excluded.fake_news_prediction,
                    fake_news_confidence = excluded.fake_news_confidence,
                    fetched_at = excluded.fetched_at
            """, (
                article.url, article.title, article.description, article.source_name, 
                article.published_at, article.predicted_industry, article.industry_confidence, 
                article.fake_news_prediction, article.fake_news_confidence, 
                article.is_bookmarked, fetched_at
            ))
        conn.commit()

def get_cached_articles(industry: str, expiry_minutes: int) -> List[Article]:
    """
    Checks Level 2 cache in SQLite. Returns a list of articles matching the industry
    that were fetched within the expiration time limit.
    """
    cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=expiry_minutes)).isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM articles 
            WHERE predicted_industry = ? 
              AND fetched_at >= ?
            ORDER BY published_at DESC
        """, (industry, cutoff_time))
        
        rows = cursor.fetchall()
        return [Article.from_row(row) for row in rows]

def get_bookmarked_articles() -> List[Article]:
    """Retrieves all bookmarked articles."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE is_bookmarked = 1 ORDER BY fetched_at DESC")
        rows = cursor.fetchall()
        return [Article.from_row(row) for row in rows]

def set_bookmark_status(url: str, is_bookmarked: bool):
    """Toggles bookmark state for an article by its unique URL."""
    val = 1 if is_bookmarked else 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE articles SET is_bookmarked = ? WHERE url = ?", (val, url))
        conn.commit()

def add_search_history(industry: str):
    """Records a search query in history."""
    now_str = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO search_history (industry, timestamp) VALUES (?, ?)", (industry, now_str))
        conn.commit()

def get_search_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves the recent search history."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT industry, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [{"industry": row["industry"], "timestamp": row["timestamp"]} for row in rows]
