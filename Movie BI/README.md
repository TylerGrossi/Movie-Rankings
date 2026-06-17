# Movie Dashboard (Power BI)

Power BI project for exploring personal movie ratings, watch habits, director/actor/genre rankings, and predicted watchlist scores.

## Open the project

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/).
2. Open `Movie Dashboard.pbip` in this folder.
3. Refresh data when CSV/Excel sources have been updated.

The project uses the **PBIP** format (folder-based), not a single `.pbix` file. The legacy `Movie Dashboard.pbix` in the repo root may be outdated.

## Project structure

```text
Movie BI/
├── Movie Dashboard.pbip              # Entry point — open this in Power BI Desktop
├── Movie Dashboard.Report/           # Report pages, visuals, themes
├── Movie Dashboard.SemanticModel/    # Data model (TMDL tables, relationships)
├── create-watch-habits-page.mjs      # Page scaffolding scripts (Node)
├── update-watch-habits-page.mjs
└── fix-watch-habits-v3.mjs
```

## Data sources

The semantic model reads from two kinds of sources:

### Local Excel — `Movies Ranks.xlsm`

Used by tables such as:

- Movie Rankings
- Movie Directors / Actors / Genres
- Director, Actor, and Genre Rankings

These tables use **absolute Windows paths** pointing at the workbook in the parent `Movies/` folder. If you clone this repo elsewhere, update the `File.Contents(...)` paths in the `.tmdl` files under `Movie Dashboard.SemanticModel/definition/tables/`.

### Remote CSV — `Predicted_Scores.csv`

The **Movies to Watch** tables load predictions from GitHub:

```text
https://raw.githubusercontent.com/TylerGrossi/Movie-Rankings/refs/heads/main/Predicted_Scores.csv
```

After running `predicted_score_model` locally, push the updated `Predicted_Scores.csv` to that repo (or change the Power Query source to a local file) before refreshing the dashboard.

Some watchlist bridge tables also join the GitHub CSV with `Movies Ranks.xlsm` for director/actor metadata.

## Report pages

Pages live under `Movie Dashboard.Report/definition/pages/`. Notable pages include:

- **pgWatchHabits** — Watch habit breakdowns (location, language, year, rewatches, etc.)
- Additional analysis pages for movies, actors, directors, genres, series, and watchlist

Page JSON and visual definitions are edited directly in PBIR format or via helper scripts like `create-watch-habits-page.mjs`.

## Updating the dashboard after a pipeline run

1. Run `python run_pipeline` from the repo root (or refresh individual CSVs).
2. Ensure `Movies Ranks.xlsm` reflects your latest personal scores.
3. Push `Predicted_Scores.csv` to GitHub if the remote source is still in use.
4. Open `Movie Dashboard.pbip` and **Refresh** all queries.

## Working with PBIR / TMDL

- **Report visuals**: `Movie Dashboard.Report/definition/pages/<pageId>/visuals/<visualId>/visual.json`
- **Semantic model tables**: `Movie Dashboard.SemanticModel/definition/tables/*.tmdl`
- **Relationships**: `Movie Dashboard.SemanticModel/definition/relationships.tmdl`

When modifying reports programmatically, prefer the existing `.mjs` scaffolding scripts as patterns, or use the PBIR Report Builder skill for IBCS-compliant visuals.

## Node helper scripts

The `.mjs` files in this folder generate or patch PBIR page/visual JSON. They are one-off build tools, not part of the Python data pipeline. Run with Node.js if you need to regenerate watch-habits page structure:

```bash
node create-watch-habits-page.mjs
```
