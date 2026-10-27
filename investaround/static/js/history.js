// "What if?" page: shows the mix field only for "Your own mix", the rate
// field only for a fixed cash rate, and draws the growth chart from the JSON
// the server put in #history-chart-data.
(function () {
  "use strict";

  const cash = document.getElementById("cash");
  const cashRate = document.getElementById("cash-rate-wrap");
  if (cash && cashRate) {
    // Only a fixed rate needs (or sends) the rate box.
    const syncCash = function () {
      cashRate.hidden = cash.value !== "fixed";
      document.getElementById("cash_rate").disabled = cashRate.hidden;
    };
    cash.addEventListener("change", function () {
      syncCash();
      if (cash.value === "fixed") document.getElementById("cash_rate").focus();
    });
    syncCash();
  }

  const what = document.getElementById("what");
  const symbolsField = document.getElementById("symbols-field");
  if (what && symbolsField) {
    const sync = function () { symbolsField.hidden = what.value !== "custom"; };
    what.addEventListener("change", function () {
      sync();
      if (what.value === "custom") document.getElementById("symbols").focus();
    });
    sync();
  }

  const dataEl = document.getElementById("history-chart-data");
  const canvas = document.getElementById("history-chart");
  if (!dataEl || !canvas) return;
  const d = JSON.parse(dataEl.textContent);

  const css = getComputedStyle(document.documentElement);
  const accent = css.getPropertyValue("--accent").trim() || "#2f6fde";
  const money = new Intl.NumberFormat("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0});
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const longDate = function (iso) {
    const [y, m, day] = iso.split("-");
    return months[+m - 1] + " " + (+day) + ", " + y;
  };
  // Axis labels: years for long ranges, months for short ones.
  const tick = function (iso) {
    const [y, m] = iso.split("-");
    return d.years > 3 ? y : months[+m - 1] + " " + y;
  };

  // One tick where each year (or month) begins, thinned to at most about 12.
  const tickIndices = (function () {
    const starts = [];
    d.dates.forEach(function (iso, i) {
      if (i === 0 || tick(iso) !== tick(d.dates[i - 1])) starts.push(i);
    });
    // The partial first year (or month) gets no tick when it is too short for its label.
    if (starts.length > 2 && (starts[1] - starts[0]) * 2 < (starts[starts.length - 1] - starts[1]) / (starts.length - 2)) {
      starts.shift();
    }
    const step = Math.ceil(starts.length / 12);
    return starts.filter((_, k) => k % step === 0);
  })();

  const datasets = [
    {label: d.label, data: d.values, borderColor: accent, backgroundColor: accent,
     borderWidth: 2, pointRadius: 0, tension: .1},
  ];
  if (d.benchmark) {
    datasets.push({label: d.benchmarkLabel, data: d.benchmark, borderColor: "#9aa3b5", backgroundColor: "#9aa3b5",
                   borderWidth: 1.5, borderDash: [5, 4], pointRadius: 0, tension: .1});
  }

  new Chart(canvas, {
    type: "line",
    data: {labels: d.dates, datasets: datasets},
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: {mode: "index", intersect: false},
      plugins: {
        legend: {display: false},
        tooltip: {callbacks: {
          title: (items) => longDate(items[0].label),
          label: (ctx) => ctx.dataset.label + ": " + money.format(ctx.parsed.y),
        }},
      },
      scales: {
        x: {ticks: {autoSkip: false, maxRotation: 0,
                    callback: function (v) { return tick(this.getLabelForValue(v)); }},
            afterBuildTicks: function (axis) { axis.ticks = tickIndices.map((i) => ({value: i})); },
            grid: {display: false}},
        y: {ticks: {maxTicksLimit: 6, callback: (v) => money.format(v)}, grid: {color: "#eef0f5"}},
      },
    },
  });
})();
