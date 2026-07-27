# AI-Powered News Intelligence Platform

An enterprise-ready, modular, and resilient real-time news aggregation and analysis platform built with Python, Streamlit, SQLite, and Hugging Face Transformers.

This project refactors a basic news retrieval tool into a clean-architecture platform demonstrating software engineering patterns (Singleton, Repository, Fallback routing, 2-Level Caching, and robust Error boundaries) while remaining beginner/intermediate friendly for interviews.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Architecture and Folder Structure](#architecture-and-folder-structure)
4. [Application Workflow](#application-workflow)
5. [Database Schema (SQLite)](#database-schema-sqlite)
6. [AI & ML Models](#ai--ml-models)
7. [API Integrations & Fallbacks](#api-integrations--fallbacks)
8. [Caching Strategy (2-Level)](#caching-strategy-2-level)
9. [Installation & Setup](#installation--setup)
10. [Running the Application](#running-the-application)
11. [Running Tests](#running-tests)
12. [Future Scope](#future-scope)

---

## Project Overview
The **AI-Powered News Intelligence Platform** allows users to track industry trends dynamically. It fetches articles from primary and fallback REST APIs, filters duplicate/negative stories, runs semantic zero-shot classification to confirm industry matching, flags the fact quality (Fake vs. Real news), and provides bookmarking and query history.

---

## Key Features
- **Semantic Filtering**: Uses a pre-trained zero-shot classification BERT model to determine if articles belong to a selected domain (e.g. Technology Services) rather than basic keyword checks.
- **Fact-Quality Guardrails**: Integrates a transformer-based fake news classifier to predict article credibility.
- **Fail-Safe Fallbacks**: If deep learning libraries or Hugging Face Hub downloads fail, the system dynamically switches to keyword/linguistic heuristic classifiers so the application never crashes.
- **Dual API Clients**: Fetches from **NewsAPI.org**, automatically falling back to **GNews.io** if limits are exceeded, tokens are invalid, or network failures occur.
- **2-Level Cache**:
  - **Level 1 (UI-State Cache)**: Streamlit resource caching to maintain instances.
  - **Level 2 (Persistent DB Cache)**: Persists fetched news and predictions in SQLite. If a category is queried within 15 minutes, it serves from the DB instantly, reducing API hits and inference latency.
- **Deduplication**: Filters duplicate articles using normalized URL checking and fuzzy title similarity (`difflib.SequenceMatcher`).
- **Interactive Sidebar Widgets**: System status indicator, real-time bookmarks manager, search history tracking, and global US headlines.

---

## Architecture and Folder Structure
The project uses a modular layout following Clean Code principles:

```
project/
│
├── app.py                      # Main Streamlit UI entry point
├── config.py                   # Configuration and Environment variable loader
├── requirements.txt            # Project dependencies
├── README.md                   # Complete system documentation
├── .env.example                # Environment variables template
│
├── database/
│   ├── __init__.py             # Database exports
│   ├── database.py             # SQLite Connection Manager, schema initialization, cache ops
│   └── models.py               # Article entities & Row mapping
│
├── api/
│   ├── __init__.py             # API exports
│   ├── newsapi_client.py       # NewsAPI v2 Client with retry adapters
│   └── gnews_client.py         # GNews API v4 Fallback Client
│
├── ai/
│   ├── __init__.py             # AI exports
│   ├── bert_classifier.py      # BERT Zero-Shot classification & Keyword fallback
│   └── fake_news_detector.py   # Fake News sequence classifier & Clickbait heuristic fallback
│
├── services/
│   ├── __init__.py             # Services exports
│   └── article_service.py      # Core workflow orchestrator (APIs, Caching, AI pipes, Deduplication)
│
└── utils/
    ├── __init__.py             # Utilities exports
    ├── filters.py              # Rule-based negative keyword matching
    └── duplicate_removal.py    # URL normalization & SequenceMatcher title deduplication
```

---

## Application Workflow
```
[User Selects Industry]
          │
          ▼
[Check SQLite Local Cache] ──(Within Expiry Window)──► [Return Cached Articles] (Instant)
          │
          ├──(Cache Expired / Empty)
          ▼
[Query NewsAPI] ──(Succeeds)──┐
          │                   │
      (Failure)               ▼
          ├───► [Query GNews] ──► [Normalize Articles Schema]
                                         │
                                         ▼
                               [Remove Duplicates]
                                         │
                                         ▼
                                [Filter Negative News]
                                         │
                                         ▼
                              [BERT Zero-Shot Classifier]
                                         │
                                         ▼
                                [Fake News Detector]
                                         │
                                         ▼
                              [Save to SQLite DB Cache]
                                         │
                                         ▼
                               [Display in Cards]
```

---

## Database Schema (SQLite)
The application utilizes a local SQLite database file to manage cache, bookmarks, and histories.

### 1. `articles` Table
Stores raw metadata along with BERT semantic predicted industries and Fake/Real predictions:
- `url` (TEXT, PRIMARY KEY): The unique canonical link to the article.
- `title` (TEXT, NOT NULL): Article title.
- `description` (TEXT): Description or summary of the article.
- `source_name` (TEXT): The publishing agency or news channel.
- `published_at` (TEXT): ISO timestamp of publication.
- `predicted_industry` (TEXT): Industry determined by BERT.
- `industry_confidence` (REAL): BERT zero-shot probability score.
- `fake_news_prediction` (TEXT): Predicted class ("Real" or "Fake").
- `fake_news_confidence` (REAL): Fake news model probability score.
- `is_bookmarked` (INTEGER): Boolean flag (0 = No, 1 = Yes) for bookmarked articles.
- `fetched_at` (TEXT, NOT NULL): ISO timestamp when the entry was written to DB.

### 2. `search_history` Table
Tracks searches to feed the sidebar "Recent Searches" feature:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT)
- `industry` (TEXT): The name of the selected industry feed.
- `timestamp` (TEXT): Time of query.

---

## AI & ML Models
1. **BERT Industry Classification**:
   - **Model ID**: `typeform/distilbert-base-uncased-mnli` (~268MB).
   - **Purpose**: Zero-shot categorization into the 9 industries.
   - **Fallback**: Count match frequencies of the industry's keywords. Selects the label with the highest hit rate, assigning confidence dynamically.
2. **Fake News Detector**:
   - **Model ID**: `mrm8488/bert-tiny-finetuned-fake-news-detection` (~17MB).
   - **Purpose**: Binary classification ("Fake" vs "Real").
   - **Fallback**: Clickbait, exclamation count, and sensational uppercase word frequency heuristic analyser.

---

## 🔌 API Integrations & Fallbacks
- **NewsAPI (Primary)**: Queries `/v2/everything` using keywords associated with the chosen industry. Queries `/v2/top-headlines` for the headlines sidebar.
- **GNews (Fallback)**: When NewsAPI exceeds limits (100 free requests/day), fails, or has an invalid token, GNews takes over silently, prompting a banner message: *"NewsAPI unavailable. Showing results from GNews."*

---

## Caching Strategy (2-Level)
1. **Level 1 (Session Resource Cache)**: Streamlit's `@st.cache_resource` caches the `ArticleService` instance on load, ensuring ML pipelines and API clients are only instantiated once.
2. **Level 2 (Database Persistence Cache)**: Evaluated during query time. If the database contains articles matching the target industry fetched within `CACHE_EXPIRY_MINUTES` (configured in `.env`), they are returned immediately, bypassing external APIs and neural network inference.

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd AI_News_Analyser/adVisors-
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` into a new `.env` file:
   ```bash
   cp .env.example .env
   ```
   Add your NewsAPI or GNews keys to the `.env` file. (A working default NewsAPI key is provided inside `config.py` for evaluation).

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application
Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
A browser tab will open automatically.

---

## Running Tests
The project features a full test suite built on python's `unittest` testing framework:
```bash
py tests/test_flow.py
```

---

## Future Scope
- **Neural Text Summarization**: Summarize article descriptions into brief bullet points using a T5-small model.
- **Sentiment Indicator**: Display negative, neutral, or positive sentiment trends for each industry.
- **User Authentication**: Allow multiple users to save distinct collections of bookmarked articles.
