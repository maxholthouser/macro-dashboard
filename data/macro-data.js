window.MACRO_DASHBOARD_DATA = {
  "updated_at": "2026-04-07T12:00:00Z",
  "sources": ["FRED", "Yahoo Finance"],
  "yield_curve": {
    "points": [
      { "label": "3M", "value": 5.1, "value_label": "5.10%", "date": "Placeholder" },
      { "label": "2Y", "value": 4.6, "value_label": "4.60%", "date": "Placeholder" },
      { "label": "5Y", "value": 4.2, "value_label": "4.20%", "date": "Placeholder" },
      { "label": "10Y", "value": 4.3, "value_label": "4.30%", "date": "Placeholder" },
      { "label": "30Y", "value": 4.45, "value_label": "4.45%", "date": "Placeholder" }
    ],
    "spread_2s10s_bp": -30,
    "spread_3m10y_bp": -80,
    "regime": "Inverted"
  },
  "sections": [
    {
      "kicker": "Growth",
      "title": "Growth & Activity",
      "metrics": [
        { "label": "Real GDP", "value": "23,000B", "detail": "YoY 2.4%", "date_label": "Placeholder" },
        { "label": "Nominal GDP", "value": "30,000B", "detail": "YoY 5.1%", "date_label": "Placeholder" },
        { "label": "Consumption", "value": "16,100B", "detail": "YoY 2.7%", "date_label": "Placeholder" },
        { "label": "Investment", "value": "4,300B", "detail": "YoY 1.8%", "date_label": "Placeholder" },
        { "label": "Government", "value": "4,200B", "detail": "YoY 1.5%", "date_label": "Placeholder" },
        { "label": "Net Exports", "value": "-900B", "detail": "Change unavailable", "date_label": "Placeholder" },
        { "label": "Industrial Production", "value": "102.6", "detail": "MoM 0.2%", "date_label": "Placeholder" },
        { "label": "Retail Sales", "value": "710.0B", "detail": "MoM 0.4%", "date_label": "Placeholder" },
        { "label": "Consumer Spending", "value": "19,800.0B", "detail": "MoM 0.3%", "date_label": "Placeholder" }
      ]
    },
    {
      "kicker": "Labor",
      "title": "Labor Market",
      "metrics": [
        { "label": "Unemployment", "value": "4.10%", "detail": "+0.1 pp vs prior", "date_label": "Placeholder" },
        { "label": "Nonfarm Payrolls", "value": "158,627k", "detail": "+210k vs prior month", "date_label": "Placeholder" },
        { "label": "Wage Growth", "value": "$35.20", "detail": "YoY 4.0%", "date_label": "Placeholder" },
        { "label": "Job Openings", "value": "8,100k", "detail": "MoM -1.2%", "date_label": "Placeholder" },
        { "label": "Participation Rate", "value": "62.60%", "detail": "+0.1 pp vs prior", "date_label": "Placeholder" }
      ]
    },
    {
      "kicker": "Inflation",
      "title": "Inflation",
      "metrics": [
        { "label": "CPI", "value": "3.20%", "detail": "Index 319.0", "date_label": "Placeholder" },
        { "label": "Core CPI", "value": "3.40%", "detail": "Index 330.2", "date_label": "Placeholder" },
        { "label": "PPI", "value": "2.10%", "detail": "Index 255.0", "date_label": "Placeholder" },
        { "label": "PCE Deflator", "value": "2.60%", "detail": "Index 125.0", "date_label": "Placeholder" },
        { "label": "Core PCE", "value": "2.80%", "detail": "Index 127.5", "date_label": "Placeholder" },
        { "label": "5Y Breakeven", "value": "2.25%", "detail": "+0.02 pp vs prior", "date_label": "Placeholder" },
        { "label": "10Y Breakeven", "value": "2.30%", "detail": "+0.01 pp vs prior", "date_label": "Placeholder" }
      ]
    },
    {
      "kicker": "Policy",
      "title": "Monetary Policy & Rates",
      "metrics": [
        { "label": "Fed Funds", "value": "5.25%", "detail": "Change unavailable", "date_label": "Placeholder" },
        { "label": "3-Month Treasury", "value": "5.10%", "detail": "-0.01 pp vs prior", "date_label": "Placeholder" },
        { "label": "2-Year Treasury", "value": "4.60%", "detail": "-0.03 pp vs prior", "date_label": "Placeholder" },
        { "label": "10-Year Treasury", "value": "4.30%", "detail": "-0.02 pp vs prior", "date_label": "Placeholder" },
        { "label": "30-Year Treasury", "value": "4.45%", "detail": "-0.02 pp vs prior", "date_label": "Placeholder" },
        { "label": "Real 10Y Rate", "value": "2.00%", "detail": "10Y minus 10Y breakeven", "date_label": "Placeholder" },
        { "label": "M2 Money Supply", "value": "22,322B", "detail": "YoY 1.6%", "date_label": "Placeholder" }
      ]
    },
    {
      "kicker": "Markets",
      "title": "Financial Conditions",
      "metrics": [
        { "label": "S&P 500", "value": "6,878.88", "detail": "-29.98 pts vs prior", "date_label": "Placeholder" },
        { "label": "IG Spread", "value": "1.05%", "detail": "+0.01 pp vs prior", "date_label": "Placeholder" },
        { "label": "HY Spread", "value": "3.45%", "detail": "+0.04 pp vs prior", "date_label": "Placeholder" },
        { "label": "Dollar Index", "value": "121.20", "detail": "+0.22 pts vs prior", "date_label": "Placeholder" },
        { "label": "NFCI", "value": "-0.48", "detail": "+0.03 idx vs prior", "date_label": "Placeholder" },
        { "label": "Equity Valuation", "value": "N/A", "detail": "P/E and CAPE omitted in default free feed", "date_label": "" }
      ]
    },
    {
      "kicker": "Trade",
      "title": "External, Leading & Fiscal",
      "metrics": [
        { "label": "Trade Balance", "value": "-74.5B", "detail": "+1.4 B vs prior", "date_label": "Placeholder" },
        { "label": "WTI Oil", "value": "$68.19", "detail": "-0.55 USD vs prior", "date_label": "Placeholder" },
        { "label": "Gold", "value": "$2,335.40", "detail": "+8.20 USD vs prior", "date_label": "Placeholder" },
        { "label": "Copper", "value": "$9,835.07", "detail": "MoM 1.9%", "date_label": "Placeholder" },
        { "label": "Leading Index", "value": "99.4", "detail": "-0.2 idx vs prior", "date_label": "Placeholder" },
        { "label": "Housing Starts", "value": "1,246k", "detail": "MoM -0.6%", "date_label": "Placeholder" },
        { "label": "Building Permits", "value": "1,470k", "detail": "MoM 0.8%", "date_label": "Placeholder" },
        { "label": "Consumer Sentiment", "value": "76.3", "detail": "+1.1 pts vs prior", "date_label": "Placeholder" },
        { "label": "Budget Balance", "value": "-6.10%", "detail": "Federal surplus/deficit as % of GDP", "date_label": "Placeholder" },
        { "label": "Debt to GDP", "value": "121.30%", "detail": "+1.0 pp vs prior", "date_label": "Placeholder" }
      ]
    }
  ],
  "charts": [
    {
      "title": "10Y minus 2Y spread",
      "kicker": "Leading Indicator",
      "color": "#2858d7",
      "fill": "rgba(40, 88, 215, 0.12)",
      "series": [
        { "date": "2025-09-01", "value": -45 },
        { "date": "2025-10-01", "value": -37 },
        { "date": "2025-11-01", "value": -31 },
        { "date": "2025-12-01", "value": -28 },
        { "date": "2026-01-01", "value": -22 },
        { "date": "2026-02-01", "value": -17 },
        { "date": "2026-03-01", "value": -11 },
        { "date": "2026-04-01", "value": -30 }
      ]
    },
    {
      "title": "CPI YoY",
      "kicker": "Inflation",
      "color": "#bc7a22",
      "fill": "rgba(188, 122, 34, 0.12)",
      "series": [
        { "date": "2025-09-01", "value": 3.4 },
        { "date": "2025-10-01", "value": 3.3 },
        { "date": "2025-11-01", "value": 3.2 },
        { "date": "2025-12-01", "value": 3.1 },
        { "date": "2026-01-01", "value": 3.1 },
        { "date": "2026-02-01", "value": 3.2 },
        { "date": "2026-03-01", "value": 3.2 },
        { "date": "2026-04-01", "value": 3.2 }
      ]
    },
    {
      "title": "Payrolls change",
      "kicker": "Labor",
      "color": "#0f766e",
      "fill": "rgba(15, 118, 110, 0.12)",
      "series": [
        { "date": "2025-09-01", "value": 165 },
        { "date": "2025-10-01", "value": 201 },
        { "date": "2025-11-01", "value": 190 },
        { "date": "2025-12-01", "value": 178 },
        { "date": "2026-01-01", "value": 175 },
        { "date": "2026-02-01", "value": 210 },
        { "date": "2026-03-01", "value": 188 },
        { "date": "2026-04-01", "value": 194 }
      ]
    }
  ],
  "yahoo_finance_top_articles": [
    {
      "title": "Morning headlines will appear here after the first live refresh",
      "url": "https://finance.yahoo.com/",
      "summary": "This placeholder lets the hosted dashboard load immediately."
    },
    {
      "title": "The scheduled refresh rewrites this file before you open the site",
      "url": "https://finance.yahoo.com/",
      "summary": "GitHub Actions can keep this file fresh every morning."
    },
    {
      "title": "If Yahoo Finance rate-limits the refresh, the last successful file remains visible",
      "url": "https://finance.yahoo.com/",
      "summary": "That keeps the site stable even when the news source is temporarily noisy."
    }
  ],
  "coverage_notes": [
    "Most economic series come from FRED, which republishes official releases from BEA, BLS, the Fed, Census, EIA, IMF, and the Chicago Fed.",
    "PMI, Shiller CAPE, and Treasury supply outlook are not included as live fields here because their best-known feeds are proprietary, paywalled, or less reliable for unattended free refreshes.",
    "The leading indicator shown here uses the OECD composite leading indicator as a free proxy rather than the Conference Board LEI.",
    "Yahoo Finance headlines are collected from the live page each refresh and can occasionally rate-limit; when that happens, the last successful data file remains usable."
  ]
};
