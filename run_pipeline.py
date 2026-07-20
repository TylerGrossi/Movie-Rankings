"""
Movie data pipeline runner.

Runs enrichment and prediction scripts in order:
  1. enrich_ratings_api
  2. enrich_watchlist_api
  3. predicted_score_model

Usage:
    python run_pipeline.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src" / "movies"

STEPS = [
    "enrich_ratings_api.py",
    "enrich_watchlist_api.py",
    "predicted_score_model.py",
]


def say(message: str = "") -> None:
    """Print, flushing immediately.

    Our own stdout is block-buffered when redirected to a file, but the child
    processes write straight to the file descriptor. Without flushing, every
    header here lands at the end of the log and the output reads out of order.
    """
    print(message, flush=True)


def run_step(script_name: str) -> int:
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        say(f"\nERROR: {script_path} not found.")
        return 1
    say(f"\n{'=' * 60}")
    say(f"Running: {script_name}")
    say(f"{'=' * 60}\n")
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT)
    return result.returncode


def main() -> int:
    for i, script in enumerate(STEPS, start=1):
        say(f"\n[Step {i}/{len(STEPS)}]")
        code = run_step(script)
        if code != 0:
            say(f"\nPipeline stopped: {script} exited with code {code}")
            return code

    say(f"\n{'=' * 60}")
    say("All steps ran. Validating outputs...")
    say(f"{'=' * 60}\n")

    # Steps can exit 0 while writing an empty or all-null CSV, so a clean run
    # is not proof of good data. Exit non-zero if the outputs don't hold up.
    check = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "check_outputs.py")], cwd=PROJECT_ROOT
    )
    if check.returncode != 0:
        say("\nPipeline ran but output validation FAILED (see above).")
        return check.returncode

    say(f"\n{'=' * 60}")
    say("Pipeline completed successfully.")
    say(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
