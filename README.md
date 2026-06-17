# Movies

Personal movie analytics project: export IMDb data, enrich it with OMDb/TMDB APIs, predict how you'll rate unwatched films, and explore everything in a Power BI dashboard.

## What this repo does

```text
IMDb export          API enrichment           ML predictions          Dashboard
───────────          ──────────────           ──────────────          ─────────
imdb_ratings.csv  →  Ratings_Enriched.csv  →                      →  Power BI
imdb_watchlist.csv → Watchlist_Enriched.csv → Predicted_Scores.csv →  (Movie BI/)
                     (OMDb + TMDB)            (XGBoost model)
```

1. **Pull** — Download your latest IMDb ratings and watchlist (`imdb_api_pull`).
2. **Enrich** — Add RT scores, cast, keywords, box office, and more from OMDb and TMDB.
3. **Predict** — Train on your rated movies and score your watchlist (`Predicted Score`, `Star Percentage`).
4. **Visualize** — Open the PBIP project in Power BI Desktop (`Movie BI/`).

## Quick start

### Prerequisites

- Python 3.10+ (Anaconda is fine)
- Chrome (only for `imdb_api_pull`)
- [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (for the dashboard)
- API keys: [OMDb](https://www.omdbapi.com/apikey.aspx), [TMDB](https://www.themoviedb.org/settings/api)

### Install dependencies

```bash
pip install requests pandas openpyxl python-dotenv scikit-learn joblib xgboost selenium webdriver-manager
```

### Environment variables

Create a `.env` file in the project root (already gitignored):

```env
OMDB_API_KEY=your_omdb_key
TMDB_API_KEY=your_tmdb_key

# Only needed for imdb_api_pull
IMDB_USER_ID=your_imdb_user_id
IMDB_AT_MAIN=
IMDB_UBID_MAIN=
IMDB_SESSION_ID=
```

### Run the full pipeline

From the project root:

```bash
python run_pipeline
```

This runs, in order:

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `enrich_ratings_api` | `imdb_ratings.csv`, `Movies Ranks.xlsm` | `Ratings_Enriched.csv` |
| 2 | `enrich_watchlist_api` | `imdb_watchlist.csv` | `Watchlist_Enriched.csv` |
| 3 | `predicted_score_model` | enriched CSVs, `Movies Ranks.xlsm` | `Predicted_Scores.csv`, `movie_score_predictor.pkl` |

The pipeline stops if any step fails.

### Run steps individually

All Python scripts are extensionless files in the project root. Run them with `python <script_name>`:

```bash
python imdb_api_pull          # optional: export fresh IMDb CSVs
python enrich_ratings_api
python enrich_watchlist_api
python predicted_score_model
```

## Key files

| File | Purpose |
|------|---------|
| `imdb_ratings.csv` | Raw IMDb ratings export |
| `imdb_watchlist.csv` | Raw IMDb watchlist export |
| `Movies Ranks.xlsm` | Personal scores and ranking tables (directors, actors, genres) |
| `Ratings_Enriched.csv` | Rated movies with API metadata + `My_Score` |
| `Watchlist_Enriched.csv` | Watchlist with API metadata |
| `Predicted_Scores.csv` | Watchlist with predicted ratings |
| `movie_score_predictor.pkl` | Saved trained model |
| `run_pipeline` | Orchestrates enrichment + prediction |
| `Movie BI/` | Power BI project (see [Movie BI/README.md](Movie%20BI/README.md)) |

## Data notes

- **Enrichment scripts** cache progress and save incrementally, so re-runs skip already-fetched movies.
- **`Movies Ranks.xlsm`** is the source of truth for your personal scores used in training and in several Power BI tables. Keep paths consistent if you move the project.
- **`Predicted_Scores.csv`** is also loaded by the Power BI model from a GitHub raw URL. After updating predictions locally, push that file to the linked repo if the dashboard should reflect the latest scores.

## Project layout

```text
Movies/
├── README.md                 # This file
├── AGENTS.md                 # Instructions for AI coding agents
├── run_pipeline              # Pipeline runner
├── imdb_api_pull             # Selenium IMDb export
├── enrich_ratings_api        # OMDb + TMDB enrichment (ratings)
├── enrich_watchlist_api      # OMDb + TMDB enrichment (watchlist)
├── predicted_score_model     # XGBoost score + star predictor
├── Movies Ranks.xlsm         # Personal rankings workbook
├── *.csv                     # Data inputs/outputs
├── movie_score_predictor.pkl # Trained model artifact
├── Old Models/               # Legacy notebooks and experiments
└── Movie BI/                 # Power BI PBIP dashboard
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ERROR: Set your OMDb/TMDB API key` | Add keys to `.env` |
| `imdb_ratings.csv not found` | Run `python imdb_api_pull` or export manually from IMDb |
| `Ratings_Enriched.csv not found` | Run `enrich_ratings_api` before `predicted_score_model` |
| Enrichment is slow | Normal — APIs are rate-limited; progress is saved between runs |
| Power BI can't refresh | Check local paths in semantic model tables and GitHub URL for `Predicted_Scores.csv` |
