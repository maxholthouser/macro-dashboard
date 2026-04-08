#!/usr/bin/env python3

import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_PATH = DATA_DIR / "macro-data.js"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BEA_API_KEY = os.getenv("BEA_API_KEY", "").strip()
CURL_TIMEOUT = "12"
CURL_RETRIES = "1"

SERIES_CONFIG = {
    "gdp_real": {"id": "GDPC1", "cosd": "2018-01-01"},
    "gdp_nominal": {"id": "GDP", "cosd": "2018-01-01"},
    "consumption": {"id": "PCEC96", "cosd": "2018-01-01"},
    "investment": {"id": "GPDIC1", "cosd": "2018-01-01"},
    "government": {"id": "GCEC1", "cosd": "2018-01-01"},
    "net_exports": {"id": "NETEXC", "cosd": "2018-01-01"},
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

MARKET_QUOTE_CONFIG = {
    "sp500": {"symbol": "%5EGSPC", "range": "1mo", "interval": "1d"},
    "oil": {"symbol": "CL=F", "range": "1mo", "interval": "1d"},
    "gold": {"symbol": "GC=F", "range": "1mo", "interval": "1d"},
    "copper": {"symbol": "HG=F", "range": "1mo", "interval": "1d"},
}

BEA_GDP_TABLES = {
    "current": {
        "table_name": "T10105",
        "series": {
            "gdp_nominal": "1",
            "consumption": "2",
            "investment": "7",
            "government": "22",
            "net_exports": "15",
        },
    },
    "real": {
        "table_name": "T10106",
        "series": {
            "gdp_real": "1",
        },
    },
}

COVERAGE_NOTES = [
    "Most economic series come from FRED, which republishes official releases from BEA, BLS, the Fed, Census, EIA, IMF, and the Chicago Fed.",
    "GDP, real GDP, and the major GDP components can come directly from the BEA NIPA API when a BEA key is configured.",
    "PMI, Shiller CAPE, and Treasury supply outlook are not included as live fields here because dependable free unattended sources are weak.",
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


def log(message):
    print(message, flush=True)


def fetch_text(url, label=None):
    source_label = label or urlparse(url).netloc
    log(f"Fetching {source_label}")
    result = subprocess.run(
        [
            "curl",
            "--http1.1",
            "--retry",
            CURL_RETRIES,
            "--retry-delay",
            "1",
            "-A",
            USER_AGENT,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            CURL_TIMEOUT,
            url,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl exit {result.returncode}: {result.stderr.strip() or 'request failed'}")
    return result.stdout


def fetch_json(url, label=None):
    return json.loads(fetch_text(url, label))


def fetch_fred_series(config):
    series_id = config["id"]
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{urlencode({'id': series_id, 'cosd': config['cosd']})}"
    rows = []
    for row in csv.DictReader(fetch_text(url, f"FRED {series_id}").splitlines()):
        value = row.get(series_id, ".")
        if value in (".", "", None):
            continue
        rows.append({"date": row["DATE"], "value": float(value)})
    return rows


def fetch_all_series():
    series_map = {}
    failures = []
    total = len(SERIES_CONFIG)
    for index, (key, config) in enumerate(SERIES_CONFIG.items(), start=1):
        try:
            log(f"[{index}/{total}] Loading {key} ({config['id']})")
            series_map[key] = fetch_fred_series(config)
        except Exception as error:
            series_map[key] = []
            failures.append(f"{key} ({config['id']}): {error}")
            log(f"Failed {key}: {error}")
    return series_map, failures


def parse_bea_value(raw):
    if raw is None:
        return None
    cleaned = str(raw).replace(",", "").strip()
    if cleaned in {"", "(NA)", "NA"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_bea_time_period(value):
    text = str(value).strip()
    if re.fullmatch(r"\d{4}Q[1-4]", text):
        month = {"1": "01", "2": "04", "3": "07", "4": "10"}[text[-1]]
        return f"{text[:4]}-{month}-01"
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01-01"
    return ""


def fetch_bea_growth_series():
    if not BEA_API_KEY:
        return {}, "BEA_API_KEY not configured"
    merged = {}
    for table_name, table in BEA_GDP_TABLES.items():
        log(f"Loading BEA table {table_name}")
        params = {
            "UserID": BEA_API_KEY,
            "method": "GetData",
            "datasetname": "NIPA",
            "TableName": table["table_name"],
            "Frequency": "Q",
            "Year": "ALL",
            "ResultFormat": "json",
        }
        payload = fetch_json(f"https://apps.bea.gov/api/data/?{urlencode(params)}", f"BEA {table['table_name']}")
        rows = payload.get("BEAAPI", {}).get("Results", {}).get("Data", [])
        for series_key, line_number in table["series"].items():
            series_rows = []
            for row in rows:
                if str(row.get("LineNumber", "")).strip() != line_number:
                    continue
                value = parse_bea_value(row.get("DataValue"))
                date_label = parse_bea_time_period(row.get("TimePeriod", ""))
                if value is None or not date_label:
                    continue
                series_rows.append({"date": date_label, "value": value / 1000.0})
            if series_rows:
                merged[series_key] = sorted(series_rows, key=lambda item: item["date"])
    return merged, None


def iso_date_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()


def fetch_yahoo_chart_series(symbol, range_value="1mo", interval="1d"):
    payload = fetch_json(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{urlencode({'range': range_value, 'interval': interval, 'includePrePost': 'false'})}",
        f"Yahoo chart {symbol}",
    )
    result = payload.get("chart", {}).get("result", [])
    if not result:
        return []
    chart = result[0]
    timestamps = chart.get("timestamp", [])
    quotes = chart.get("indicators", {}).get("quote", [])
    closes = quotes[0].get("close", []) if quotes else []
    rows = []
    for timestamp, close in zip(timestamps, closes):
        if close in (None, ""):
            continue
        rows.append({"date": iso_date_from_timestamp(timestamp), "value": float(close)})
    return rows


def overlay_market_quotes(series_map):
    applied = []
    failures = []
    for key, config in MARKET_QUOTE_CONFIG.items():
        try:
            log(f"Refreshing live market quote for {key}")
            rows = fetch_yahoo_chart_series(config["symbol"], config["range"], config["interval"])
            if rows:
                series_map[key] = rows
                applied.append(key)
        except Exception as error:
            failures.append(f"{key} ({config['symbol']}): {error}")
            log(f"Failed market quote {key}: {error}")
    return applied, failures


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
                metric("Real GDP", fmt_num(value_of(series_map, 'gdp_real'), 1, 'B'), yoy_detail(series_map['gdp_real'], 4), date_of(series_map, 'gdp_real')),
                metric("Nominal GDP", fmt_num(value_of(series_map, 'gdp_nominal'), 1, 'B'), yoy_detail(series_map['gdp_nominal'], 4), date_of(series_map, 'gdp_nominal')),
                metric("Consumption", fmt_num(value_of(series_map, 'consumption'), 1, 'B'), yoy_detail(series_map['consumption'], 4), date_of(series_map, 'consumption')),
                metric("Investment", fmt_num(value_of(series_map, 'investment'), 1, 'B'), yoy_detail(series_map['investment'], 4), date_of(series_map, 'investment')),
                metric("Government", fmt_num(value_of(series_map, 'government'), 1, 'B'), yoy_detail(series_map['government'], 4), date_of(series_map, 'government')),
                metric("Net Exports", fmt_num(value_of(series_map, 'net_exports'), 1, 'B'), diff_detail(series_map['net_exports'], 'B', 1), date_of(series_map, 'net_exports')),
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
        {"title": "10Y minus 2Y spread", "kicker": "Leading Indicator", "color": "#2563eb", "fill": "rgba(37, 99, 235, 0.12)", "series": spread_series(series_map['yield_10y'], series_map['yield_2y'], 120, 100.0)},
        {"title": "CPI YoY", "kicker": "Inflation", "color": "#c77725", "fill": "rgba(199, 119, 37, 0.12)", "series": yoy_series(series_map['cpi'], 36)},
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
        parser.feed(fetch_text('https://finance.yahoo.com/', 'Yahoo Finance homepage'))
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
    except Exception as error:
        log(f"Failed Yahoo Finance headlines: {error}")
        return []


def build_payload():
    notes = list(COVERAGE_NOTES)
    series_map, failures = fetch_all_series()
    market_quote_keys, market_quote_failures = overlay_market_quotes(series_map)
    bea_series, bea_error = fetch_bea_growth_series()
    if bea_series:
        series_map.update(bea_series)
        notes.append("GDP, real GDP, and major GDP components are sourced directly from the BEA NIPA API in this refresh.")
    elif bea_error:
        notes.append(f"BEA direct GDP sourcing inactive: {bea_error}.")
    if market_quote_keys:
        notes.append("S&P 500 and selected commodities are refreshed from Yahoo Finance chart data for a more current market snapshot.")
    if failures:
        notes.append('Some series were unavailable in the latest refresh: ' + '; '.join(failures[:6]))
    if market_quote_failures:
        notes.append('Some live market quote refreshes were unavailable: ' + '; '.join(market_quote_failures[:4]))
    articles = fetch_yahoo_finance_articles()
    if not articles:
        notes.append('Yahoo Finance headlines were unavailable during the latest refresh attempt.')
    sources = ["FRED", "Yahoo Finance"]
    if bea_series:
        sources.insert(1, "BEA")
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "yield_curve": build_yield_curve(series_map),
        "sections": build_sections(series_map),
        "charts": build_charts(series_map),
        "yahoo_finance_top_articles": articles,
        "coverage_notes": notes,
    }


def main():
    log("Preparing output directory")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUTPUT_PATH.write_text('window.MACRO_DASHBOARD_DATA = ' + json.dumps(payload, indent=2) + ';\n', encoding='utf-8')
    log(f"Wrote dashboard data to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
