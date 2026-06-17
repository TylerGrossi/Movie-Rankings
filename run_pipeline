"""
Movie data pipeline runner.

Runs enrichment and prediction scripts in order:
  1. enrich_ratings_api
  2. enrich_watchlist_api
  3. predicted_score_model

Usage:
    python run_pipeline
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

STEPS = [
    "enrich_ratings_api",
    "enrich_watchlist_api",
    "predicted_score_model",
]


def run_step(script_name: str) -> int:
    script_path = SCRIPT_DIR / script_name
    print(f"\n{'=' * 60}")
    print(f"Running: {script_name}")
    print(f"{'=' * 60}\n")
    result = subprocess.run([sys.executable, str(script_path)], cwd=SCRIPT_DIR)
    return result.returncode


def main() -> int:
    for i, script in enumerate(STEPS, start=1):
        print(f"\n[Step {i}/{len(STEPS)}]")
        code = run_step(script)
        if code != 0:
            print(f"\nPipeline stopped: {script} exited with code {code}")
            return code

    print(f"\n{'=' * 60}")
    print("Pipeline completed successfully.")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())