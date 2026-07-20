"""
Smoke check for pipeline outputs.

Encodes the manual validation that used to be done by eye: do the expected
files exist, do they have rows, and do the key columns survive?

Usage:
    python check_outputs.py

Exit code 0 = all checks passed, 1 = something is wrong.
"""

import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent / "src" / "movies"))
import paths  # noqa: E402

# (path, minimum rows, columns that must be present and non-empty)
CHECKS = [
    (paths.IMDB_RATINGS_CSV, 1, []),
    (paths.IMDB_WATCHLIST_CSV, 1, []),
    (paths.RATINGS_ENRICHED_CSV, 1, ["My_Score"]),
    (paths.WATCHLIST_ENRICHED_CSV, 1, []),
    (paths.PREDICTED_SCORES_CSV, 1, ["Predicted Score", "Star Percentage"]),
]

REQUIRED_INPUTS = [paths.MOVIE_RANKS_XLSM]


def check_file(path, min_rows, required_cols):
    """Return a list of failure messages for one file (empty = passed)."""
    failures = []
    if not path.exists():
        return [f"MISSING: {path}"]

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return [f"UNREADABLE: {path} ({exc})"]

    if len(df) < min_rows:
        failures.append(f"EMPTY: {path.name} has {len(df)} rows (expected >= {min_rows})")

    for col in required_cols:
        if col not in df.columns:
            failures.append(f"MISSING COLUMN: {path.name} has no '{col}'")
        elif df[col].notna().sum() == 0:
            failures.append(f"ALL NULL: {path.name}['{col}'] is entirely empty")

    if not failures:
        cols = f", cols OK: {required_cols}" if required_cols else ""
        print(f"  PASS  {path.name}  ({len(df)} rows{cols})")
    return failures


def main() -> int:
    print("Checking pipeline outputs...\n")
    failures = []

    for path in REQUIRED_INPUTS:
        if path.exists():
            print(f"  PASS  {path.name}  (present)")
        else:
            failures.append(f"MISSING REQUIRED INPUT: {path}")

    for path, min_rows, cols in CHECKS:
        failures.extend(check_file(path, min_rows, cols))

    if not paths.MODEL_PKL.exists():
        failures.append(f"MISSING: {paths.MODEL_PKL} (run predicted_score_model.py)")
    else:
        size_mb = paths.MODEL_PKL.stat().st_size / 1_000_000
        print(f"  PASS  {paths.MODEL_PKL.name}  ({size_mb:.1f} MB)")

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED:\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
