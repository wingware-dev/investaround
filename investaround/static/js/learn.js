// Learn pages: the glossary filter (/learn/) and the strategy lab chart (/learn/lab).
(function () {
  "use strict";

  // Glossary: hide terms whose name or meaning doesn't contain the typed text.
  const filter = document.getElementById("glossary-filter");
  if (filter) {
    const terms = [...document.querySelectorAll(".glossary dt[data-term]")];
    const none = document.getElementById("glossary-none");
    filter.addEventListener("input", function () {
      const q = filter.value.trim().toLowerCase();
      let shown = 0;
      terms.forEach(function (dt) {
        const dd = dt.nextElementSibling;
        const match = !q || (dt.textContent + " " + dd.textContent).toLowerCase().includes(q);
        dt.hidden = dd.hidden = !match;
        if (match) shown++;
      });
      none.hidden = shown > 0;
    });
  }

  // Strategy lab: one line per strategy, plus the money the spread-out one has put in so far.
  const dataEl = document.getElementById("lab-chart-data");
  const canvas = document.getElementById("lab-chart");
  if (dataEl && canvas) {
    const d = JSON.parse(dataEl.textContent);
    const money = new Intl.NumberFormat("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0});
    const color = (key) => d.colors[key.startsWith("rebalance") ? "rebalance" : key];
    const datasets = d.series.map((s) => ({
      label: s.label, data: s.values, borderColor: color(s.key), backgroundColor: color(s.key),
      borderWidth: 2, pointRadius: 0, tension: .15,
    }));
    datasets.push({
      label: "Money invested so far (spread out)", data: d.invested, borderColor: "#9aa3b5",
      borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, stepped: true,
    });
    new Chart(canvas, {
      type: "line",
      data: {labels: d.months, datasets: datasets},
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        interaction: {mode: "index", intersect: false},
        plugins: {
          legend: {display: false},
          tooltip: {callbacks: {label: (ctx) => ctx.dataset.label + ": " + money.format(ctx.parsed.y)}},
        },
        scales: {
          x: {ticks: {maxTicksLimit: 8, maxRotation: 0}, grid: {display: false}},
          y: {ticks: {maxTicksLimit: 6, callback: (v) => money.format(v)}, grid: {color: "#eef0f5"}},
        },
      },
    });
  }
})();
