// Portfolio builder (form#builder) and watch page (#watch).
(function () {
  "use strict";

  function money(x) {
    return x.toLocaleString("en-US", { style: "currency", currency: "USD" });
  }

  // ------------------------------------------------------------ builder

  function initBuilder(form) {
    const startCash = parseFloat(form.dataset.startCash);
    const maxHoldings = parseInt(form.dataset.max, 10);
    const suggestedMin = parseInt(form.dataset.suggestedMin, 10);
    const searchUrl = form.dataset.searchUrl;
    const body = document.getElementById("holdings");
    const emptyRow = body.querySelector("tr.empty");
    const template = document.getElementById("holding-row-template");
    const search = document.getElementById("search");
    const results = document.getElementById("search-results");
    const countEl = document.getElementById("holding-count");
    const totalEl = document.getElementById("weight-total");
    const hintEl = document.getElementById("spread-hint");
    // Until the user types a weight, adding or removing an investment
    // re-splits the money evenly.
    let weightsTouched = body.querySelectorAll("tr.holding-row").length > 0;

    const rows = () => Array.from(body.querySelectorAll("tr.holding-row"));
    const symbols = () => rows().map((r) => r.dataset.symbol);
    const weightOf = (r) => parseFloat(r.querySelector("input.weight").value) || 0;

    function update() {
      const all = rows();
      const n = all.length;
      const total = all.reduce((sum, r) => sum + weightOf(r), 0);
      emptyRow.hidden = n > 0;
      all.forEach((r) => {
        r.querySelector(".holding-amount").textContent = money(startCash * weightOf(r) / 100);
      });
      countEl.textContent = `${n} investment${n === 1 ? "" : "s"}`;
      const ok = n === 0 || Math.abs(total - 100) <= 0.01;
      totalEl.className = ok ? "ok" : "bad";
      totalEl.textContent = n ? `· weights add up to ${+total.toFixed(2)}%` +
        (ok ? "" : ` (they need to add up to 100%)`) : "";
      if (n === 0) {
        hintEl.textContent = `Aim for ${suggestedMin} to ${maxHoldings} investments.`;
      } else if (n < suggestedMin) {
        hintEl.textContent = `Tip: with only ${n}, one bad day for a single pick moves the whole portfolio. ` +
          `Most people use ${suggestedMin} to ${maxHoldings}.`;
      } else if (n >= maxHoldings) {
        hintEl.textContent = `That's the most this app allows (${maxHoldings}).`;
      } else {
        hintEl.textContent = `${n} investments is a good spread.`;
      }
      search.disabled = n >= maxHoldings;
    }

    function splitEvenly() {
      const all = rows();
      if (!all.length) return;
      const base = Math.floor(10000 / all.length) / 100;
      const first = +(100 - base * (all.length - 1)).toFixed(2);
      all.forEach((r, i) => { r.querySelector("input.weight").value = i === 0 ? first : base; });
    }

    function addHolding(symbol, name) {
      if (symbols().includes(symbol)) {
        hintEl.textContent = `${symbol} is already in the portfolio.`;
        return;
      }
      if (rows().length >= maxHoldings) return;
      const row = template.content.firstElementChild.cloneNode(true);
      row.dataset.symbol = symbol;
      row.querySelector(".holding-symbol").textContent = symbol;
      row.querySelector('input[name="symbol"]').value = symbol;
      row.querySelector('input[name="holding_name"]').value = name;
      row.querySelector(".holding-name").textContent = name;
      row.querySelector("input.weight").setAttribute("aria-label", `Weight for ${symbol} (%)`);
      row.querySelector("button.remove").setAttribute("aria-label", `Remove ${symbol}`);
      body.insertBefore(row, emptyRow);
      if (weightsTouched) {
        const used = rows().reduce((sum, r) => sum + weightOf(r), 0);
        row.querySelector("input.weight").value = Math.max(0, +(100 - used).toFixed(2));
      } else {
        splitEvenly();
      }
      update();
    }

    body.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button.remove");
      if (!btn) return;
      btn.closest("tr").remove();
      if (!weightsTouched) splitEvenly();
      update();
    });
    body.addEventListener("input", (ev) => {
      if (ev.target.matches("input.weight")) {
        weightsTouched = true;
        update();
      }
    });
    document.getElementById("split-evenly").addEventListener("click", () => {
      splitEvenly();
      update();
    });

    // Search: debounced, newest answer wins.
    let timer = null;
    let seq = 0;

    function closeResults() {
      results.hidden = true;
      results.replaceChildren();
    }

    function showMessage(text) {
      const li = document.createElement("li");
      li.className = "message";
      li.textContent = text;
      results.replaceChildren(li);
      results.hidden = false;
    }

    async function runSearch(q) {
      const mine = ++seq;
      let data;
      try {
        const resp = await fetch(`${searchUrl}?q=${encodeURIComponent(q)}`);
        data = await resp.json();
      } catch (err) {
        if (mine === seq) showMessage("Search isn't working right now. Try again in a moment.");
        return;
      }
      if (mine !== seq) return;
      if (data.error) return showMessage(data.error);
      if (!data.results.length) return showMessage(`Nothing found for “${q}”.`);
      results.replaceChildren(...data.results.map((hit) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("role", "option");
        btn.dataset.symbol = hit.symbol;
        for (const [cls, text] of [["sym", hit.symbol], ["nm", hit.name], ["kind muted", hit.type]]) {
          const span = document.createElement("span");
          span.className = cls;
          span.textContent = text || "";
          btn.appendChild(span);
        }
        btn.addEventListener("click", () => {
          addHolding(hit.symbol, hit.name);
          search.value = "";
          closeResults();
          search.focus();
        });
        li.appendChild(btn);
        return li;
      }));
      results.hidden = false;
    }

    search.addEventListener("input", () => {
      clearTimeout(timer);
      const q = search.value.trim();
      if (q.length < 2) {
        seq++;
        closeResults();
        return;
      }
      timer = setTimeout(() => runSearch(q), 200);
    });
    search.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        // Enter picks the top match rather than submitting the form.
        ev.preventDefault();
        const top = results.querySelector("button[data-symbol]");
        if (top) top.click();
      } else if (ev.key === "Escape") {
        closeResults();
      } else if (ev.key === "ArrowDown") {
        const top = results.querySelector("button");
        if (top) { ev.preventDefault(); top.focus(); }
      }
    });
    results.addEventListener("keydown", (ev) => {
      const li = ev.target.closest("li");
      if (!li) return;
      const next = ev.key === "ArrowDown" ? li.nextElementSibling : ev.key === "ArrowUp" ? li.previousElementSibling : null;
      if (next) { ev.preventDefault(); next.querySelector("button").focus(); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); search.focus(); }
      else if (ev.key === "Escape") { closeResults(); search.focus(); }
    });
    document.addEventListener("click", (ev) => {
      if (!ev.target.closest(".search-box")) closeResults();
    });

    update();
  }

  // ------------------------------------------------------------ watch page

  const REFRESH_EVERY_MS = 5 * 60 * 1000;

  function initWatch(root) {
    const url = root.dataset.tableUrl;
    const button = document.getElementById("refresh");
    const checkedEl = document.getElementById("checked-at");
    const asOfEl = document.getElementById("prices-as-of");

    function showTimes() {
      const live = document.getElementById("watch-live");
      const checked = new Date(live.dataset.checkedAt);
      checkedEl.dateTime = live.dataset.checkedAt;
      checkedEl.textContent = checked.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
      if (live.dataset.pricesAsOf) {
        const asOf = new Date(live.dataset.pricesAsOf);
        const sameDay = asOf.toDateString() === checked.toDateString();
        asOfEl.textContent = "· prices from " + (sameDay
          ? asOf.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
          : asOf.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }));
      } else {
        asOfEl.textContent = "";
      }
    }

    async function refresh() {
      button.disabled = true;
      button.textContent = "Refreshing…";
      try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        document.getElementById("watch-live").outerHTML = await resp.text();
        showTimes();
      } catch (err) {
        asOfEl.textContent = `· couldn't refresh (${err.message}); showing earlier prices`;
      } finally {
        button.disabled = false;
        button.textContent = "Refresh prices";
      }
    }

    button.addEventListener("click", refresh);
    setInterval(() => { if (!document.hidden) refresh(); }, REFRESH_EVERY_MS);
    showTimes();
  }

  const builder = document.getElementById("builder");
  if (builder) initBuilder(builder);
  const watch = document.getElementById("watch");
  if (watch) initWatch(watch);
})();
