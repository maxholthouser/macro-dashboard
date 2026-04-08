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

## Local preview

Open `index.html` directly in a browser, or serve the folder with any static file server.

To refresh the dataset locally:

```bash
python3 scripts/update_macro_data.py
```

## Public hosting with GitHub Pages

1. Push the repository to the `main` branch.
2. In GitHub, open `Settings` -> `Pages`.
3. Set the source to `GitHub Actions`.
4. Run the `Deploy Pages` workflow once, or push a commit.

Your public URL will usually be:

```text
https://maxholthouser.github.io/macro-dashboard/
```

## Morning refresh timing

GitHub Actions cron is UTC-based, so the refresh workflow runs at `12:00 UTC` and `13:00 UTC` each day and then checks whether the current New York local time is exactly 8:00 AM before updating data. This keeps the refresh aligned with `America/New_York` across daylight saving time changes.

## Notes

- Most series come from FRED.
- Yahoo Finance article collection can occasionally rate-limit.
- A few requested metrics such as PMI, Shiller CAPE, and Treasury supply outlook are left out of the live default feed because dependable free unattended sources are not as clean.
