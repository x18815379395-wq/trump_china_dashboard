# 🇺🇸 Trump China Monitor

Streamlit dashboards that monitor how Donald Trump talks about China through two complementary experiences: a Truth Social-style board (`app.py`) and a Google News NLP board (`trump_china_dashboard.py`). The apps surface fresh content, run sentiment analysis, summarize key points, and log data for longer-term inspection.

## Features
- Dual dashboards: Truth Social mock feed + Google News scraper cover both social and media narratives.
- Automatic refresh every 5 minutes plus manual refresh controls to keep data current.
- Sentiment pipelines (TextBlob + Hugging Face Transformers) with lightweight long/short/hold trading cues.
- Plotly Express visuals that make positive/negative/neutral splits obvious at a glance.
- Persistent CSV logging (`trump_china_sentiment_data.csv`) with de-duplication by post ID.
- Streamlit caching (`st.cache_data`, `st.cache_resource`) to avoid redundant network calls and model loads.

## Repository Layout
- `app.py` — Truth Social themed dashboard, CSV persistence, mock data generator, TextBlob sentiment.
- `trump_china_dashboard.py` — Google News RSS scraper plus transformer summarization & sentiment.
- `trump_china_sentiment_data.csv` — rolling store of processed posts for historical review.
- `requirements.txt.txt` — dependency list (rename to `requirements.txt` for most deployment targets).
- `venv/` — optional local virtual environment (safe to ignore in deployments).

## Getting Started
1. Install Python 3.10+ and `pip`.
2. (Optional) create a virtual environment: `python -m venv venv` followed by `source venv/bin/activate` (macOS/Linux) or `venv\\Scripts\\activate` (Windows).
3. Install dependencies: `pip install -r requirements.txt.txt` (after renaming to `requirements.txt` if needed).
4. For the transformer dashboard, make sure outbound network access is allowed so Hugging Face models can download on first run.

## Running the Dashboards
### Truth Social Sentiment Board (`app.py`)
```
streamlit run app.py
```
- Generates or ingests posts, filters for the keyword "China", analyzes sentiment with TextBlob, renders a dataframe + bar chart, and appends results to `trump_china_sentiment_data.csv`.
- Session-state caching (`truth_posts`, `last_refresh_time`) prevents unnecessary fetches; tweak `REFRESH_INTERVAL` and `SENTIMENT_THRESHOLD` constants to change behavior.

### Google News NLP Board (`trump_china_dashboard.py`)
```
streamlit run trump_china_dashboard.py
```
- Scrapes Google News RSS for "Trump China", summarizes each article, classifies sentiment with Hugging Face pipelines, and displays a sentiment distribution.
- First launch downloads large models (~1.5 GB). Keep the process warm or switch to distilled models if cold-start latency or memory pressure is an issue.

## Data & Caching
- `trump_china_sentiment_data.csv` stores the processed Truth Social-style feed. Saving logic keeps timestamps as datetimes and deduplicates by `帖子ID`.
- Streamlit caching keeps heavy operations from rerunning on every interaction. Clear the caches or bump `REFRESH_INTERVAL` when you need fresher data.
- For multi-user deployments, consider file locking or moving storage to SQLite/Supabase to avoid concurrent write collisions.

## Configuration Tips
- Tune constants (`REFRESH_INTERVAL`, `SENTIMENT_THRESHOLD`, cache keys) directly in the scripts or expose them via environment variables.
- Set `HF_HOME` or `TRANSFORMERS_CACHE` to persist downloaded models between deployments.
- Rename `requirements.txt.txt` to `requirements.txt` (or symlink it) so Streamlit Cloud, Docker, and CI pipelines automatically pick it up.

## Roadmap / Ideas
- Replace the mock Truth Social feed with the real fetcher and share logic between dashboards.
- Harden Google News requests with retry/backoff logic and a custom User-Agent to prevent transient failures.
- Add filters (date range, sentiment, keyword) and moving-average stats for richer insight.
- Package the fetch/analyze helpers into a module and add pytest coverage for parsing, caching, and CSV merging routines.
