# Macro Morning Dashboard

Static macroeconomics dashboard designed for GitHub Pages with a scheduled data refresh.

## What it includes

- Growth and activity metrics
- Labor market metrics
- Inflation and breakeven inflation
- Monetary policy and rates
- Financial conditions
- Trade, commodities, housing, leading indicators, and fiscal metrics
- Top 3 Yahoo Finance articles
- GitHub Actions refresh around 8:00 AM New York time
- Optional direct BEA sourcing for GDP and GDP components

## Local preview

Open `index.html` directly in a browser, or serve the folder with any static file server.

To refresh the dataset locally:

```bash
python3 scripts/update_macro_data.py
```

## BEA setup

The dashboard can use the BEA API directly for GDP, real GDP, and major GDP components.

1. Request a BEA API key from the official signup page: https://apps.bea.gov/API/signup/
2. Add it as an environment variable locally, or as a GitHub Actions repository secret named `BEA_API_KEY`
3. Re-run the `Refresh Macro Data` workflow

If `BEA_API_KEY` is not set, the dashboard still works and falls back to FRED-backed series where possible.

## Public hosting with GitHub Pages

1. In GitHub, open `Settings` -> `Pages`
2. Set the source to `GitHub Actions`
3. Run the `Deploy Pages` workflow once, or push a commit

Your public URL will usually be:

```text
https://maxholthouser.github.io/macro-dashboard/
```

## Morning refresh timing

GitHub Actions cron is UTC-based, so the refresh workflow runs at `12:00 UTC` and `13:00 UTC` each day and then checks whether the current New York local time is exactly 8:00 AM before updating data. This keeps the refresh aligned with `America/New_York` across daylight saving time changes.

## Notes

- Most series come from FRED.
- GDP and GDP-component data will come directly from BEA when `BEA_API_KEY` is configured.
- Yahoo Finance article collection can occasionally rate-limit.
- A few requested metrics such as PMI, Shiller CAPE, and Treasury supply outlook are left out of the live default feed because dependable free unattended sources are not as clean.
