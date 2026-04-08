const dashboardData = window.MACRO_DASHBOARD_DATA || null;

const elements = {
  lastUpdated: document.querySelector("#last-updated"),
  sourceCount: document.querySelector("#source-count"),
  curve2s10s: document.querySelector("#curve-2s10s"),
  curve3m10y: document.querySelector("#curve-3m10y"),
  curveRegime: document.querySelector("#curve-regime"),
  yieldCurveChart: document.querySelector("#yield-curve-chart"),
  yieldCurvePoints: document.querySelector("#yield-curve-points"),
  newsList: document.querySelector("#news-list"),
  chartsGrid: document.querySelector("#charts-grid"),
  sectionsGrid: document.querySelector("#sections-grid"),
  coverageNotes: document.querySelector("#coverage-notes"),
  sectionTemplate: document.querySelector("#section-template"),
  metricTemplate: document.querySelector("#metric-template"),
  chartTemplate: document.querySelector("#chart-template"),
  newsTemplate: document.querySelector("#news-template"),
};

renderDashboard();

function renderDashboard() {
  if (!dashboardData) {
    renderEmptyState("No dashboard data yet. Run the updater or the scheduled workflow to populate this site.");
    return;
  }

  elements.lastUpdated.textContent = formatTimestamp(dashboardData.updated_at);
  elements.sourceCount.textContent = (dashboardData.sources || []).join(" + ") || "Macro sources";
  renderYieldCurve(dashboardData.yield_curve || {});
  renderSections(dashboardData.sections || []);
  renderCharts(dashboardData.charts || []);
  renderNews(dashboardData.yahoo_finance_top_articles || []);
  renderCoverageNotes(dashboardData.coverage_notes || []);
}

function renderYieldCurve(yieldCurve) {
  const points = Array.isArray(yieldCurve.points) ? yieldCurve.points : [];
  elements.curve2s10s.textContent = formatBasisPoints(yieldCurve.spread_2s10s_bp);
  elements.curve3m10y.textContent = formatBasisPoints(yieldCurve.spread_3m10y_bp);
  elements.curveRegime.textContent = yieldCurve.regime || "--";
  elements.yieldCurvePoints.innerHTML = "";

  points.forEach((point) => {
    const node = document.createElement("div");
    node.className = `curve-point${point.value == null ? " is-missing" : ""}`;
    node.innerHTML = `<span>${escapeHtml(point.label)}</span><strong>${escapeHtml(point.value_label)}</strong>`;
    elements.yieldCurvePoints.appendChild(node);
  });

  renderLineChart(elements.yieldCurveChart, points.filter((point) => Number.isFinite(point.value)), {
    xAccessor: (point) => point.label,
    yAccessor: (point) => point.value,
    stroke: "#0f766e",
    fill: "rgba(15, 118, 110, 0.14)",
    labelFormatter: (label) => label,
  });
}

function renderSections(sections) {
  elements.sectionsGrid.innerHTML = "";

  sections.forEach((section) => {
    const node = elements.sectionTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".section-label").textContent = section.kicker || section.title;
    node.querySelector("h2").textContent = section.title;
    const metricGrid = node.querySelector(".metric-grid");

    (section.metrics || []).forEach((metric) => {
      const card = elements.metricTemplate.content.firstElementChild.cloneNode(true);
      const missing = !metric.value || metric.value === "N/A";
      card.classList.toggle("is-missing", missing);
      card.querySelector(".metric-label").textContent = metric.label;
      card.querySelector(".metric-value").textContent = metric.value || "N/A";
      card.querySelector(".metric-detail").textContent = metric.detail || " ";
      card.querySelector(".metric-date").textContent = metric.date_label ? `As of ${metric.date_label}` : missing ? "Source unavailable in latest refresh" : " ";
      metricGrid.appendChild(card);
    });

    elements.sectionsGrid.appendChild(node);
  });
}

function renderCharts(charts) {
  elements.chartsGrid.innerHTML = "";

  charts.forEach((chart) => {
    const node = elements.chartTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".chart-kicker").textContent = chart.kicker || "Trend";
    node.querySelector(".chart-title").textContent = chart.title;
    renderLineChart(node.querySelector(".chart"), chart.series || [], {
      xAccessor: (point) => point.date,
      yAccessor: (point) => point.value,
      stroke: chart.color || "#2858d7",
      fill: chart.fill || "rgba(40, 88, 215, 0.12)",
      labelFormatter: formatDateLabel,
    });
    elements.chartsGrid.appendChild(node);
  });
}

function renderNews(articles) {
  elements.newsList.innerHTML = "";

  if (!articles.length) {
    elements.newsList.innerHTML = `<div class="empty-message">No Yahoo Finance articles were available in the latest refresh.</div>`;
    return;
  }

  articles.slice(0, 3).forEach((article, index) => {
    const item = elements.newsTemplate.content.firstElementChild.cloneNode(true);
    item.href = article.url;
    item.querySelector(".news-rank").textContent = String(index + 1);
    item.querySelector(".news-title").textContent = article.title;
    item.querySelector(".news-summary").textContent = article.summary || article.url;
    elements.newsList.appendChild(item);
  });
}

function renderCoverageNotes(notes) {
  elements.coverageNotes.innerHTML = "";
  notes.forEach((note) => {
    const div = document.createElement("div");
    const warning = /inactive|unavailable|rate-limit|failed|not configured/i.test(note);
    div.className = `coverage-note${warning ? " is-warning" : ""}`;
    div.textContent = note;
    elements.coverageNotes.appendChild(div);
  });
}

function renderLineChart(container, series, options) {
  container.innerHTML = "";

  if (!series.length) {
    container.innerHTML = `<div class="empty-message">No chart data available.</div>`;
    return;
  }

  const width = 760;
  const height = 250;
  const padding = { top: 18, right: 16, bottom: 28, left: 40 };
  const values = series.map(options.yAccessor).filter((value) => Number.isFinite(value));

  if (!values.length) {
    container.innerHTML = `<div class="empty-message">No chart data available.</div>`;
    return;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const xAt = (index) => {
    if (series.length === 1) return width / 2;
    return padding.left + (index / (series.length - 1)) * (width - padding.left - padding.right);
  };

  const yAt = (value) => height - padding.bottom - ((value - min) / range) * (height - padding.top - padding.bottom);
  const points = series.map((point, index) => ({
    x: xAt(index),
    y: yAt(options.yAccessor(point)),
    label: options.xAccessor(point),
    value: options.yAccessor(point),
  }));

  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
  const areaPath = `${path} L ${points[points.length - 1].x.toFixed(2)} ${height - padding.bottom} L ${points[0].x.toFixed(2)} ${height - padding.bottom} Z`;
  const zeroY = min <= 0 && max >= 0 ? yAt(0) : null;
  const gradientId = `gradient-${Math.random().toString(36).slice(2, 9)}`;

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" aria-hidden="true">
      <defs>
        <linearGradient id="${gradientId}" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="${options.fill}" />
          <stop offset="100%" stop-color="rgba(255,255,255,0)" />
        </linearGradient>
      </defs>
      ${buildGridLines(min, max, yAt, width, padding)}
      ${zeroY == null ? "" : `<line x1="${padding.left}" y1="${zeroY}" x2="${width - padding.right}" y2="${zeroY}" stroke="rgba(21,30,37,0.16)" stroke-dasharray="4 6"></line>`}
      <path d="${areaPath}" fill="url(#${gradientId})"></path>
      <path d="${path}" fill="none" stroke="${options.stroke}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
      ${points.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="4.25" fill="${options.stroke}"></circle>`).join("")}
      ${buildAxisLabels(points, height, options.labelFormatter)}
    </svg>
  `;
}

function buildGridLines(min, max, yAt, width, padding) {
  const lines = [];
  const steps = 4;

  for (let index = 0; index <= steps; index += 1) {
    const value = min + ((max - min) / steps) * index;
    const y = yAt(value);
    lines.push(`<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(21,30,37,0.08)"></line>`);
    lines.push(`<text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="rgba(98,112,119,0.95)">${value.toFixed(1)}</text>`);
  }

  return lines.join("");
}

function buildAxisLabels(points, height, formatter) {
  const indexes = [0, Math.floor((points.length - 1) / 2), points.length - 1].filter((value, index, array) => array.indexOf(value) === index);

  return indexes.map((index) => {
    const point = points[index];
    return `<text x="${point.x}" y="${height - 8}" text-anchor="middle" font-size="11" fill="rgba(98,112,119,0.95)">${escapeHtml(formatter(point.label))}</text>`;
  }).join("");
}

function renderEmptyState(message) {
  elements.sectionsGrid.innerHTML = `<div class="panel"><div class="empty-message">${escapeHtml(message)}</div></div>`;
  elements.chartsGrid.innerHTML = "";
  elements.yieldCurveChart.innerHTML = `<div class="empty-message">${escapeHtml(message)}</div>`;
  elements.newsList.innerHTML = `<div class="empty-message">${escapeHtml(message)}</div>`;
}

function formatTimestamp(value) {
  return value ? new Date(value).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }) : "Unknown";
}

function formatBasisPoints(value) {
  return value == null ? "--" : `${value.toFixed(1)} bp`;
}

function formatDateLabel(label) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(label)) {
    return label;
  }

  return new Date(`${label}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    year: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
