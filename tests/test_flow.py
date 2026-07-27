import unittest
import os
import sys

# Add the project directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from database.models import Article
from database.database import (
    init_db,
    insert_or_replace_articles,
    get_cached_articles,
    get_bookmarked_articles,
    set_bookmark_status
)
from utils.filters import contains_negative_keywords
from utils.duplicate_removal import remove_duplicate_articles, normalize_url, get_title_similarity
from ai.bert_classifier import BERTClassifier
from ai.fake_news_detector import FakeNewsDetector

class TestNewsPlatformFlow(unittest.TestCase):
    def setUp(self):
        # Configure database path to run in a temporary test file
        config.DATABASE_PATH = "test_news_platform.db"
        init_db()

    def tearDown(self):
        # Clean up test database file
        if os.path.exists("test_news_platform.db"):
            try:
                os.remove("test_news_platform.db")
            except Exception:
                pass

    def test_config_defaults(self):
        """Verify configuration constants load successfully."""
        self.assertIsNotNone(config.NEWSAPI_KEY)
        self.assertEqual(config.CACHE_EXPIRY_MINUTES, 15)
        self.assertEqual(config.MIN_INDUSTRY_CONFIDENCE, 0.4)

    def test_negative_keyword_filtering(self):
        """Test rule-based negative keyword removal."""
        self.assertTrue(contains_negative_keywords("Tragedy in town", "A car accident happened"))
        self.assertTrue(contains_negative_keywords("Great news", "A political scandal erupted"))
        self.assertFalse(contains_negative_keywords("E-commerce store sales double", "Shopping details here"))

    def test_url_normalization(self):
        """Test URL query cleaning, netloc standardization, and trailing slash removal."""
        url1 = "https://www.example.com/news/?utm_source=fb&ref=123"
        url2 = "http://example.com/news"
        self.assertEqual(normalize_url(url1), normalize_url(url2))

    def test_title_similarity(self):
        """Test SequenceMatcher title similarity checks."""
        title1 = "Apple releases new iPhone 18 in USA"
        title2 = "Apple Releases New iPhone 18 In The USA"
        title3 = "Google updates Gemini models"
        
        self.assertGreater(get_title_similarity(title1, title2), 0.85)
        self.assertLess(get_title_similarity(title1, title3), 0.5)

    def test_duplicate_removal(self):
        """Test duplicate detection filters out redundant items based on url/title."""
        art1 = {
            "url": "https://example.com/item1?utm_source=twitter",
            "title": "Unique E-commerce Trend",
            "publishedAt": "2026-07-24T10:00:00Z",
            "source_name": "Source A"
        }
        art2 = {
            "url": "https://example.com/item1",
            "title": "Unique E-Commerce Trend",
            "publishedAt": "2026-07-24T10:01:00Z",
            "source_name": "Source B"
        }
        articles = [art1, art2]
        unique_list = remove_duplicate_articles(articles)
        self.assertEqual(len(unique_list), 1)

    def test_database_persistence_and_bookmarks(self):
        """Test article caching, lookup, and bookmark management in SQLite."""
        article = Article(
            url="https://domain.com/art",
            title="AI Revolution in Healthcare",
            description="DeepMind solves biological mysteries",
            source_name="Google Blog",
            published_at="2026-07-24T09:00:00Z",
            predicted_industry="Health and Wellness",
            industry_confidence=0.85,
            fake_news_prediction="Real",
            fake_news_confidence=0.98,
            is_bookmarked=0
        )
        
        # Save to DB
        insert_or_replace_articles([article])
        
        # Query cached
        cached = get_cached_articles("Health and Wellness", expiry_minutes=10)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0].url, article.url)
        self.assertEqual(cached[0].is_bookmarked, 0)
        
        # Bookmark
        set_bookmark_status(article.url, True)
        bookmarks = get_bookmarked_articles()
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].url, article.url)
        self.assertEqual(bookmarks[0].is_bookmarked, 1)

    def test_heuristics_classification_fallback(self):
        """Verify heuristic fallback logic for BERT classifier and Fake News detector."""
        bert = BERTClassifier()
        industry, conf = bert._heuristic_classify(
            "Flipkart and Amazon offer massive online shopping sales.",
            list(config.INDUSTRY_KEYWORDS.keys())
        )
        self.assertEqual(industry, "E-commerce")
        self.assertGreater(conf, 0.5)

        detector = FakeNewsDetector()
        label, conf = detector._heuristic_detect(
            "SHOCKING! SECRET CONSPIRACY EXPOSED!!!",
            "You won't believe this weird trick..."
        )
        self.assertEqual(label, "Fake")
        self.assertGreater(conf, 0.5)

if __name__ == '__main__':
    unittest.main()
