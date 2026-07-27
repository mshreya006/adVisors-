import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any

import config
from database.database import (
    get_cached_articles,
    insert_or_replace_articles,
    add_search_history
)
from database.models import Article
from api.newsapi_client import NewsAPIClient
from api.gnews_client import GNewsClient
from ai.bert_classifier import BERTClassifier
from ai.fake_news_detector import FakeNewsDetector
from utils.filters import filter_negative_news
from utils.duplicate_removal import remove_duplicate_articles

logger = logging.getLogger(__name__)

class ArticleService:
    def __init__(self):
        self.news_client = NewsAPIClient()
        self.gnews_client = GNewsClient()
        self.bert_classifier = BERTClassifier()
        self.fake_news_detector = FakeNewsDetector()

    def get_model_statuses(self) -> Dict[str, str]:
        """Returns the status of the AI models (loaded or running on fallback)."""
        return {
            "bert": "Fallback (Keyword-Based)" if self.bert_classifier.use_fallback else "Active (BERT Zero-Shot)",
            "fake_news": "Fallback (Linguistic Heuristics)" if self.fake_news_detector.use_fallback else "Active (Transformer Classifier)"
        }

    def fetch_and_process_industry_news(self, industry: str) -> Tuple[List[Article], bool, str]:
        """
        Retrieves articles for a given industry.
        Returns:
            - List of Article models.
            - is_from_cache: boolean indicating if data was loaded from Level 2 SQLite cache.
            - api_source: string indicating which source was used ("NewsAPI", "GNews", or "SQLite Cache").
        """
        # Step 1: Check SQLite Cache (Level 2 Cache)
        cached = get_cached_articles(industry, config.CACHE_EXPIRY_MINUTES)
        if cached:
            logger.info(f"Loaded {len(cached)} articles for industry '{industry}' from SQLite Cache.")
            return cached, True, "SQLite Cache"

        # Record this search in database history
        try:
            add_search_history(industry)
        except Exception as e:
            logger.warning(f"Failed to record search history: {e}")

        # Step 2: Fetch articles using APIs
        raw_articles = []
        api_source = ""
        keywords = config.INDUSTRY_KEYWORDS.get(industry, [industry])
        
        try:
            logger.info(f"Attempting to fetch news from NewsAPI for industry '{industry}'.")
            raw_articles = self.news_client.fetch_by_keywords(keywords)
            api_source = "NewsAPI"
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}. Attempting fallback to GNews.")
            try:
                raw_articles = self.gnews_client.fetch_by_keywords(keywords)
                api_source = "GNews"
            except Exception as ge:
                logger.error(f"GNews fallback also failed: {ge}")
                raise RuntimeError("Both primary NewsAPI and fallback GNews API are currently unavailable.") from ge

        if not raw_articles:
            return [], False, api_source

        # Step 3: Remove duplicate articles (fuzzy title & URL matching)
        deduplicated = remove_duplicate_articles(raw_articles)

        # Step 4: Rule-based negative keyword filtering
        filtered = filter_negative_news(deduplicated)

        # Step 5: Run AI Classifiers and map to Database models
        processed_articles = []
        all_labels = list(config.INDUSTRY_KEYWORDS.keys())
        now_str = datetime.now(timezone.utc).isoformat()

        for art in filtered:
            title = art.get('title', '')
            description = art.get('description', '')
            url = art.get('url', '')
            published_at = art.get('publishedAt', art.get('published_at', now_str))
            source_name = art.get('source_name', 'Unknown Source')

            if not url or not title:
                continue

            # Run BERT industry classification
            pred_industry, ind_confidence = self.bert_classifier.classify_article(
                title, description, all_labels
            )

            # Store predictions for all fetched articles to optimize database cache
            # Run Fake News detection
            fake_label, fake_confidence = self.fake_news_detector.detect_fake_news(title, description)

            article_obj = Article(
                url=url,
                title=title,
                description=description or 'No description available.',
                source_name=source_name,
                published_at=published_at,
                predicted_industry=pred_industry,
                industry_confidence=ind_confidence,
                fake_news_prediction=fake_label,
                fake_news_confidence=fake_confidence,
                is_bookmarked=0,
                fetched_at=now_str
            )
            processed_articles.append(article_obj)

        # Step 6: Cache all classified articles in the SQLite DB
        if processed_articles:
            try:
                insert_or_replace_articles(processed_articles)
            except Exception as e:
                logger.error(f"Failed to save articles to SQLite: {e}")

        # Step 7: Filter result list to only return articles matching the selected industry
        # and satisfying the minimum BERT confidence threshold
        result_articles = [
            art for art in processed_articles 
            if art.predicted_industry == industry and art.industry_confidence >= config.MIN_INDUSTRY_CONFIDENCE
        ]

        # Sort by publication date descending
        result_articles.sort(key=lambda x: x.published_at, reverse=True)

        return result_articles, False, api_source

    def fetch_and_process_headlines(self) -> Tuple[List[Article], str]:
        """
        Retrieves top headlines. Uses database cache if fresh, otherwise calls APIs.
        Headlines are stored in DB with predicted_industry = 'Headlines'.
        """
        cached = get_cached_articles("Headlines", config.CACHE_EXPIRY_MINUTES)
        if cached:
            return cached, "SQLite Cache"

        raw_articles = []
        api_source = ""
        
        try:
            raw_articles = self.news_client.fetch_top_headlines()
            api_source = "NewsAPI"
        except Exception as e:
            logger.warning(f"NewsAPI headlines failed: {e}. Trying fallback to GNews.")
            try:
                raw_articles = self.gnews_client.fetch_top_headlines()
                api_source = "GNews"
            except Exception as ge:
                logger.error(f"GNews headlines fallback failed: {ge}")
                return [], "Unavailable"

        if not raw_articles:
            return [], api_source

        processed = []
        now_str = datetime.now(timezone.utc).isoformat()

        for art in raw_articles:
            url = art.get('url', '')
            title = art.get('title', '')
            description = art.get('description', '')
            source_name = art.get('source_name', 'Unknown Source')
            published_at = art.get('publishedAt', art.get('published_at', now_str))

            if not url or not title:
                continue

            # Run Fake News detection for headlines as well to add value
            fake_label, fake_confidence = self.fake_news_detector.detect_fake_news(title, description)

            article_obj = Article(
                url=url,
                title=title,
                description=description or '',
                source_name=source_name,
                published_at=published_at,
                predicted_industry="Headlines",
                industry_confidence=1.0,  # Explicitly headlines
                fake_news_prediction=fake_label,
                fake_news_confidence=fake_confidence,
                is_bookmarked=0,
                fetched_at=now_str
            )
            processed.append(article_obj)

        if processed:
            try:
                insert_or_replace_articles(processed)
            except Exception as e:
                logger.error(f"Failed to cache headlines: {e}")

        return processed, api_source
