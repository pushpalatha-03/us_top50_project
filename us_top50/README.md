# US Top 50 Playlist Performance & Song Popularity Trend Analysis

## Architecture
```
data/Atlantic_United_States.csv
        │
        ▼
┌─ src/data_pipeline.py ──────────────┐  Layer 1: ingest → validate → clean → features
│ load_and_validate · add_features    │  (rank 1-50, dup song-day, dates, artist normalisation)
│ song_features · artist_features     │
└──────────────┬──────────────────────┘
               ▼
┌─ src/analytics.py ──────────────────┐  Layer 2: pure analysis functions
│ ranking · song · artist · popularity│  (movement, entry/exit, correlations, content attrs)
│ · content-attribute analytics       │
└───────┬─────────────────┬───────────┘
        ▼                 ▼
  app.py (Streamlit)   run_eda.py ──► outputs/ (CSVs, research_paper.md, executive_summary.md)
  Layer 3: dashboard   Layer 4: batch reporting
        tests/ (pytest)
```
## Run
```bash
pip install -r requirements.txt
python run_eda.py          # tables + research paper + executive summary -> outputs/
streamlit run app.py       # dashboard
pytest -q                  # tests
```
## KPIs
Days on Chart · Average Rank · Rank Volatility Index (std of rank) · Popularity Trend Score (7-day rolling mean) ·
Artist Dominance Index (% of rank points, points = 51 − rank) · Explicit Content Share.

## Robustness (what the dashboard handles)
- Tiny/empty filter selections (1 row, 1 day, 1 song, rank 1-1, no album type) - panels show a note instead of crashing.
- **Reset all filters** button in the sidebar; stale song picks are dropped when the artist changes.
- Missing CSV, missing columns, other date formats (ISO / dd-mm-yyyy), UTF-8 / cp1252 encodings, and dirty rows
  (non-numeric values, rank outside 1-50, blank song) give a clear message or are dropped and counted.
- Stress tests: `python tests/fuzz_app.py <seed> <n>` (random filter combos on the real app) and
  `python tests/fuzz_functions.py` (all analytics on tiny subsets, warnings treated as errors). `pytest -q` runs unit tests.
