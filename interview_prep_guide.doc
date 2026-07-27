# Interview Preparation Guide: AI-Powered News Intelligence Platform

This document serves as a study guide for technical interviews, detailing the platform's architecture, design decisions, tech stack, and scalability trade-offs.

---

## 1. Project Implementation vs. Features & Functionality

### 💻 System Implementation (Code Architecture)
The platform is designed around **Clean Architecture** principles. Code is organized into decoupled layers, separating database persistence, external integrations, machine learning, business services, and presentation:

- **Presentation Layer (`app.py`)**: Responsible for layout, CSS injection, state maintenance, and handling user inputs. It has **zero direct access** to database details or raw API clients.
- **Service Layer (`services/article_service.py`)**: Acts as the system orchestrator. It manages the business flow: checks the database cache, coordinates API fallbacks, calls utility deduplication tools, feeds data to the AI classifiers, and updates cache states.
- **AI & ML Layer (`ai/`)**: Encapsulates model logic. Exposes a clean interface (`classify_article` and `detect_fake_news`) using Singletons to ensure models load only once in memory.
- **Data & Persistence Layer (`database/`)**: Manages the SQLite schema and connection pools using Python context managers to prevent socket leaks. Maps SQL database rows to structured Python dataclasses (`Article`).
- **REST API Client Layer (`api/`)**: Resilient HTTP connectors that reuse sessions and implement exponential backoff-based retries via `urllib3.util.Retry`.
- **Utility Layer (`utils/`)**: Reusable helper functions for rule filtering and text distance comparisons.

### ⚙️ Features & Functionality
- **Dual-API Resiliency**: Fetches news from NewsAPI. If the client catches an API rate limit or key error, it dynamically switches to GNews.
- **Fuzzy Deduplication**: Prevents syndication clutter by normalizing URLs (stripping UTM tracking parameters, protocol schemes, www) and comparing titles using Gestalt Pattern Matching.
- **Negative-News Filtering**: Filters out sensitive topics (tragedy, accident, crime) using a negative-word list.
- **AI Classification**: Maps articles semantically to one of 9 industries via zero-shot classification, and grades article reliability (Real/Fake).
- **2-Level Caching**: Uses memory-level caching for service states (`@st.cache_resource`) and SQLite persistence caching for article feeds.
- **User Bookmarks & Search History**: Toggles article bookmark flags and logs search history in database tables.

---

## 2. Tech Stack Used

- **Core**: Python 3.12 (modern features like `fromisoformat` support, type hinting, and dataclasses).
- **UI**: Streamlit 1.28.0 (an interactive pythonic front-end engine for quick analytical UI deployment).
- **Database**: SQLite3 (built-in relational SQL engine, serverless and file-backed).
- **Deep Learning**: PyTorch 2.2.2 & Hugging Face Transformers 4.48.3 (pipeline abstractions for CPU/GPU NLP inference).
- **Network**: Requests 2.34.2 & urllib3 2.7.0 (resilient HTTP session pooling).
- **Config**: Python-dotenv 1.0.1 (safe configuration injection via `.env` files).

---

## 3. Tool Justifications & Mapping

| Tool | Role | Why It Was Chosen (Justification) |
| :--- | :--- | :--- |
| **Streamlit** | UI / Presentation | Enables writing pure Python dashboards for analytical models. Eliminates the overhead of managing a React/Vue build chain, node dependencies, or Flask routing code, keeping the project highly readable. |
| **SQLite3** | Caching & Storage | Serverless, zero-configuration database that writes to a single local file. Unlike PostgreSQL or MySQL, it requires no setup script or active service port on the user's host machine, making it ideal for self-contained, offline-compatible projects. |
| **Hugging Face** | AI Inference Pipeline | Provides pre-trained, standard pipeline APIs (`zero-shot-classification`, `text-classification`) that support auto-downloading, caching, and CPU/GPU device selection out of the box. |
| **difflib** | Similarity Utility | Standard Python library that computes string similarity using the Gestalt Pattern Matching algorithm. Avoids compiling complex C-based distance libraries (like `Levenshtein` or `spacy`) which frequently fail to compile on Windows. |
| **urllib3.util.Retry** | API Resiliency | Integrates directly with requests sessions to handle transient errors (status 500, 502, 503, 504, connection losses) automatically with backoff timeouts. |

---

## 4. Design Choices & Alternatives

### A. Database Choice: SQLite vs. PostgreSQL/MySQL
- **Chosen**: SQLite.
- **Alternative**: PostgreSQL.
- **Why SQLite**: Local execution is key for interview demos. Setting up a PostgreSQL database requires docker containers or host installation, credentials, and network setup. SQLite stores everything in a local file, making it instantly portable.

### B. NLP Strategy: Zero-Shot Classifier vs. Pre-Trained Multi-Class BERT
- **Chosen**: Zero-Shot Classification (`distilbert-base-uncased-mnli`).
- **Alternative**: Fine-tuning a `bert-base-uncased` classifier on a custom news dataset.
- **Why Zero-Shot**: **Extensibility**. If you fine-tune a model on 9 specific categories, adding a 10th category requires gathering a new dataset, training, validating, and deploying a new model file. With Zero-Shot NLI models, you simply append the new category name to `config.py`, and the model classifies it immediately without re-training.

### C. ML Fail-safe: Fallback Heuristics vs. Fail-Hard
- **Chosen**: Heuristic Fallbacks.
- **Alternative**: Throwing an error and blocking page loads.
- **Why Heuristics**: Deep learning models are heavy. In environments without CUDA (GPUs), offline systems, or machines with Keras/TensorFlow library version mismatches, loading large PyTorch weights fails. Our architecture catches these errors and switches to keyword frequency and clickbait analysis rules, allowing the app to run on any computer.

---

## 5. "What if you changed..." - Interview Questions

> [!TIP]
> Use these answers to show structural understanding and adaptability.

### "What if we wanted to change the database from SQLite to PostgreSQL?"
- **Answer**: "Because we followed Clean Architecture, we would only have to modify [database/database.py](file:///d:/Shreya/AI_News_Analyser/adVisors-/database/database.py). The database queries are separated from the rest of the application. The `ArticleService` and the Streamlit frontend interact only with Python dataclass objects (`Article`), meaning not a single line of frontend or service layer code would change."

### "What if we wanted to add a 10th industry category?"
- **Answer**: "We only need to add the category and its search terms to the `INDUSTRY_KEYWORDS` dictionary in [config.py](file:///d:/Shreya/AI_News_Analyser/adVisors-/config.py). Because we use a Zero-Shot classification pipeline, the BERT model automatically begins evaluating texts against the new label without needing dataset re-labeling or model re-training."

### "What if we wanted to replace the local BERT model with an API call to OpenAI or Gemini?"
- **Answer**: "We would swap the pipeline initialization inside [ai/bert_classifier.py](file:///d:/Shreya/AI_News_Analyser/adVisors-/ai/bert_classifier.py) with an API request to the target model provider. The `ArticleService` calls `classify_article()` and is agnostic to *how* the classification is achieved, meaning the orchestration logic remains untouched."

---

## 6. Project Scalability & Extension

### 📈 Current Limits
- **Capacity**: Handles ~100 articles per search.
- **Bottleneck**: Network I/O (fetching from NewsAPI/GNews) and CPU-bound model inference (running BERT classification over 100 descriptions on a CPU can take 15–20 seconds).
- **Mitigation**: This is why our **Level 2 Cache** (SQLite) is critical. By storing classified articles for 15 minutes, subsequent users load them instantly without hitting APIs or triggering model inference.

### 🚀 Scaling to Production
To scale the platform to handle millions of articles and users, we would implement:

1. **Decoupled Background Workers**: 
   Currently, fetching and AI classification happen synchronously during the user's HTTP request. In production, we would use **Celery** or **RabbitMQ** to run cron-like workers. These workers fetch and classify articles in the background, writing them to a central database. The Streamlit app becomes **read-only** from the database, dropping loading times to milliseconds.
2. **Model Serving API**: 
   Instead of loading heavy model weights inside the Python web process, we would deploy the models as standalone microservices (e.g. FastAPI + Triton Inference Server or Hugging Face TGI) on GPU instances. The web server calls the model server via fast gRPC connections.
3. **Database Indexing**: 
   Add database indexes on the `articles` table:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_industry_fetched ON articles (predicted_industry, fetched_at DESC);
   ```

---

## 7. Scenario-Based Interview Q&A

### Scenario A: "NewsAPI and GNews keys both get rate-limited. How does the app handle it?"
- **Answer**: "The `ArticleService` catches connection/rate errors and reports a safe warning in the UI, prompting the user to check keys. However, if the user requests an industry that was recently fetched, the database cache will still serve the cached articles successfully, allowing the app to remain functional despite API blackouts."

### Scenario B: "SQLite databases lock when multiple users write concurrently. How do you resolve this?"
- **Answer**: "SQLite is a single-file database. We can optimize it for concurrency by enabling **WAL (Write-Ahead Logging)** mode, which allows multiple readers to read while a writer is writing. We also set a busy timeout (e.g. 10 seconds) on connections so they wait instead of failing immediately:
  ```python
  conn = sqlite3.connect(db_path, timeout=10.0)
  conn.execute("PRAGMA journal_mode=WAL;")
  ```
  If write volume grows further, we would migrate to PostgreSQL."

### Scenario C: "Your model fallbacks trigger on a server deployment because `torch` is too heavy for the hosting provider's free tier. How does the app adapt?"
- **Answer**: "The application starts successfully because model loading is wrapped in a try-except block. The UI displays the articles by falling back to the weighted keyword matching rules. It runs efficiently on minimal RAM and requires zero disk usage for model weights, enabling deployment on free hosting tiers (like Streamlit Community Cloud or Render Free Tier)."
