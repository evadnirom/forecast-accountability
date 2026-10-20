# Forecast Accountability

An experimental Hamden, Connecticut weather forecast archive and accuracy scoreboard.

- Daily automatic forecast collection from GFS, ECMWF IFS, and ICON (through Open-Meteo).
- Archived predictions for each of the next seven days.
- Public read-only dashboard.
- Accuracy scores **only** when independent observations with source evidence are available.

## Activate website deployment
1. Open repository **Settings → Pages**.
2. Under **Build and deployment**, choose **GitHub Actions**.
3. Open **Actions → Daily forecast archive → Run workflow** for the initial snapshot.
4. Check that the workflow succeeds; then the website should be at https://evadnirom.github.io/forecast-accountability/ .

The cron schedule is 12:15 **UTC** daily, not local time. GitHub may delay scheduled actions, and may disable scheduled workflows after prolonged inactivity.

## Critical evidence rules
These are numerical model forecasts, not the predictions shown by consumer apps. Fetch time is **not** the forecast model initialization time. TV meteorologists are **not** individually ranked without attributable, archived dated forecasts.

To add observed 2 p.m. temperature values, create `data/observations.csv` using the header in `data/observations-template.csv`. Every measurement must include the observation date, station, temperature at 2 p.m. America/New_York, and an evidence URL. Without observations, the leaderboard correctly remains empty.

Forecasts are appended into `data/snapshots-YYYY.jsonl` and committed by GitHub Actions. This is an early research tool, not an operational weather alert service.

## Observed temperature collection

`collect_observations.py` imports independently measured airport METAR temperatures from the Iowa Environmental Mesonet (station HVN). It selects the closest valid report within **35 minutes** of 2 p.m. local time, stores the exact observation time and provenance, and revisits the past ten days for late arrivals. This is a **nearby airport comparison**, not a measurement at the Hamden forecast coordinate, and comparisons are approximate when the report is not exactly at 2 p.m.

The daily workflow now fetches observations before generating the public dashboard. The workflow change is committed, but successful execution of the new step is not yet verified. If the data source is temporarily unavailable, the workflow will fail instead of substituting invented observations.
