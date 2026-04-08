#!/usr/bin/env python3

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_PATH = DATA_DIR / "macro-data.js"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

SERIES_CONFIG = {
    "gdp_real": {"id": "GDPC1", "cosd": "2018-01-01"},
    "gdp_nominal": {"id": "GDP", "cosd": "2018-01-01"},
    "industrial_production": {"id": "INDPRO", "cosd": "2020-01-01"},
    "retail_sales": {"id": "RSAFS", "cosd": "2020-01-01"},
    "consumer_spending": {"id": "PCE", "cosd": "2020-01-01"},
    "unemployment": {"id": "UNRATE", "cosd": "2020-01-01"},
    "payrolls": {"id": "PAYEMS", "cosd": "2020-01-01"},
    "avg_hourly_earnings": {"id": "CES0500000003", "cosd": "2020-01-01"},
    "job_openings": {"id": "JTSJOL", "cosd": "2020-01-01"},
    "labor_force_participation": {"id": "CIVPART", "cosd": "2020-01-01"},
    "cpi": {"id": "CPIAUCSL", "cosd": "2020-01-01"},
    "core_cpi": {"id": "CPILFESL", "cosd": "2020-01-01"},
    "ppi": {"id": "PPIACO", "cosd": "2020-01-01"},
    "pce_deflator": {"id": "PCEPI", "cosd": "2020-01-01"},
    "core_pce": {"id": "PCEPILFE", "cosd": "2020-01-01"},
    "breakeven_5y": {"id": "T5YIE", "cosd": "2024-01-01"},
    "breakeven_10y": {"id": "T10YIE", "cosd": "2024-01-01"},
    "fed_funds": {"id": "DFF", "cosd": "2024-01-01"},
    "yield_3m": {"id": "DGS3MO", "cosd": "2024-01-01"},
    "yield_2y": {"id": "DGS2", "cosd": "2024-01-01"},
    "yield_5y": {"id": "DGS5", "cosd": "2024-01-01"},
    "yield_10y": {"id": "DGS10", "cosd": "2024-01-01"},
    "yield_30y": {"id": "DGS30", "cosd": "2024-01-01"},
    "m2": {"id": "M2SL", "cosd": "2020-01-01"},
    "sp500": {"id": "SP500", "cosd": "2024-01-01"},
    "ig_spread": {"id": "BAMLC0A0CM", "cosd": "2024-01-01"},
    "hy_spread": {"id": "BAMLH0A0HYM2", "cosd": "2024-01-01"},
    "dollar_index": {"id": "DTWEXBGS", "cosd": "2024-01-01"},
    "financial_conditions": {"id": "NFCI", "cosd": "2024-01-01"},
    "trade_balance": {"id": "BOPGSTB", "cosd": "2020-01-01"},
    "oil": {"id": "DCOILWTICO", "cosd": "2024-01-01"},
    "gold": {"id": "GOLDAMGBD228NLBM", "cosd": "2024-01-01"},
    "copper": {"id": "PCOPPUSDM", "cosd": "2020-01-01"},
    "leading_index": {"id": "USSLIND", "cosd": "2020-01-01"},
    "housing_starts": {"id": "HOUST", "cosd": "2020-01-01"},
    "building_permits": {"id": "PERMIT", "cosd": "2020-01-01"},
    "consumer_sentiment": {"id": "UMCSENT", "cosd": "2020-01-01"},
    "budget_balance": {"id": "FYFSGDA188S", "cosd": "2018-01-01"},
    "debt_to_gdp": {"id": "GFDEGDQ188S", "cosd": "2018-01-01"},
}

COVERAGE_NOTES = [
    "Most economic series come from FRED, which republishes official releases from BEA, BLS, the Fed, Census, EIA, IMF, and the Chicago Fed.",
    "PMI, Shiller CAPE, and Treasury supply outlook are not included as live fields here because dependable free unattended sources are weak.",
    "The leading indicator shown here uses a free proxy rather than the Conference Board LEI.",
    "Yahoo Finance headlines are collected from the live page each refresh and can occasionally rate-limit; when that happens, the last successful data file remains usable.",
]

class AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_anchor = False
        self.current_href = None
        self.current_text = []
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        self.in_anchor = True
        self.current_href = href
        self.current_text = []

    def handle_data(self, data):
        if self.in_anchor:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self.in_anchor:
            return
        text = " ".join(" ".join(self.current_text).split())
        self.anchors.append({"href": self.current_href, "text": text})
        self.in_anchor = False
        self.current_href = None
        self.current_text = []


def fetch_text(url):
    result = subprocess.run([
        "curl", "-A", USER_AGENT, "-L", "--fail", "--silent", "--show-error", "--max-time", "45", url
    ], capture_output=True, text=True, check=True)
    return result.stdout


def fetch_fred_series(config):
    series_id = config["id"]
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{urlencode({'id': series_id, 'cosd': config['cosd']})}"
    rows = []
    for row in csv.DictReader(fetch_text(url).splitlines()):
        value = row.get(series_id, ".")
        if value in (".", "", None):
            continue
        rows.append({"date": row["DATE"], "value": float(value)})
    return rows


def fetch_all_series():
    series_map = {}
    failures = []
    for key, config in SERIES_CONFIG.items():
        try:
            series_map[key] = fetch_fred_series(config)
        except Exception as error:
            series_map[key] = []
            failures.append(f"{key} ({config['id']}): {error}")
    return series_map, failures


def latest(rows):
    return rows[-1] if rows else None


def value_of(series_map, key):
    point = latest(series_map.get(key, []))
    return point["value"] if point else None


def date_of(series_map, key):
    point = latest(series_map.get(key, []))
    return point["date"] if point else ""


def pct_change(rows, periods_back):
    if len(rows) <= periods_back or rows[-1]["value"] == 0 or rows[-1 - periods_back]["value"] == 0:
        return None
    return ((rows[-1]["value"] / rows[-1 - periods_back]["value"]) - 1.0) * 100.0


def delta(rows, periods_back=1):
    if len(rows) <= periods_back:
        return None
    return rows[-1]["value"] - rows[-1 - periods_back]["value"]


def fmt_num(value, decimals=2, suffix=""):
    return "N/A" if value is None else f"{value:,.{decimals}f}{suffix}"


def fmt_pct(value, decimals=2):
    return fmt_num(value, decimals, "%")


def fmt_usd(value, decimals=2):
    return "N/A" if value is None else f"${value:,.{decimals}f}"


def metric(label, value, detail, date_label):
    return {"label": label, "value": value, "detail": detail, "date_label": date_label}


def diff_detail(rows, unit="pp", decimals=2):
    value = delta(rows)
    if value is None:
        return "Change unavailable"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f} {unit} vs prior"


def yoy_detail(rows, periods_back=12):
    value = pct_change(rows, periods_back)
    return f"YoY {fmt_pct(value, 1)}" if value is not None else "YoY unavailable"


def mom_detail(rows):
    value = pct_change(rows, 1)
    return f"MoM {fmt_pct(value, 1)}" if value is not None else "MoM unavailable"


def build_sections(series_map):
    return [
        {
            "kicker": "Growth",
            "title": "Growth & Activity",
            "metrics": [
                metric("Real GDP", fmt_num(value_of(series_map, 'gdp_real'), 0, 'B'), yoy_detail(series_map['gdp_real'], 4), date_of(series_map, 'gdp_real')),
                metric("Nominal GDP", fmt_num(value_of(series_map, 'gdp_nominal'), 0, 'B'), yoy_detail(series_map['gdp_nominal'], 4), date_of(series_map, 'gdp_nominal')),
                metric("Industrial Production", fmt_num(value_of(series_map, 'industrial_production'), 1), mom_detail(series_map['industrial_production']), date_of(series_map, 'industrial_production')),
                metric("Retail Sales", fmt_num(value_of(series_map, 'retail_sales'), 1, 'B'), mom_detail(series_map['retail_sales']), date_of(series_map, 'retail_sales')),
                metric("Consumer Spending", fmt_num(value_of(series_map, 'consumer_spending'), 1, 'B'), mom_detail(series_map['consumer_spending']), date_of(series_map, 'consumer_spending')),
            ],
        },
        {
            "kicker": "Labor",
            "title": "Labor Market",
            "metrics": [
                metric("Unemployment", fmt_pct(value_of(series_map, 'unemployment'), 1), diff_detail(series_map['unemployment'], 'pp', 1), date_of(series_map, 'unemployment')),
                metric("Nonfarm Payrolls", fmt_num(value_of(series_map, 'payrolls'), 0, 'k'), diff_detail(series_map['payrolls'], 'k', 0), date_of(series_map, 'payrolls')),
                metric("Wage Growth", fmt_usd(value_of(series_map, 'avg_hourly_earnings'), 2), yoy_detail(series_map['avg_hourly_earnings']), date_of(series_map, 'avg_hourly_earnings')),
                metric("Job Openings", fmt_num(value_of(series_map, 'job_openings'), 0, 'k'), mom_detail(series_map['job_openings']), date_of(series_map, 'job_openings')),
                metric("Participation Rate", fmt_pct(value_of(series_map, 'labor_force_participation'), 1), diff_detail(series_map['labor_force_participation'], 'pp', 1), date_of(series_map, 'labor_force_participation')),
            ],
        },
        {
            "kicker": "Inflation",
            "title": "Inflation",
            "metrics": [
                metric("CPI", fmt_pct(pct_change(series_map['cpi'], 12), 1), f"Index {fmt_num(value_of(series_map, 'cpi'), 1)}", date_of(series_map, 'cpi')),
                metric("Core CPI", fmt_pct(pct_change(series_map['core_cpi'], 12), 1), f"Index {fmt_num(value_of(series_map, 'core_cpi'), 1)}", date_of(series_map, 'core_cpi')),
                metric("PPI", fmt_pct(pct_change(series_map['ppi'], 12), 1), f"Index {fmt_num(value_of(series_map, 'ppi'), 1)}", date_of(series_map, 'ppi')),
                metric("PCE Deflator", fmt_pct(pct_change(series_map['pce_deflator'], 12), 1), f"Index {fmt_num(value_of(series_map, 'pce_deflator'), 1)}", date_of(series_map, 'pce_deflator')),
                metric("Core PCE", fmt_pct(pct_change(series_map['core_pce'], 12), 1), f"Index {fmt_num(value_of(series_map, 'core_pce'), 1)}", date_of(series_map, 'core_pce')),
                metric("5Y Breakeven", fmt_pct(value_of(series_map, 'breakeven_5y'), 2), diff_detail(series_map['breakeven_5y']), date_of(series_map, 'breakeven_5y')),
                metric("10Y Breakeven", fmt_pct(value_of(series_map, 'breakeven_10y'), 2), diff_detail(series_map['breakeven_10y']), date_of(series_map, 'breakeven_10y')),
            ],
        },
        {
            "kicker": "Policy",
            "title": "Monetary Policy & Rates",
            "metrics": [
                metric("Fed Funds", fmt_pct(value_of(series_map, 'fed_funds'), 2), diff_detail(series_map['fed_funds']), date_of(series_map, 'fed_funds')),
                metric("3-Month Treasury", fmt_pct(value_of(series_map, 'yield_3m'), 2), diff_detail(series_map['yield_3m']), date_of(series_map, 'yield_3m')),
                metric("2-Year Treasury", fmt_pct(value_of(series_map, 'yield_2y'), 2), diff_detail(series_map['yield_2y']), date_of(series_map, 'yield_2y')),
                metric("10-Year Treasury", fmt_pct(value_of(series_map, 'yield_10y'), 2), diff_detail(series_map['yield_10y']), date_of(series_map, 'yield_10y')),
                metric("30-Year Treasury", fmt_pct(value_of(series_map, 'yield_30y'), 2), diff_detail(series_map['yield_30y']), date_of(series_map, 'yield_30y')),
                metric("M2 Money Supply", fmt_num(value_of(series_map, 'm2'), 0, 'B'), yoy_detail(series_map['m2']), date_of(series_map, 'm2')),
            ],
        },
        {
            "kicker": "Markets",
            "title": "Financial Conditions",
            "metrics": [
                metric("S&P 500", fmt_num(value_of(series_map, 'sp500'), 2), diff_detail(series_map['sp500'], 'pts', 2), date_of(series_map, 'sp500')),
                metric("IG Spread", fmt_pct(value_of(series_map, 'ig_spread'), 2), diff_detail(series_map['ig_spread']), date_of(series_map, 'ig_spread')),
                metric("HY Spread", fmt_pct(value_of(series_map, 'hy_spread'), 2), diff_detail(series_map['hy_spread']), date_of(series_map, 'hy_spread')),
                metric("Dollar Index", fmt_num(value_of(series_map, 'dollar_index'), 2), diff_detail(series_map['dollar_index'], 'pts', 2), date_of(series_map, 'dollar_index')),
                metric("NFCI", fmt_num(value_of(series_map, 'financial_conditions'), 2), diff_detail(series_map['financial_conditions'], 'idx', 2), date_of(series_map, 'financial_conditions')),
                metric("Equity Valuation", "N/A", "P/E and CAPE omitted in default free feed", ""),
            ],
        },
        {
            "kicker": "Trade",
            "title": "External, Leading & Fiscal",
            "metrics": [
                metric("Trade Balance", fmt_num(value_of(series_map, 'trade_balance'), 1, 'B'), diff_detail(series_map['trade_balance'], 'B', 1), date_of(series_map, 'trade_balance')),
                metric("WTI Oil", fmt_usd(value_of(series_map, 'oil'), 2), diff_detail(series_map['oil'], 'USD', 2), date_of(series_map, 'oil')),
                metric("Gold", fmt_usd(value_of(series_map, 'gold'), 2), diff_detail(series_map['gold'], 'USD', 2), date_of(series_map, 'gold')),
                metric("Copper", fmt_usd(value_of(series_map, 'copper'), 2), mom_detail(series_map['copper']), date_of(series_map, 'copper')),
                metric("Leading Index", fmt_num(value_of(series_map, 'leading_index'), 1), diff_detail(series_map['leading_index'], 'idx', 1), date_of(series_map, 'leading_index')),
                metric("Housing Starts", fmt_num(value_of(series_map, 'housing_starts'), 0, 'k'), mom_detail(series_map['housing_starts']), date_of(series_map, 'housing_starts')),
                metric("Building Permits", fmt_num(value_of(series_map, 'building_permits'), 0, 'k'), mom_detail(series_map['building_permits']), date_of(series_map, 'building_permits')),
                metric("Consumer Sentiment", fmt_num(value_of(series_map, 'consumer_sentiment'), 1), diff_detail(series_map['consumer_sentiment'], 'pts', 1), date_of(series_map, 'consumer_sentiment')),
                metric("Budget Balance", fmt_pct(value_of(series_map, 'budget_balance'), 1), "Federal surplus/deficit as % of GDP", date_of(series_map, 'budget_balance')),
                metric("Debt to GDP", fmt_pct(value_of(series_map, 'debt_to_gdp'), 1), diff_detail(series_map['debt_to_gdp'], 'pp', 1), date_of(series_map, 'debt_to_gdp')),
            ],
        },
    ]


def spread_series(left_rows, right_rows, limit, multiplier=1.0):
    right_map = {row['date']: row['value'] for row in right_rows}
    history = []
    for row in left_rows:
        if row['date'] in right_map:
            history.append({'date': row['date'], 'value': round((row['value'] - right_map[row['date']]) * multiplier, 2)})
    return history[-limit:]


def yoy_series(rows, limit):
    history = []
    for index in range(12, len(rows)):
        prior = rows[index - 12]['value']
        if prior == 0:
            continue
        history.append({'date': rows[index]['date'], 'value': round(((rows[index]['value'] / prior) - 1.0) * 100.0, 2)})
    return history[-limit:]


def change_series(rows, limit):
    history = []
    for index in range(1, len(rows)):
        history.append({'date': rows[index]['date'], 'value': round(rows[index]['value'] - rows[index - 1]['value'], 2)})
    return history[-limit:]


def build_charts(series_map):
    return [
        {"title": "10Y minus 2Y spread", "kicker": "Leading Indicator", "color": "#2858d7", "fill": "rgba(40, 88, 215, 0.12)", "series": spread_series(series_map['yield_10y'], series_map['yield_2y'], 120, 100.0)},
        {"title": "CPI YoY", "kicker": "Inflation", "color": "#bc7a22", "fill": "rgba(188, 122, 34, 0.12)", "series": yoy_series(series_map['cpi'], 36)},
        {"title": "Payrolls change", "kicker": "Labor", "color": "#0f766e", "fill": "rgba(15, 118, 110, 0.12)", "series": change_series(series_map['payrolls'], 36)},
    ]


def build_yield_curve(series_map):
    labels = [('3M', 'yield_3m'), ('2Y', 'yield_2y'), ('5Y', 'yield_5y'), ('10Y', 'yield_10y'), ('30Y', 'yield_30y')]
    points = []
    for label, key in labels:
        value = value_of(series_map, key)
        points.append({"label": label, "value": value, "value_label": fmt_pct(value, 2), "date": date_of(series_map, key)})
    two_year = value_of(series_map, 'yield_2y')
    ten_year = value_of(series_map, 'yield_10y')
    three_month = value_of(series_map, 'yield_3m')
    spread_2s10s = None if ten_year is None or two_year is None else round((ten_year - two_year) * 100.0, 2)
    spread_3m10y = None if ten_year is None or three_month is None else round((ten_year - three_month) * 100.0, 2)
    regime = 'Unavailable'
    if spread_2s10s is not None or spread_3m10y is not None:
        regime = 'Inverted' if ((spread_2s10s is not None and spread_2s10s < 0) or (spread_3m10y is not None and spread_3m10y < 0)) else 'Normal'
    return {"points": points, "spread_2s10s_bp": spread_2s10s, "spread_3m10y_bp": spread_3m10y, "regime": regime}


def fetch_yahoo_finance_articles():
    try:
        parser = AnchorCollector()
        parser.feed(fetch_text('https://finance.yahoo.com/'))
        articles = []
        seen = set()
        for anchor in parser.anchors:
            title = ' '.join(anchor['text'].split())
            url = urljoin('https://finance.yahoo.com/', anchor['href'])
            if not title or '/article/' not in url:
                continue
            if 'finance.yahoo.com/markets/' not in url and 'finance.yahoo.com/news/' not in url:
                continue
            if url in seen:
                continue
            seen.add(url)
            articles.append({"title": title, "url": url, "summary": re.sub(r'\s+', ' ', title).strip()[:150]})
            if len(articles) == 3:
                break
        return articles
    except Exception:
        return []


def build_payload():
    series_map, failures = fetch_all_series()
    notes = list(COVERAGE_NOTES)
    if failures:
        notes.append('Some series were unavailable in the latest refresh: ' + '; '.join(failures[:6]))
    articles = fetch_yahoo_finance_articles()
    if not articles:
        notes.append('Yahoo Finance headlines were unavailable during the latest refresh attempt.')
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["FRED", "Yahoo Finance"],
        "yield_curve": build_yield_curve(series_map),
        "sections": build_sections(series_map),
        "charts": build_charts(series_map),
        "yahoo_finance_top_articles": articles,
        "coverage_notes": notes,
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUTPUT_PATH.write_text('window.MACRO_DASHBOARD_DATA = ' + json.dumps(payload, indent=2) + ';\n', encoding='utf-8')
    print(f'Wrote dashboard data to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
