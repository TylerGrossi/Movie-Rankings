"""Reconcile the rated / watchlist split against Movies Ranks.xlsm.

The workbook is the owner's source of truth for what has actually been
watched and scored. IMDb's ratings export can lag it — a film scored in the
workbook may still be sitting in the IMDb watchlist. When that happens the
movie is wrong on both sides:

  * it is missing from training data (a real rated example, unused), and
  * it gets recommended back to the owner as something to watch.

Both matter more than they look on a 271-row dataset.
"""

import pandas as pd

import paths


def _norm(title) -> str:
    """Loose title match — mirrors the normalisation used during enrichment."""
    from enrich_ratings_api import normalize_title

    return normalize_title(str(title).strip().lower())


def workbook_titles() -> dict:
    """{normalised title: (original title, score)} for every scored movie."""
    df = pd.read_excel(paths.MOVIE_RANKS_XLSM, sheet_name="Movie Rankings")
    df = df[df["Movie"].notna()]
    out = {}
    for _, row in df.iterrows():
        out[_norm(row["Movie"])] = (row["Movie"], row.get("Score"))
    return out


def find_misplaced(ratings: pd.DataFrame, watchlist: pd.DataFrame):
    """Titles scored in the workbook that are in the watchlist, not the ratings.

    Returns a list of (watchlist_index, title, score).
    """
    scored = workbook_titles()
    rated = {_norm(m) for m in ratings["Movie"].dropna()}

    misplaced = []
    for i, title in watchlist["Movie"].dropna().items():
        key = _norm(title)
        if key in scored and key not in rated:
            misplaced.append((i, title, scored[key][1]))
    return misplaced


def reconcile_watched(ratings: pd.DataFrame, watchlist: pd.DataFrame):
    """Move workbook-scored movies out of the watchlist and into the ratings.

    Returns (ratings, watchlist, moved_titles). The enriched metadata columns
    are shared between the two files, so a misplaced row carries everything the
    model needs — only My_Score has to be attached.
    """
    misplaced = find_misplaced(ratings, watchlist)
    if not misplaced:
        return ratings, watchlist, []

    idx = [i for i, _, _ in misplaced]
    moved = watchlist.loc[idx].copy()
    moved["My_Score"] = [score for _, _, score in misplaced]

    # Keep only columns the ratings frame already knows about.
    moved = moved.reindex(columns=ratings.columns)

    ratings_out = pd.concat([ratings, moved], ignore_index=True)
    watchlist_out = watchlist.drop(index=idx).reset_index(drop=True)
    return ratings_out, watchlist_out, [t for _, t, _ in misplaced]


def reconcile_files(verbose: bool = True) -> int:
    """Apply the move to the enriched CSVs on disk.

    Runs as a pipeline step so the split stays correct between runs, rather
    than each consumer having to reconcile in memory. Returns the number of
    movies moved.
    """
    ratings = pd.read_csv(paths.RATINGS_ENRICHED_CSV)
    watchlist = pd.read_csv(paths.WATCHLIST_ENRICHED_CSV)

    ratings_out, watchlist_out, moved = reconcile_watched(ratings, watchlist)
    if not moved:
        if verbose:
            print("  Nothing to reconcile — no scored movies left in the watchlist.")
        return 0

    ratings_out.to_csv(paths.RATINGS_ENRICHED_CSV, index=False)
    watchlist_out.to_csv(paths.WATCHLIST_ENRICHED_CSV, index=False)

    if verbose:
        print(f"  Moved {len(moved)} watched movies from watchlist -> ratings:")
        for title in moved:
            print(f"    - {title}")
        print(f"  Ratings:   {len(ratings)} -> {len(ratings_out)} rows")
        print(f"  Watchlist: {len(watchlist)} -> {len(watchlist_out)} rows")
    return len(moved)


if __name__ == "__main__":
    import paths as _paths

    _paths.use_utf8_console()
    print("Reconciling watched movies against Movies Ranks.xlsm...")
    reconcile_files()
