"""Canonical file locations for the Movies pipeline.

Single source of truth for where data lives. Import from here rather than
rebuilding paths from __file__ — that way a layout change is a one-file edit.

Layout:
    data/raw/        IMDb exports (input, overwritten by imdb_api_pull)
    data/processed/  enriched CSVs and predictions (generated)
    models/          trained model artifact (generated)
    Movies Ranks.xlsm  user-maintained, stays at repo root (Power BI reads it
                       from an absolute path — do not move it)
"""

import sys
from pathlib import Path


def use_utf8_console() -> None:
    """Make stdout/stderr UTF-8 safe.

    The scripts print check marks and other non-ASCII progress characters.
    On Windows the default console encoding is cp1252, which raises
    UnicodeEncodeError mid-run. Call this before any printing.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Raw IMDb exports
IMDB_RATINGS_CSV = DATA_RAW / "imdb_ratings.csv"
IMDB_WATCHLIST_CSV = DATA_RAW / "imdb_watchlist.csv"

# Generated
RATINGS_ENRICHED_CSV = DATA_PROCESSED / "Ratings_Enriched.csv"
WATCHLIST_ENRICHED_CSV = DATA_PROCESSED / "Watchlist_Enriched.csv"
PREDICTED_SCORES_CSV = DATA_PROCESSED / "Predicted_Scores.csv"
MODEL_PKL = MODELS_DIR / "movie_score_predictor.pkl"

# User-maintained input
MOVIE_RANKS_XLSM = PROJECT_ROOT / "Movies Ranks.xlsm"


def ensure_output_dirs() -> None:
    """Create generated-output directories if they don't exist."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
