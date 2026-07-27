import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Base Project Path
BASE_DIR = Path(__file__).resolve().parent

# API Keys
# Default fallback to original NewsAPI key for instant evaluation if env is not set
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "4d4e4be81eb342b28974ac7ffd90821d")
GNEWS_KEY = os.getenv("GNEWS_KEY", "")

# Database settings
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "news_platform.db"))

# Caching settings
CACHE_EXPIRY_MINUTES = int(os.getenv("CACHE_EXPIRY_MINUTES", "15"))

# AI Models settings
BERT_MODEL_NAME = os.getenv("BERT_MODEL_NAME", "typeform/distilbert-base-uncased-mnli")
FAKE_NEWS_MODEL_NAME = os.getenv("FAKE_NEWS_MODEL_NAME", "mrm8488/bert-tiny-finetuned-fake-news-detection")

# Thresholds
MIN_INDUSTRY_CONFIDENCE = float(os.getenv("MIN_INDUSTRY_CONFIDENCE", "0.4"))
MIN_FAKE_NEWS_CONFIDENCE = float(os.getenv("MIN_FAKE_NEWS_CONFIDENCE", "0.5"))

# API request retry settings
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "5"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))

# Industries and their search keywords (used for fetching candidates from APIs)
INDUSTRY_KEYWORDS = {
    'E-commerce': ['e-commerce', 'online shopping', 'retail', 'amazon shopping', 'flipkart deal', 'ecommerce offer'],
    'Health and Wellness': ['health', 'wellness', 'fitness', 'nutrition', 'skincare', 'longevity', 'aging', 'mood boost', 'supplement', 'beauty', 'cosmetics', 'personal care', 'makeup'],
    'Food and Beverage': ['food', 'beverage', 'restaurant', 'culinary', 'meat', 'meal prep', 'coffee', 'tea', 'drinks', 'chocolate', 'latte'],
    'Technology Services': ['tech', 'techs', 'IT services', 'software', 'cybersecurity', 'amazon tech', 'tech product', 'tesla tech'],
    'Fashion and Apparel': ['fashion', 'apparel', 'clothing', 'style', 'fabric', 'designer'],
    'Education and Tutoring': ['education', 'tutoring', 'digital learning'],
    'Home Improvement and Interior Design': ['home improvement', 'interior design', 'renovation', 'home decor', 'diy decoration'],
    'Digital Marketing': ['digital marketing', 'SEO', 'social media', 'content marketing'],
    'Sustainable and Green Businesses': ['sustainability', 'green business', 'eco-friendly']
}

# Negative keywords to filter out sensitive or tragic news (from original code)
NEGATIVE_KEYWORDS = ['tragedy', 'disaster', 'attack', 'crime', 'shooting', 'death', 'injury', 'accident', 'scandal']
