# Run trail

Generated 2026-10-28 12:21 from Wing's task store, the Tasks Manager's log, the agents' transcripts and the repository.  Times are local (-04:00).

Before publishing, the price data the agents recorded from Yahoo Finance for the tests was replaced with made-up sample prices and removed from the history, so this repository ships no market data.  The commits linked below therefore have no price data, their tests use the sample prices, and their screenshots are the final ones.

## Totals

| | Time | Input | Output | Cache read | Cache write |
|---|---|---|---|---|---|
| Workers (19 tasks) | 1h 14m task time | 35k | 422k | 39.28M | 1.07M |
| Tasks Manager (its sessions over the run) |  | 526 | 44k | 24.89M | 163k |
| **Total** | 54m 02s elapsed | 36k | 466k | 64.16M | 1.24M |

- Questions from workers: 0 (answered by the user 0, by the Tasks Manager 0, unanswered 0)
- Questions the Tasks Manager passed to the user, Wing's included: 1
- Questions from the Tasks Manager to the user: 0
- Judgement calls: 75
- Findings filed: 0
- Commits: 17
- Tasks Manager decisions: 56

## Timeline

| Time | Event |
|---|---|
| 2026-10-27 15:19 | Committed 2a570968be33: Initial commit |
| 2026-10-27 15:20 | T1 new-investing-want-software started |
| 2026-10-27 15:23 | The Tasks Manager passed T1 new-investing-want-software's question to the user |
| 2026-10-27 15:24 | T2 app-foundation started |
| 2026-10-27 15:30 | T2 app-foundation finished: done |
| 2026-10-27 15:31 | Committed d10a3b63de43 for T2 app-foundation: Add paper-investing app foundation: models, storage, price sources, app skeleton |
| 2026-10-27 15:31 | T4 yahoo-price-source started |
| 2026-10-27 15:31 | T3 ui-harness-and-shots started |
| 2026-10-27 15:31 | T5 analytics-engine started |
| 2026-10-27 15:34 | T3 ui-harness-and-shots finished: done |
| 2026-10-27 15:34 | Committed 39b2c2f36233 for T3 ui-harness-and-shots: Add UI test harness, screenshot tool and smoke UI tests |
| 2026-10-27 15:34 | T8 example-portfolios started |
| 2026-10-27 15:37 | T4 yahoo-price-source finished: done |
| 2026-10-27 15:37 | Committed 465a4ce3d39f for T4 yahoo-price-source: Add Yahoo price source and SQLite price cache; use Yahoo by default |
| 2026-10-27 15:37 | T6 portfolio-builder-watch started |
| 2026-10-27 15:38 | T5 analytics-engine finished: done |
| 2026-10-27 15:38 | Committed 573816e5f614 for T5 analytics-engine: Add pure analytics engine: value series, performance metrics and strategies |
| 2026-10-27 15:38 | T7 history-backtest-page started |
| 2026-10-27 15:38 | T9 learn-strategy-lab started |
| 2026-10-27 15:39 | T8 example-portfolios finished: done |
| 2026-10-27 15:39 | Committed 2d5891525b5e for T8 example-portfolios: Add example portfolios gallery |
| 2026-10-27 15:40 | T13 richer-example-fixtures started |
| 2026-10-27 15:42 | T13 richer-example-fixtures finished: done |
| 2026-10-27 15:42 | Committed c082bed9c661 for T13 richer-example-fixtures: Record more price fixtures and complete the example portfolios |
| 2026-10-27 15:43 | T12 interest-on-uninvested-cash started |
| 2026-10-27 15:44 | T9 learn-strategy-lab finished: done |
| 2026-10-27 15:44 | Committed d94be11d7548 for T9 learn-strategy-lab: Add Learn page and Strategy lab |
| 2026-10-27 15:44 | T14 examples-in-strategy-lab started |
| 2026-10-27 15:45 | T6 portfolio-builder-watch finished: done |
| 2026-10-27 15:45 | Committed 404acfb9a4ae for T6 portfolio-builder-watch: Add portfolio builder and daily watch page |
| 2026-10-27 15:45 | T7 history-backtest-page finished: done |
| 2026-10-27 15:45 | Committed 87a7e0dfdbd7 for T7 history-backtest-page: Add "What if?" history backtest page |
| 2026-10-27 15:46 | T14 examples-in-strategy-lab finished: done |
| 2026-10-27 15:46 | Committed 041823065e47 for T14 examples-in-strategy-lab: Offer the example portfolios in the strategy lab |
| 2026-10-27 15:46 | T12 interest-on-uninvested-cash finished: done |
| 2026-10-27 15:46 | Committed 2a0194fc572f for T12 interest-on-uninvested-cash: Let uninvested cash earn interest in the analytics engine |
| 2026-10-27 15:46 | T10 home-dashboard-docs started |
| 2026-10-27 15:46 | T20 irx-tbill-fixture started |
| 2026-10-27 15:48 | T20 irx-tbill-fixture finished: done |
| 2026-10-27 15:48 | Committed 2f1ae55126c1 for T20 irx-tbill-fixture: Record ^IRX T-bill yield fixture and test cash interest on real yields |
| 2026-10-27 15:52 | T1 new-investing-want-software finished: done |
| 2026-10-27 15:52 | T10 home-dashboard-docs finished: done |
| 2026-10-27 15:52 | Committed 2cc5ced41921 for T10 home-dashboard-docs: Add home dashboard, price-source status banner and README |
| 2026-10-27 15:53 | T19 cash-rate-option-in-pages started |
| 2026-10-27 15:58 | T15 store-purchase-prices started |
| 2026-10-27 16:00 | T19 cash-rate-option-in-pages finished: done |
| 2026-10-27 16:00 | Committed 347320221c6d for T19 cash-rate-option-in-pages: Offer a "Waiting cash earns" option on the history page and strategy lab |
| 2026-10-27 16:01 | T15 store-purchase-prices finished: done |
| 2026-10-27 16:01 | Committed 08f02824bfc7 for T15 store-purchase-prices: Record each holding's purchase price and date |
| 2026-10-27 16:01 | T18 regression-tests-paper-app started |
| 2026-10-27 16:02 | T18 regression-tests-paper-app finished: done |
| 2026-10-27 16:11 | T22 run-set-main-entry finished: done |
| 2026-10-27 16:12 | T23 running-wing-doesn-work started |
| 2026-10-27 16:13 | T23 running-wing-doesn-work finished: done |
| 2026-10-27 16:13 | Committed 5a0f7b5cb767 for T23 running-wing-doesn-work: Add run_investaround.py launcher so Wing can run the app |

## Tasks

### T1 new-investing-want-software

- **Origin:** Written by the user
- **Goal:** Ungrouped Tasks
- **Ran:** 2026-10-27 15:20 to 2026-10-27 15:52 (2m 44s)
- **Outcome:** done
- **Usage:** 14k input, 15k output, 371k cache read, 54k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> I'm new to investing and want some software so I can try it out by just picking
> investments without actually buying them and watching them over time, both in
> current values day to day and by setting the date range to see how they would
> have done in the past. I would pick around 5-20 investments, and would be useful
> to have some way of seeing examples to work from. I'm hoping to do this with
> real investments and prices from somewhere free where I don't need an account.
> Anything else that would help a new investor to try and understand common
> strategies would also be great.
>
> Commit a screenshot of each major visible change under docs/shots/ since we'll
> be creating a publishable trace of this run later.
>
> [Tasks Manager, 2026-10-27 15:20] Manager: the project is empty apart from .venv and an empty requirements.txt, so plan this before building it. Pick a free price source that needs no account or API key, and check it really works for both daily current prices and historical ranges. Plan the app's form (for example a local web or desktop app) and how its pieces fit. Order the steps so they can run side by side where possible: shared data/model contracts come first, then features in their own files. Each step should say which files it owns and which it shares. Include early a harness that drives the UI as a user would (invariant 12) and that also captures the docs/shots/ screenshots the task asks for. Tests must use stand-ins for the network, not live calls.
>
> See <project>/.TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md

**Passed to the user by the Tasks Manager**

- 2026-10-27 15:23, question : Suggested: accept. The plan builds a local web app that runs in your browser and has 9 steps, several of which run side by side. Two choices are worth checking before you accept. (1) Prices come from Yahoo Finance's public chart and search endpoints. These need no account, but they are unofficial, so the app caches results and keeps the source swappable. Other free sources either needed a key or blocked scripted access. (2) Step 1 makes one live download of real price history for about 15 symbols, to use as test data; tests never go to the network after that. Once you accept, I'll file the steps as tasks and run them, committing each one.

**Judgement calls**

1. **Price source: Yahoo Finance's public chart and search endpoints, no key or account**
   Checked live on 2026-10-27 with plain GET requests and an honest app User-Agent ("investaround/0.1"). Current quote, previous close and 26 years of daily SPY history (6,743 bars, adjusted close, 108 dividends) all came back in one call each. Stocks, ETFs (VOO), mutual funds (VTSAX) and crypto (BTC-USD) all worked, and search works too. Risks: the endpoint is unofficial with no SLA, it is meant for personal use, and it can rate-limit. The app caches everything in SQLite, fetches each symbol at most once per refresh, sends an honest UA, and shows a clear 'data unavailable' message when a fetch fails.
   Alternatives: Stooq CSV: now sits behind a JavaScript proof-of-work bot check, so it is unusable; Twelve Data / Alpha Vantage / FMP / Tiingo: reliable, but each needs a free account and API key, which the user ruled out; FRED fredgraph.csv: keyless but only has indexes, no individual stocks or funds, and it timed out from here; Nasdaq's api.nasdaq.com: only works when imitating a browser, so I didn't pursue it
2. **Form: local Flask web app in the browser, with Chart.js vendored**
   Charts and date pickers come for free, Playwright can drive it headless for invariant 12 and the screenshots, and it needs no desktop GUI toolkit on Python 3.14.
   Alternatives: Streamlit: quicker to start but harder to drive and test precisely; Desktop app with Qt: heavier, and screenshot automation is more fiddly
3. **Tests and screenshots use recorded real prices, frozen at a fixed 'today'**
   No network in tests, as the Manager asked. Screenshots still show real tickers and real history, and they are deterministic.
   Alternatives: Synthetic prices: unrealistic screenshots; Live screenshots: they change from run to run and depend on the network
4. **Feature stubs and the nav are created in step 1, so feature steps never edit shared files**
   Lets steps 5-8 run side by side.
   Alternatives: Each feature registers itself in a shared list, which would serialize the steps
5. **Harness uses the installed Google Chrome (Playwright channel="chrome") and falls back to Playwright's own Chromium**
   Chrome is already installed, which avoids a ~150 MB browser download on this machine. Elsewhere it falls back to `playwright install chromium`.
   Alternatives: Always download Playwright Chromium

**Summary**

> Planned "investaround", a local Flask web app for practice investing with no real money. It covers paper portfolios of 5-20 holdings with daily values, past-performance tests over any date range, example portfolios, and a strategies lab, using Yahoo Finance's keyless chart and search endpoints, which I checked live.
> - 9 steps: contracts and app skeleton first, then a UI and screenshot harness, a price source, an analytics engine, and four feature pages in their own files, then integration.
> - Tests use a fake price source fed by recorded real prices, so no test touches the network.


### T2 app-foundation

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:24 to 2026-10-27 15:30 (6m 11s)
- **Outcome:** done; committed [`d10a3b63de43`](https://github.com/wingware-dev/investaround/commit/d10a3b63de43a3f22a6c20a23eaf929f914d0a4f)
- **Usage:** 82 input, 36k output, 2.31M cache read, 78k cache write (claude-opus-5-5)

**Prompt**

> Paper investing app step 1: foundation, contracts and app skeleton
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md (Design section).
>
> Creates the package layout with models, the PriceSource protocol, FakePriceSource, PortfolioStore and the Flask app factory. It also adds base.html with the full nav, CSS, vendored Chart.js, and stub blueprints and templates for every feature (home, portfolios, history, examples, learn), so later steps never touch shared files. Adds tools/record_fixtures.py and runs it once (live, developer-run, read-only GETs to Yahoo with the honest UA) to record tests/fixtures/prices for about 15 symbols: SPY, VOO, VTI, VXUS, BND, QQQ, VNQ, GLD, AAPL, MSFT, JNJ, KO, AMZN, NVDA, VTSAX. Also adds requirements.txt, data/ to .gitignore, and unit tests for models, storage and the fake source.
> Owns: investaround/{__init__,__main__,app,models,storage}.py, prices/{base,fake}.py, web/*.py stubs, templates/base.html + stubs, static/css, static/vendor, tools/record_fixtures.py, tests/fixtures, tests/unit/test_{models,storage,fake_source}.py. Shares: requirements.txt, .gitignore.
>
> Manager: put every dependency the plan names in requirements.txt now, dev ones included (flask, httpx, pytest, playwright), and install them in .venv. Steps 2-4 then run side by side and need not touch it. Leave app.py with a clear hook where step 3 plugs in the yahoo source. Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> See <project>/.TASKS/notes/paper-investing-app-step-1-foundation-contracts-and-app.md

**Judgement calls**

1. **Set the Wing project's test framework to pytest and excluded site-packages/ from test discovery** (report 1)
   The plan's tests and harness are pytest-based, and Wing's unittest runner couldn't import the package; the venv lives inside the project.
   Alternatives: Write unittest-style tests and keep the unittest framework
2. **Default price source stays 'fake' until step 3 switches DEFAULT_PRICE_SOURCE to 'yahoo'** (report 1)
   No Yahoo source exists yet. Choosing yahoo now would make the app fail to start.
   Alternatives: Default to yahoo and raise until step 3 lands
3. **Named the screenshot docs/shots/00-app-skeleton.png** (report 1)
   Step 2 owns docs/shots/01-*, so 00 avoids a collision while still leaving a trace of this step.
   Alternatives: Leave screenshots entirely to step 2
4. **Added pyproject.toml, prices/__init__.py, templates/error.html and tests/unit/test_app.py beyond the Owns list** (report 1)
   pytest needs the import path, the error pages need a template, and the app factory deserved its own tests. None of these files is claimed by another step.
   Alternatives: Put pytest config in a root conftest.py
5. **Chart.js is loaded on every page from base.html, and pages add their JS in a `scripts` block** (report 1)
   This keeps later steps from having to touch base.html. The file is about 200 KB and served locally.
   Alternatives: Each page includes Chart.js itself
6. **Server listens on port 8765 by default, not 5000** (report 1)
   macOS AirPlay Receiver often holds port 5000.
   Alternatives: 5000

**Screenshots**

![00-app-skeleton.png](https://github.com/wingware-dev/investaround/raw/d10a3b63de43a3f22a6c20a23eaf929f914d0a4f/docs/shots/00-app-skeleton.png)

**Summary**

> Paper-investing app foundation: package skeleton, contracts, recorded price fixtures and the stub UI for every feature.
> - `models.py` (Holding/Portfolio with 1-20 holdings validation and an under-5 warning, Quote, PriceBar, PriceSeries, SearchHit), `storage.py` (PortfolioStore: JSON with atomic writes), `prices/base.py` (PriceSource Protocol, PriceSourceError, UnknownSymbol), `prices/fake.py` (FakePriceSource over the fixtures, frozen today, search, injectable failures)
> - `app.py` factory with get_store()/get_prices(), 404 and price-error pages, and a `_make_yahoo` hook plus `DEFAULT_PRICE_SOURCE` for step 3; `python -m investaround` runs the server and opens a browser
> - base.html with full nav, footer disclaimer, shared CSS and vendored Chart.js 4.4.6; stub blueprints and templates for home, portfolios, history, examples and learn
> - tools/record_fixtures.py, run once live: tests/fixtures/prices holds 15 symbols, 2005 (or listing date) to 2026-10-27, plus quotes.json
> - requirements.txt (flask, httpx, pytest, playwright, installed in .venv), pyproject.toml (pytest config), `/data/` in .gitignore, 55 unit tests (models, storage, fake source, app) all passing, screenshot docs/shots/00-app-skeleton.png


### T4 yahoo-price-source

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:31 to 2026-10-27 15:37 (5m 51s)
- **Outcome:** done; committed [`465a4ce3d39f`](https://github.com/wingware-dev/investaround/commit/465a4ce3d39f6fd42191c5aea5431488515b0078)
- **Usage:** 2,181 input, 39k output, 2.45M cache read, 47k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Paper investing app step 3: Yahoo price source and cache
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md (Findings section has the endpoints). Runs after step 1 app-foundation, side by side with steps 2 and 4.
>
> Adds YahooPriceSource, which parses chart/search JSON, handles errors, 429s and missing data, and sends an honest UA. Adds CachingPriceSource (SQLite) and wires app.py to choose yahoo by default. Tests feed recorded JSON responses through an injected fake transport, with no live calls; they cover rate limits, an unknown symbol, gaps and holidays.
> Owns: prices/{yahoo,cache}.py, tests/unit/test_{yahoo,cache}.py, tests/fixtures/yahoo/*.json. Shares: app.py (source selection, a few lines).
>
> [Tasks Manager, 2026-10-27 15:30] Manager, from T2 app-foundation (9fa9251e): in investaround/app.py, implement `_make_yahoo(app)` to return CachingPriceSource(YahooPriceSource(...)) with the cache under app.config['DATA_DIR'], and set DEFAULT_PRICE_SOURCE = 'yahoo'. Nothing else in app.py needs to change. Note that T3 and T5 run beside you on other files.
>
> See <project>/.TASKS/notes/paper-investing-app-step-3-yahoo-price-source-and-cache.md

**Judgement calls**

1. **Recorded the Yahoo test fixtures live: 8 read-only GETs, plus 3 for a manual check through the app**
   The task asks for tests on recorded JSON responses, and only real replies show the actual shapes. Doing so turned up two behaviours a hand-made fixture would have got wrong: a range before a fund existed returns HTTP 400 'Data doesn't exist', not empty data, and a mutual fund's today row has a null close. The plan said step 1's recording would be the only live use; these calls were free, keyless, and used the same honest UA.
   Alternatives: Hand-write every fixture without touching the network
2. **Added tools/record_yahoo_fixtures.py, a file the task didn't list**
   So the recorded replies can be refreshed the same way step 1's prices can. No other step claims it.
   Alternatives: Keep the capture script out of the repo
3. **Cache keeps one continuous date range per symbol and fills any gap between old and new requests**
   This keeps the bookkeeping simple and correct. The cost is a larger one-off fetch when a request lands far from what is cached.
   Alternatives: Track several separate ranges per symbol
4. **Cache rescales stored adjusted closes when an overlap day differs**
   Yahoo re-bases every past adjclose after each dividend. Without rescaling, a series stitched from old and new fetches would jump at the join and skew total-return figures.
   Alternatives: Re-fetch full history on every extension; Ignore the drift
5. **Cache serves stale quotes, bars and searches, with a logged warning, when Yahoo fails**
   The design says to degrade gracefully. Pages keep working offline or when rate limited, and errors surface only when nothing is cached.
   Alternatives: Always raise so the page shows the error banner
6. **A quote's previous close comes from the daily bars, not meta.chartPreviousClose**
   With range=5d, chartPreviousClose is the close before the 5-day window, so today's change would have been wrong.
   Alternatives: Use meta.chartPreviousClose

**Summary**

> Added the Yahoo price source and SQLite cache, and made Yahoo the app's default price source.
> - `prices/yahoo.py`: YahooPriceSource parses chart and search JSON and sends the honest UA with a polite gap between requests. A 429 becomes `RateLimited`, a 404 becomes `UnknownSymbol`, and a range before a fund existed (Yahoo's 400 "Data doesn't exist") gives an empty series. Network, 5xx, non-JSON and other 4xx replies become `PriceSourceError`. Null rows (holidays, a fund's unpriced today) are skipped.
> - `prices/cache.py`: CachingPriceSource keeps daily bars for good and fetches only the missing head or tail of a range. Today's bar is re-fetched after 15 minutes. Cached adjusted closes are rescaled when Yahoo re-bases them after a dividend. Quotes are cached for 15 minutes and searches for a day, and cached data is served when the source fails.
> - `app.py`: `_make_yahoo` returns CachingPriceSource(YahooPriceSource()) with the cache at `<DATA_DIR>/prices.sqlite`, and DEFAULT_PRICE_SOURCE is now "yahoo"
> - Recorded Yahoo replies in tests/fixtures/yahoo (plus a hand-written 429) and `tools/record_yahoo_fixtures.py` to refresh them; 52 new tests in test_yahoo.py and test_cache.py, none live


### T3 ui-harness-and-shots

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:31 to 2026-10-27 15:34 (2m 37s)
- **Outcome:** done; committed [`39b2c2f36233`](https://github.com/wingware-dev/investaround/commit/39b2c2f36233e2254ff311b6c3934ece8df03128)
- **Usage:** 2,248 input, 16k output, 1.05M cache read, 49k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Paper investing app step 2: UI harness and screenshot tool
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after step 1 app-foundation, side by side with steps 3 and 4.
>
> Adds tests/ui/harness.py (pytest fixtures). Each test starts its own app instance on an OS-assigned port with the fake source and a temp data dir, so instances can run concurrently. A headless Playwright browser uses installed Chrome (channel="chrome") and falls back to Playwright Chromium. Adds tools/shots.py with a registry of named shots that features add to, each in its own file under tools/shots/, so steps don't collide. Includes a smoke UI test (home loads, nav works), takes docs/shots/01-home-skeleton.png, and views it.
> Owns: tests/ui/{conftest,harness}.py, tests/ui/test_smoke.py, tools/shots.py, tools/shots/__init__.py, docs/shots/01-*. Shares: requirements.txt (dev deps; step 1 should already have added them).
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> [Tasks Manager, 2026-10-27 15:30] Manager, from T2 app-foundation (9fa9251e): build test apps with create_app({'DATA_DIR': tmp, 'PRICE_SOURCE': 'fake'}). For error-path tests, pass PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={...}). pytest is already configured (pyproject.toml sets pythonpath=['.']). Both installed Chrome (channel='chrome') and Playwright Chromium work here. docs/shots/00-app-skeleton.png already exists, so the next shot is 01-home-skeleton. Pass PRICE_SOURCE explicitly: T4 is making yahoo the default at the same time. T4 and T5 run beside you on other files.

**Judgement calls**

1. **Put the 01 shot in tools/shots/skeleton.py**
   Shots must be registered in a module, and step 9 owns tools/shots/home.py, so this name avoids a collision.
   Alternatives: Define it in tools/shots/__init__.py
2. **The page fixture fails a test on any uncaught JavaScript error**
   It catches broken feature JS early in every UI test. tools/shots.py applies the same check.
   Alternatives: Only collect errors and let each test assert on them
3. **Shot functions take (page, live)**
   live.store lets a shot seed portfolios directly, and page.goto('/path') works through base_url.
   Alternatives: Seed only by driving the UI
4. **Harness drops werkzeug's per-request access log lines**
   They cluttered the output of tests and tools/shots.py. Errors are still logged.

**Screenshots**

![01-home-skeleton.png](https://github.com/wingware-dev/investaround/raw/39b2c2f36233e2254ff311b6c3934ece8df03128/docs/shots/01-home-skeleton.png)

**Summary**

> Added the UI test harness, a screenshot tool with a per-feature shot registry, smoke UI tests, and the 01-home-skeleton screenshot.
> - tests/ui/harness.py: `start_app()` serves each app on an OS-assigned port from a thread, using the fake source and its own data dir. It also has `launch_browser()` (headless installed Chrome, falling back to Playwright Chromium) and the pytest fixtures `live_app`, `browser` and `page`. `page` sets base_url and fails the test on uncaught JS errors. tests/ui/conftest.py registers the fixtures.
> - tools/shots/__init__.py: `@shot("NN-name", "description")` registry and `load_all()`, which imports every module in tools/shots/. tools/shots/skeleton.py defines 01-home-skeleton.
> - tools/shots.py: a CLI that takes shots by name or glob and supports `--list` and `--out`. Each shot gets a fresh app and page.
> - tests/ui/test_smoke.py: 8 tests (home loads, nav reaches every section with the right aria-current, brand link, 404, two apps side by side, registry rules, CLI writes a PNG and rejects unknown names). All pass.
> - docs/shots/01-home-skeleton.png: generated and checked by eye.


### T5 analytics-engine

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:31 to 2026-10-27 15:38 (6m 46s)
- **Outcome:** done; committed [`573816e5f614`](https://github.com/wingware-dev/investaround/commit/573816e5f614dbbaae095656949e4f9c02df4853)
- **Usage:** 40 input, 47k output, 1.05M cache read, 77k cache write (claude-opus-5-5)

**Prompt**

> Paper investing app step 4: analytics engine
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after step 1 app-foundation, side by side with steps 2 and 3.
>
> Pure functions with no Flask. Builds a portfolio value series from holdings (weights to shares at start, using adjusted close for total return). Computes total return, CAGR, annualized volatility, max drawdown with dates, best and worst year, and per-holding contribution. Compares against a benchmark series. Strategies: buy & hold, rebalancing (monthly/quarterly/yearly), dollar-cost averaging (amount per month), and lump sum vs DCA. Tests use small synthetic series with hand-computed answers.
> Owns: analytics/*.py, tests/unit/test_{performance,strategies}.py. Shares: none.
>
> See <project>/.TASKS/notes/paper-investing-app-step-4-analytics-engine.md

**Judgement calls**

1. **Package lives at investaround/analytics/ (inside the app package)**
   The design's layout tree puts analytics/ under investaround/, next to prices/ and web/; the task's bare 'analytics/*.py' is relative to that.
   Alternatives: Top-level analytics/ package
2. **A holding with no price yet waits as cash until its first price, then is bought**
   Step 6 needs to 'start them late'. Keeping the money as cash keeps the starting amount honest and the contributions adding up. The UI can read late_starts and no_data to explain it. Seen on real fixtures: VXUS starts 2011-01-28, so a 2008 three-fund backtest holds 30% cash through the crash.
   Alternatives: Re-split the money among the holdings that have prices on day one; Start the whole backtest at the latest first date
3. **Total return = final value / money deposited - 1; CAGR, volatility, drawdown and yearly returns use the time-weighted growth index**
   For DCA, deposits must not count as gains. For buy & hold the two returns are the same. CAGR is therefore the investments' rate, not the saver's money-weighted rate (IRR).
   Alternatives: Money-weighted IRR for CAGR
4. **CAGR is None for ranges under a year; best and worst year use full calendar years only**
   Annualizing a few weeks gives misleading numbers to beginners. A partial year is one that starts after the first week of January or ends before December 24; it is still listed in yearly, flagged partial.
   Alternatives: Always annualize; Include partial years in best/worst
5. **Volatility assumes 252 trading days a year**
   Standard for stocks and funds. It would understate volatility for 7-day-a-week assets such as crypto, which no fixture contains.
   Alternatives: Estimate periods per year from the data
6. **Lump sum vs DCA: both start holding the whole sum; DCA invests it in equal monthly parts and keeps the rest as uninvested cash, earning nothing**
   Same money and same start date makes the final values directly comparable. Parts the range is too short to invest stay as cash.
   Alternatives: DCA money arrives monthly from outside (the plain dollar_cost_average does this)
7. **Share-count holdings take their starting cost from close and grow by adjclose**
   Gives the real starting value while still counting total return. The T4 yahoo-price-source finding (close is already split-adjusted) means share counts are on today's split basis; this is noted in the module docstring.
   Alternatives: Use adjclose for cost too

**Summary**

> Added the pure analytics engine `investaround/analytics/`, with no Flask, plus 46 unit tests on small synthetic series with hand-computed answers.
> - `performance.py`: `simulate()` runs a portfolio day by day on adjusted closes, with deposits, scheduled buys and optional rebalancing. `portfolio_value_series()` builds buy & hold from saved weight or share-count holdings. `metrics()` gives total return, time-weighted return, CAGR, annualized volatility, max drawdown with peak, trough and recovery dates, calendar-year returns with best and worst year, and each holding's gain and contribution. `compare_to_benchmark()` replays the same money on the same days into a benchmark.
> - `strategies.py`: `buy_and_hold`, `rebalanced` (monthly, quarterly or yearly), `dollar_cost_average` (an amount per month plus an optional initial sum) and `lump_sum_vs_dca`.
> - Holdings that start late wait as cash until their first price and are reported in `late_starts`. Symbols with no data at all stay as cash and are listed in `no_data`.


### T8 example-portfolios

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:34 to 2026-10-27 15:39 (5m 07s)
- **Outcome:** done; committed [`2d5891525b5e`](https://github.com/wingware-dev/investaround/commit/2d5891525b5e95e060b971a11c5ebfdfe9f416f4)
- **Usage:** 76 input, 29k output, 2.35M cache read, 81k cache write (claude-opus-5-5)

**Prompt**

> Paper investing app step 7: example portfolios gallery
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after step 2 (ui-harness-and-shots); side by side with 5, 6 and 8.
>
> About 8 examples, each with a plain explanation of the idea and its risks: S&P 500 only, Three-fund (VTI/VXUS/BND), 60/40, All-weather-style, Dividend payers, Tech/growth-heavy, 10 blue-chip stocks, Gold & REIT diversifier. Each card has a mini history chart and buttons for "Try it as my portfolio" (copy to store) and "See how it would have done" (link to history). Shot: 30-examples.png.
> Owns: examples/examples.json, web/examples.py, templates/examples/*, tools/shots/examples.py, tests/ui/test_examples.py, tests/unit/test_examples_data.py (every symbol has fixtures and weights sum to 100). Shares: none.
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> See <project>/.TASKS/notes/paper-investing-app-step-7-example-portfolios-gallery.md

**Judgement calls**

1. **"Six blue-chip stocks" instead of 10** (report 1)
   Only 6 individual stocks (AAPL, MSFT, AMZN, NVDA, JNJ, KO) have recorded fixtures. The unit test requires fixtures for every symbol, and recording more would mean live network use and editing step 1's fixtures.
   Alternatives: Record 4+ more stock fixtures (e.g. JPM, PG, XOM, WMT) and make it 10
2. **Examples use only the 15 recorded symbols** (report 1)
   Same fixture limit. All-weather is approximated with VTI/BND/GLD (no long-term bonds or commodities), and Dividend payers uses JNJ/KO/MSFT/VNQ instead of a dividend ETF. The text says the all-weather version is simplified.
   Alternatives: Add TLT, DBC, VYM/SCHD fixtures
3. **Mini charts are 10-year buy-and-hold with an S&P 500 (SPY) dashed line, plus the final value and worst drop** (report 1)
   Every fixture covers 10 years, and the worst drop shows the risk in plain terms next to the gain.
   Alternatives: Since inception per example; No benchmark line
4. **After "Try it" the user stays on Examples, which shows an "Added … Go to My portfolios" notice** (report 1)
   The portfolio pages are being built in parallel (step 5), so their per-portfolio URLs aren't known yet. Repeat copies get named "Name (2)".
   Alternatives: Redirect to the new portfolio's watch page once step 5 exists
5. **Chart JS inline in the template, not static/js/examples.js** (report 1)
   The task's Owns list covers templates/examples/* but not static/js.

**Screenshots**

![30-examples.png](https://github.com/wingware-dev/investaround/raw/2d5891525b5e95e060b971a11c5ebfdfe9f416f4/docs/shots/30-examples.png)

**Summary**

> Added the example portfolios gallery: 8 plain-language examples, each with the idea, its risks, holdings and a mini 10-year growth chart against the S&P 500.
> - investaround/examples/examples.json: S&P 500 only, Three-fund, 60/40, All-weather style, Dividend payers, Tech/growth heavy, Six blue-chip stocks, Gold & real-estate diversifier.
> - web/examples.py: loads the examples (`load_examples`/`get_example`), computes buy-and-hold growth of $10,000 (adjusted closes, month-end samples, worst drop). `POST /examples/<id>/try` copies an example into the store without clashing names. "See how it would have done" links to `/history/?example=<id>`. If a card's prices can't be fetched, that card says so and the rest of the page still loads.
> - templates/examples/index.html with inline Chart.js mini charts; tools/shots/examples.py and docs/shots/30-examples.png.
> - tests/unit/test_examples_data.py (every symbol has fixtures, weights sum to 100, the copy is a valid portfolio, growth checked by hand) and tests/ui/test_examples.py. 51 tests passed (including the smoke UI tests).


### T6 portfolio-builder-watch

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:37 to 2026-10-27 15:45 (7m 25s)
- **Outcome:** done; committed [`404acfb9a4ae`](https://github.com/wingware-dev/investaround/commit/404acfb9a4aec10e4b745527d08e276a969bd3d3)
- **Usage:** 78 input, 46k output, 3.05M cache read, 113k cache write (claude-opus-5-5)

**Prompt**

> Paper investing app step 5: portfolio builder and daily watch page
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after steps 2 (ui-harness-and-shots) and 3 (yahoo-price-source); side by side with 6, 7 and 8.
>
> Create, edit and delete paper portfolios with a $10,000 pretend start. Holdings are added through symbol search (/api/search) with weights, a 5-20 guidance hint, and validation. The watch page shows each holding's current price, today's change, value and gain since the portfolio was created, totals, and a "last updated" time with refresh. UI tests create a portfolio as a user would. Shots: 10-build-portfolio.png, 11-watch-portfolio.png.
> Owns: web/portfolios.py, templates/portfolios/*, static/js/portfolio.js, tools/shots/portfolios.py, tests/ui/test_portfolios.py. Shares: none.
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> See <project>/.TASKS/notes/paper-investing-app-step-5-portfolio-builder-and-daily-w.md

**Judgement calls**

1. **A portfolio is bought at the last closing price before the day it was created**
   No purchase price is stored in the model, so the start has to come from history. Using the close before the creation day means the starting point never moves afterwards, which today's still-changing bar could not guarantee. On day one the gain equals today's change. The watch page says which close was used.
   Alternatives: Add purchase prices to Holding in models.py (outside this task's files); Use the close on the creation day itself
2. **Gains use the adjusted-close ratio, so dividends and splits count**
   This matches how the history and analytics features measure total return.
3. **Changing investments or weights starts the portfolio again from today; renaming or editing notes does not**
   Otherwise an edit would rewrite the past, as if the new mix had been held since the original date. The edit form explains this.
   Alternatives: Keep the original start date always; Ask with a checkbox
4. **Served /api/search at the site root using record_once in web/portfolios.py**
   The task names /api/search but app.py is not in this task's files, and a blueprint route always gets the /portfolios prefix.
5. **Added tests/unit/test_portfolios_web.py beyond the listed files**
   The valuation maths and form checks are easier to cover exactly with unit tests than through the browser. It is a new file, so it doesn't collide with other tasks.
6. **Deleting goes through a confirmation page rather than a JavaScript confirm()**
   It works without JavaScript and is easy to drive in UI tests.

**Screenshots**

![10-build-portfolio.png](https://github.com/wingware-dev/investaround/raw/404acfb9a4aec10e4b745527d08e276a969bd3d3/docs/shots/10-build-portfolio.png)

![11-watch-portfolio.png](https://github.com/wingware-dev/investaround/raw/404acfb9a4aec10e4b745527d08e276a969bd3d3/docs/shots/11-watch-portfolio.png)

**Summary**

> Added the portfolio builder and the daily watch page:
> - `/portfolios/` lists portfolios with value, today's change and gain. Each one can be created, edited and deleted (deleting asks first on a confirm page).
> - The builder adds investments through symbol search (`/api/search`) and splits $10,000 evenly until the user types weights. It shows the 5–20 guidance, a running weight total and dollar amounts. The server checks the weights and that every symbol is known.
> - The watch page shows price, today's change, value and gain since start for each holding, plus totals. It has a "Last updated" time and a Refresh button that reloads only the table, and it also refreshes every 5 minutes. If prices are unavailable it shows a message instead of an error page.
> - New unit and UI tests. Screenshots are in docs/shots/10-build-portfolio.png and docs/shots/11-watch-portfolio.png.


### T7 history-backtest-page

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:38 to 2026-10-27 15:45 (6m 17s)
- **Outcome:** done; committed [`87a7e0dfdbd7`](https://github.com/wingware-dev/investaround/commit/87a7e0dfdbd7b5e0fc061d8d2a3ea8d19b4e7881)
- **Usage:** 2,222 input, 39k output, 3.12M cache read, 108k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Paper investing app step 6: history / "what if" backtest page
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after steps 2, 3 and 4 (ui-harness-and-shots, yahoo-price-source, analytics-engine); side by side with 5, 7 and 8.
>
> Pick a portfolio (or a quick ad-hoc set) and a date range. Preset ranges: 1y, 5y, 10y, max, 2008 crash, 2020 crash, 2022 bear. The page charts the growth of $10,000 against a benchmark (SPY by default), shows a metrics table with plain-English tooltips, and a per-holding table. It handles symbols with no data that early by saying so and starting them late. Shots: 20-history-10y.png, 21-history-2008.png.
> Owns: web/history.py, templates/history/*, static/js/history.js, tools/shots/history.py, tests/ui/test_history.py. Shares: none.
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> [Tasks Manager, 2026-10-27 15:37] Manager, from T4 yahoo-price-source (ea97e03c): Yahoo's `close` is already split-adjusted, and `adjclose` only adds dividends. Use `adjclose` for total return. No split handling is needed.
>
> [Tasks Manager, 2026-10-27 15:38] Manager, from T5 analytics-engine (6cb78b44): use investaround.analytics: portfolio_value_series() and compare_to_benchmark(). Explain the ValueSeries' late_starts (holdings kept as cash until their first price) and no_data on the page. cagr and best/worst year are None for short ranges, so show 'n/a' for those.
>
> See <project>/.TASKS/notes/paper-investing-app-step-6-history-what-if-backtest.md

**Judgement calls**

1. **Crash presets: 2008 = Oct 1 2007–Dec 31 2012, 2020 = calendar 2020, 2022 = Jan 2022–Dec 2023**
   Each window shows the fall and the recovery, so a newcomer sees both the drop and how long holding on took. The one-line explanation of each shows on the page and in the button tooltip.
   Alternatives: Peak-to-trough only (e.g. Oct 2007–Mar 2009); Peak to full recovery, per symbol
2. **Custom-mix weights that don't add to 100 are scaled to 100, with a note**
   Friendlier for quick what-ifs ("SPY 3, BND 1" becomes 75/25). Missing some but not all weights is still an error.
   Alternatives: Reject unless the weights add up to exactly 100%, as saved portfolios do
3. **The first visit runs nothing. It preselects the first saved portfolio, else the Three-fund example**
   Avoids fetching prices before the user has chosen anything. One click on a range button runs it.
   Alternatives: Auto-run 10y on the default pick
4. **Added tests/unit/test_history_view.py, which the task's Owns list doesn't name**
   The regimen wants unit tests for the new parsing and range code, and the new file collides with nothing.
   Alternatives: Fold those checks into tests/ui/test_history.py
5. **Share-count portfolios chart their actual starting cost, not a fixed $10,000**
   portfolio_value_series() buys the given shares at the first close, so the headline says "$X put in on <date>" with the real amount. Weight portfolios and examples use their $10,000 start cash.
   Alternatives: Convert share counts to weights and always show $10,000

**Screenshots**

![20-history-10y.png](https://github.com/wingware-dev/investaround/raw/87a7e0dfdbd7b5e0fc061d8d2a3ea8d19b4e7881/docs/shots/20-history-10y.png)

![21-history-2008.png](https://github.com/wingware-dev/investaround/raw/87a7e0dfdbd7b5e0fc061d8d2a3ea8d19b4e7881/docs/shots/21-history-2008.png)

**Summary**

> Built the "What if?" history backtest page.
> - `web/history.py`: pick a saved portfolio, an example (`?example=<id>`, as the Examples page links) or your own mix ("VTI 60, BND 40", or "VTI, BND" to split evenly), a preset range (1y/5y/10y/max/2008 crash/2020 crash/2022 bear) or custom dates, and a benchmark (SPY by default). Runs `portfolio_value_series()` + `compare_to_benchmark()` on adjusted closes.
> - `templates/history/index.html` + `static/js/history.js`: growth chart against the benchmark, a "Good to know" box explaining late starts (money waits as cash until a holding's first price) and no-data holdings (kept as cash, with a Cash row), a metrics table with plain-English tooltips ('n/a' for CAGR and best/worst year on short ranges), and a per-holding table.
> - Friendly messages for an unknown example or portfolio, unknown symbols, bad weights or dates, and price-source failures. A benchmark failure still shows the portfolio, just without the comparison.
> - Tests: `tests/ui/test_history.py` (10 UI tests) and `tests/unit/test_history_view.py` (parsing, ranges, formatting). All 36 pass, plus the Examples→History link test.
> - Shots: `docs/shots/20-history-10y.png` and `docs/shots/21-history-2008.png` (`tools/shots/history.py`), both looked at.


### T9 learn-strategy-lab

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:38 to 2026-10-27 15:44 (5m 30s)
- **Outcome:** done; committed [`d94be11d7548`](https://github.com/wingware-dev/investaround/commit/d94be11d754872282e3e8135889c916e86293176)
- **Usage:** 70 input, 32k output, 2.58M cache read, 103k cache write (claude-opus-5-5)

**Prompt**

> Paper investing app step 8: Learn and Strategies lab
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after steps 2 and 4 (ui-harness-and-shots, analytics-engine); side by side with 5, 6 and 7.
>
> Short lessons: what stocks, ETFs, funds and bonds are; diversification; fees; volatility and drawdown; time in market; DCA; rebalancing. Adds a glossary. The Strategy lab runs lump sum vs DCA vs rebalancing for a chosen portfolio and range, and shows them side by side with a "what this shows" explanation. Adds a not-financial-advice disclaimer. Shots: 40-learn.png, 41-strategy-lab.png.
> Owns: web/learn.py, templates/learn/*, static/js/learn.js, tools/shots/learn.py, tests/ui/test_learn.py. Shares: none.
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> [Tasks Manager, 2026-10-27 15:38] Manager, from T5 analytics-engine (6cb78b44): use investaround.analytics.strategies: buy_and_hold, rebalanced(period in REBALANCE_PERIODS), dollar_cost_average, and lump_sum_vs_dca, which returns lump, dca, difference and winner. Each StrategyResult has key, label, series and metrics. Uninvested cash earns 0%, which tilts lump sum vs DCA slightly toward lump sum, so say so in the "what this shows" text.
>
> See <project>/.TASKS/notes/paper-investing-app-step-8-learn-and-strategies-lab.md

**Judgement calls**

1. **The lab has its own four ready-made mixes instead of using the Examples gallery's examples**
   The examples module belongs to task T7 and isn't committed yet, so depending on it would tie the two tasks together. With ready-made mixes the lab works even with no saved portfolio. Saved portfolios are also offered.
   Alternatives: Offer the examples from investaround.web.examples.load_examples() once T7 is committed
2. **Preset date ranges only, no custom start and end dates**
   Keeps the form simple for beginners and every result meaningful: 5/10/15 years, the 2008 crash, the 2020 crash and the 2022 bear market. Choices go in the URL, so results can be linked to.
   Alternatives: Add custom date inputs as on the History page
3. **Share-count portfolios are weighted by their value at the start of the range**
   The strategies take weights, so this turns share counts into weights and runs the same mix through all three strategies.
   Alternatives: Leave share-count portfolios out of the lab
4. **Added tests/unit/test_learn.py, which the task's Owns list doesn't name**
   The testing regimen asks for unit tests of new code. The lab's logic and explanation text are easier to pin down with synthetic prices than through the UI. It is a new file, so it can't clash with other tasks.
   Alternatives: Put all the tests in tests/ui/test_learn.py

**Screenshots**

![40-learn.png](https://github.com/wingware-dev/investaround/raw/d94be11d754872282e3e8135889c916e86293176/docs/shots/40-learn.png)

![41-strategy-lab.png](https://github.com/wingware-dev/investaround/raw/d94be11d754872282e3e8135889c916e86293176/docs/shots/41-strategy-lab.png)

**Summary**

> Adds the Learn page and the Strategy lab:
> - `/learn/`: a not-financial-advice disclaimer, nine short lessons (stocks, bonds, funds/ETFs, diversification, fees, volatility and drawdown, time in market, DCA, rebalancing) with "Try it" links, and a glossary of 27 terms you can filter.
> - `/learn/lab`: runs $10,000 three ways (all at once, spread over 3/6/12/24 months, rebalanced monthly/quarterly/yearly) for a ready-made mix or a saved portfolio over six preset ranges. Shows the three side by side with metrics and a shared chart, plus a "What this shows" text built from the results. The text says that waiting cash earns 0%, and how far the mix drifted without rebalancing.
> - Tests in tests/unit/test_learn.py and tests/ui/test_learn.py; shots docs/shots/40-learn.png and 41-strategy-lab.png.


### T13 richer-example-fixtures

- **Origin:** Filed by the Tasks Manager from the plan of T8 example-portfolios
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:40 to 2026-10-27 15:42 (2m 06s)
- **Outcome:** done; committed [`c082bed9c661`](https://github.com/wingware-dev/investaround/commit/c082bed9c66129bbfcf97dfd5c6d37482e40a9cd)
- **Usage:** 1,938 input, 9,132 output, 1.60M cache read, 20k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Record more fixtures for richer example portfolios
>
> Follow-up from T8 example-portfolios (5868efa4); it completes the plan's example list, which asked for "10 blue-chip stocks". Run tools/record_fixtures.py (live, developer-run, read-only Yahoo GETs) for JPM, PG, XOM, WMT, HD, TLT, DBC, VYM, for example. Then make "Six blue-chip stocks" a true 10-stock example, give All-weather its long-term bonds and commodities, and add a dividend ETF to Dividend payers. Keep tests/unit/test_examples_data.py passing (every symbol has fixtures, weights sum to 100) and refresh docs/shots/30-examples.png if the cards change visibly.

**Judgement calls**

1. **All-weather uses the published 30/40/15/7.5/7.5 split with TLT, IEF, GLD and DBC**
   It matches the well-known Dalio mix that the card describes, and the 7.5% weights show fine as "7.5%".
   Alternatives: Round to 30/40/15/8/7
2. **Dividend payers: 50% in VYM and SCHD, plus JNJ, KO, PG, HD and VNQ at 10% each; MSFT dropped**
   The two funds give real diversification. Dropping MSFT avoids overlap with the tech and blue-chip examples, and it lets HD, which was recorded for this, be used.
   Alternatives: Use only one dividend ETF
3. **Edited tests/unit/test_fake_source.py and tools/record_fixtures.py, outside the examples files**
   The fake-source test asserts the exact recorded symbol list. Without the default-list change, a full fixture refresh would leave the new symbols stale.

**Summary**

> Recorded price fixtures for 10 more symbols and used them to make three example portfolios complete.
> - New fixtures (live, read-only Yahoo GETs through tools/record_fixtures.py): JPM, PG, XOM, WMT, HD, TLT, IEF, DBC, VYM and SCHD. quotes.json only gained entries; existing quotes and its as_of date are unchanged. They're also added to the recorder's default list and to the fake-source test's list.
> - "Six blue-chip stocks" is now "10 blue-chip stocks": ten companies at 10% each, adding JPMorgan, Procter & Gamble, ExxonMobil and Walmart.
> - All-weather now follows Dalio's mix: VTI 30, TLT 40, IEF 15, GLD 7.5, DBC 7.5, with the idea and risks text rewritten to match.
> - Dividend payers now puts half in two dividend funds: VYM 25 and SCHD 25, then JNJ, KO, PG, HD and VNQ at 10 each.
> - Refreshed docs/shots/30-examples.png. 55 tests passed (examples unit and UI tests, fake-source tests).


### T12 interest-on-uninvested-cash

- **Origin:** Filed by the Tasks Manager from the plan of T5 analytics-engine
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:43 to 2026-10-27 15:46 (2m 55s)
- **Outcome:** done; committed [`2a0194fc572f`](https://github.com/wingware-dev/investaround/commit/2a0194fc572f337504b97ae08809b9f1af0a2aa4)
- **Usage:** 40 input, 17k output, 1.93M cache read, 29k cache write (claude-opus-5-5)

**Prompt**

> Interest on uninvested cash
>
> Follow-up proposed by T5 analytics-engine (6cb78b44). Optionally let cash (waiting DCA money, late-start holdings) earn a fixed or T-bill rate instead of 0%, which currently makes lump sum vs DCA slightly favour lump sum. Code is in investaround/analytics.
>
> [Tasks Manager, 2026-10-27 15:43] Manager: T7 history-backtest-page and T9 learn-strategy-lab are calling investaround.analytics right now. Add the cash rate as an optional keyword that defaults to 0%, so existing calls and results stay unchanged. Don't edit web/, templates/ or static/; the pages can offer the option later.
>
> See <project>/.TASKS/notes/interest-on-uninvested-cash.md

**Judgement calls**

1. **A fixed rate is a fraction (0.04); a yield series is in percent (5.0), as Yahoo's ^IRX reports it**
   A float in fractions matches the other analytics inputs, and a ^IRX PriceSeries from the price source can be passed straight in without conversion. Both are documented in the performance.py module docstring.
   Alternatives: Percent for both; Only a fixed rate
2. **Dates before a yield series' first value earn 0%**
   This is the same rule as a holding with no price yet. Nothing is invented for missing data.
   Alternatives: Back-fill the first yield
3. **Lump sum vs DCA's final installment invests all remaining cash, not just total/months**
   Otherwise the interest would sit as cash forever after the money is supposed to be fully invested. With 0% the result is identical to before.
   Alternatives: Leave the interest as cash
4. **Negative rates down to just above -100% are allowed**
   Negative cash rates have existed in real markets; only rates at or below -100% (or non-finite ones) are rejected.

**Summary**

> Uninvested cash can now earn interest through an optional `cash_rate` keyword, defaulting to 0% so existing calls and results are unchanged.
> - `cash_rate` is accepted by `simulate`, `portfolio_value_series`, `buy_and_hold`, `rebalanced`, `dollar_cost_average` and `lump_sum_vs_dca`. It is a fixed yearly fraction (0.04) or a PriceSeries of percent yields such as Yahoo's ^IRX T-bill series.
> - Interest compounds over calendar days on all cash, including money waiting for late-starting holdings. It counts as gain, not as a deposit, and is reported in `ValueSeries.interest` and `Metrics.interest_earned`.
> - Benchmark comparisons give the benchmark's waiting cash the same rate. Lump sum vs DCA's last installment invests all remaining cash, interest included.


### T14 examples-in-strategy-lab

- **Origin:** Filed by the Tasks Manager from the plan of T9 learn-strategy-lab
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:44 to 2026-10-27 15:46 (1m 40s)
- **Outcome:** done; committed [`041823065e47`](https://github.com/wingware-dev/investaround/commit/041823065e473eaf9e205ec4c5606560f8511986)
- **Usage:** 2,111 input, 7,379 output, 1.78M cache read, 17k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Offer example portfolios in the strategy lab
>
> Follow-up from T9 learn-strategy-lab (341d042b), joining it to T8 example-portfolios (5868efa4, committed). Add the example portfolios (investaround.web.examples) to the strategy lab's portfolio picker, perhaps replacing learn.PRESETS, and add a "Try in the strategy lab" link on each example card. Update the UI tests, and refresh docs/shots/41-strategy-lab.png and 30-examples.png if they change visibly.

**Judgement calls**

1. **Replaced the lab's own presets with the examples, dropping the "Stocks and gold" mix**
   One list of ready-made portfolios across the app. The gold-and-REIT example covers gold, and three of the four presets were already examples.
   Alternatives: Keep the presets alongside the examples
2. **Old ?portfolio=preset:<id> links fall back to the default 60/40**
   The lab was committed only shortly before, so no one has bookmarks worth keeping, and unknown choices already fall back to the default.
   Alternatives: Map preset:<id> to example:<id>

**Summary**

> The strategy lab's portfolio picker now offers the eight example portfolios in place of its own presets, and each example card links to the lab with that example chosen:
> - web/learn.py: removed `PRESETS`; the "Example portfolios" choices come from `load_examples()` (`?portfolio=example:<id>`), with 60/40 still the default.
> - Examples cards: new "Try in the strategy lab" button.
> - Updated UI and unit tests and added new ones; refreshed docs/shots/30-examples.png and 41-strategy-lab.png.


### T10 home-dashboard-docs

- **Origin:** Filed by the Tasks Manager from the plan of T1 new-investing-want-software, at the user's request
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:46 to 2026-10-27 15:52 (5m 51s)
- **Outcome:** done; committed [`2cc5ced41921`](https://github.com/wingware-dev/investaround/commit/2cc5ced41921e3c15dc66dc76ee5b6cf597abe96)
- **Usage:** 2,216 input, 29k output, 4.01M cache read, 127k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Paper investing app step 9: home dashboard, integration and docs
>
> From the accepted plan of T1 new-investing-want-software (691d1322); full design in .TASKS/notes/i-m-new-to-investing-and-want-some-software-so-i-can-try.md. Runs after steps 5-8.
>
> Home shows all portfolios with today's change and a sparkline, plus a "start here" path (examples, build, watch, history, learn). Adds the data-source status and error banner and a README (install, run, data-source caveat, where data is stored). Regenerates the full docs/shots/ set with tools/shots.py and reviews every image. Runs a final live manual check with the real Yahoo source (read-only GETs, developer step, not a test).
> Owns: web/home.py, templates~ README.md, tools/shots/home.py. Shares: templates/base.html, static/css/app.css, docs/shots/.
>
> Commit a screenshot of each major visible change under docs/shots/ (the user wants a publishable trace).
>
> [Tasks Manager, 2026-10-27 15:39] Manager, from T8 example-portfolios (5868efa4): as part of integration, change POST /examples/<id>/try (or the link in its "Added …" notice) to go to the new portfolio's own watch page from T6, not to /portfolios/.
>
> [Tasks Manager, 2026-10-27 15:44] Manager, from T9 learn-strategy-lab (341d042b): link /learn/ (lessons) and /learn/lab (strategy lab) from the home dashboard's "start here" path.
>
> [Tasks Manager, 2026-10-27 15:45] Manager, from T6 portfolio-builder-watch (b0a3ff12): for each portfolio's value, today's change and gain, call investaround.web.portfolios.value_portfolio(p, prices) instead of computing them again.
>
> See <project>/.TASKS/notes/paper-investing-app-step-9-home-dashboard-integration-a.md

**Judgement calls**

1. **Sparkline shows the current holdings over the last 91 days**
   Most portfolios are new, so a 'since start' line would often be one or two points; 3 months always gives a readable trend. The column header and tooltip say so.
   Alternatives: Since the portfolio's start date; Last 30 days
2. **Did not regenerate 01-home-skeleton.png**
   It records the skeleton stage for the publishable trace; regenerating it would overwrite that with the new dashboard under a 'skeleton' name. The new home is in 50-52.
   Alternatives: Regenerate it too; Delete the skeleton shot
3. **Status and error banner are on the home page only**
   Every other page already handles price errors its own way (the 503 error page, the watch-page error, per-card notices). A site-wide banner would need a change to how app.py tracks the price source's state.
   Alternatives: Track the last price failure in app.py and show it on every page
4. **Removed the examples page's 'Added …' notice**
   The try button now goes straight to the new portfolio's watch page (Manager request from T8), so nothing used the notice. The watch page's notes already say 'Copied from the … example.'
   Alternatives: Keep the notice and show it on the watch page
5. **Home shots are numbered 5x**
   Shot names are grouped by feature; I documented 5x for the home dashboard in tools/shots/__init__.py.
   Alternatives: 02-home-*

**Screenshots**

![50-home-dashboard.png](https://github.com/wingware-dev/investaround/raw/2cc5ced41921e3c15dc66dc76ee5b6cf597abe96/docs/shots/50-home-dashboard.png)

![51-home-first-visit.png](https://github.com/wingware-dev/investaround/raw/2cc5ced41921e3c15dc66dc76ee5b6cf597abe96/docs/shots/51-home-first-visit.png)

![52-home-price-error.png](https://github.com/wingware-dev/investaround/raw/2cc5ced41921e3c15dc66dc76ee5b6cf597abe96/docs/shots/52-home-price-error.png)

**Summary**

> Added the home dashboard, the price-source status and error banner, and a README, and sent "Try it as my portfolio" to the new portfolio's watch page.
> - Home lists every portfolio with value, today's change and gain (from `value_portfolio`), a 3-month SVG sparkline, totals, and a 6-step "start here" path (examples, build, watch, history, learn, strategy lab).
> - The home page shows where prices come from and how fresh they are, with an error banner when prices can't be fetched.
> - `POST /examples/<id>/try` now redirects to the new portfolio's watch page; the unused "Added …" notice is gone.
> - README covers install, run, the Yahoo data-source caveat and where data is stored.
> - Added shots 50-home-dashboard, 51-home-first-visit and 52-home-price-error and regenerated the rest (only 10 and 11 changed, in their timestamps); reviewed every image.
> - Live check against real Yahoo, in a temp data dir: home, watch, history, examples and search all worked, with no JS errors and matching values.


### T20 irx-tbill-fixture

- **Origin:** Filed by the Tasks Manager from the plan of T12 interest-on-uninvested-cash
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:46 to 2026-10-27 15:48 (1m 37s)
- **Outcome:** done; committed [`2f1ae55126c1`](https://github.com/wingware-dev/investaround/commit/2f1ae55126c145eeb8ad5d6a786d22f39a346086)
- **Usage:** 30 input, 7,676 output, 1.67M cache read, 15k cache write (claude-opus-5-5)

**Prompt**

> Record a ^IRX T-bill yield fixture
>
> Follow-up from T12 interest-on-uninvested-cash (c4e0c2ee). Add ^IRX to tools/record_fixtures.py and record it into tests/fixtures/prices (live, developer-run, read-only Yahoo GETs), so the "cash earns T-bill rates" path is tested with real data rather than synthetic only.

**Judgement calls**

1. **Re-recorded only ^IRX, not all symbols**
   Re-running for every symbol would have rewritten the other 25 fixtures and changed results other tasks' tests depend on. Running with just ^IRX kept the rest of quotes.json and the frozen as_of date as they were.
   Alternatives: Refresh every fixture
2. **^IRX is a normal FakePriceSource symbol, with a quote entry and a file named ^IRX.csv**
   FakePriceSource only knows symbols that have a quote entry. The yields therefore load through src.history('^IRX') like any price, and ^IRX now shows in fake-source search for terms like 'treasury'. No existing search test is affected.
   Alternatives: Keep the yield series outside the price fixtures with its own loader
3. **Edited tests/unit/test_fake_source.py (from step 1) to add ^IRX to its exact symbol list**
   That test pins the full set of recorded symbols, so adding the fixture would otherwise break it.

**Summary**

> Recorded real 13-week T-bill yields (^IRX) as a price fixture, so interest on uninvested cash is now tested with real data.
> - Added ^IRX to tools/record_fixtures.py. I ran it live for ^IRX only: one read-only Yahoo GET recorded tests/fixtures/prices/^IRX.csv (5,484 daily yields in percent, 2005-01-03 to 2026-10-27). quotes.json only gained the ^IRX entry; its recording date and as_of are unchanged.
> - tests/unit/test_performance.py adds real-yield tests. 2023 cash interest falls between that year's lowest and highest yield. 2021's near-zero yields earn almost nothing. Lump sum vs DCA's waiting money earns T-bill interest.
> - Added ^IRX to the pinned symbol list in tests/unit/test_fake_source.py.


### T19 cash-rate-option-in-pages

- **Origin:** Filed by the Tasks Manager from the plan of T12 interest-on-uninvested-cash
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:53 to 2026-10-27 16:00 (7m 21s)
- **Outcome:** done; committed [`347320221c6d`](https://github.com/wingware-dev/investaround/commit/347320221c6d9d3037001505c2f9b9be31c52619)
- **Usage:** 1,880 input, 32k output, 5.87M cache read, 88k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Offer the cash rate on the history page and strategy lab
>
> Follow-up from T12 interest-on-uninvested-cash (c4e0c2ee), which added cash_rate to investaround.analytics but no way to choose it. Add a "cash earns" option (0%, a fixed %, or T-bill) to web/history.py and web/learn.py, pass cash_rate through, and show Metrics.interest_earned. Update the UI tests and the history and strategy-lab screenshots in docs/shots/.
>
> [Tasks Manager, 2026-10-27 15:52] Manager, from T10 home-dashboard-docs (f91681c3): the strategy lab's "what this shows" text still says waiting money "earns nothing (0%)". Once the cash option exists, make that text match the chosen rate. The T-bill choice can use the ^IRX fixture that T20 irx-tbill-fixture recorded (tests/fixtures/prices/^IRX.csv, committed in 2f1ae55).

**Judgement calls**

1. **The T-bill rate is described as the yield averaged over the days cash waited, weighted by how much cash waited**
   Averaging over the whole range said '2.4% a year' for a 10-year lab run where cash only waited during the first year, at about 0.6%. The weighted figure matches the interest actually shown.
   Alternatives: Plain average over the whole range; Name no number, only 'Treasury bill rates'
2. **If T-bill rates can't be fetched, or there are none for the dates, the page runs at 0% and says so instead of failing**
   A short outage of the unofficial Yahoo source shouldn't hide the whole backtest. An invalid fixed rate, by contrast, is the user's input, so the page shows a field error and doesn't run.
   Alternatives: Show an error and run nothing
3. **The "Interest on cash" row appears only when cash earns something, and then on every column and card, including $0 ones**
   With 0% the pages look exactly as before, so existing tests and shots are unaffected. When cash earns, the $0 figures make clear that only waiting money earns interest.
   Alternatives: Always show the row; Show it only where interest is above zero
4. **Fixed rates are limited to 0-20% a year in the UI, defaulting to 4%**
   Keeps out typos such as 40 meant as 4.0. Negative rates are allowed by the engine but not offered to beginners.
   Alternatives: Allow negative rates; No upper limit
5. **Shots 21-history-2008 and 41-strategy-lab now show the option turned on; 20-history-10y shows the default**
   The task asked to update these screenshots. In 2008, VXUS's late start is where waiting cash matters, and the lab is where the comparison changes.
   Alternatives: Add new shots and keep the old ones as they were
6. **The lab's 0% explanation now ends by pointing to the new option**
   The T10 relay asked for the text to match the chosen rate. The 0% wording keeps 'earns nothing (0%)' and adds 'Try a fixed rate or Treasury bill rates under “Waiting cash earns”.'

**Summary**

> The history page and the strategy lab now have a "Waiting cash earns" option: nothing (0%, the default), a fixed rate, or Treasury bill rates from ^IRX. The interest earned is shown on both pages.
> - The new `web/cash.py` reads the `cash` and `cash_rate` query parameters for both pages, validates fixed rates from 0 to 20%, and turns the choice into the analytics `cash_rate`. If T-bill rates can't be fetched, it falls back to 0% with a note. The T-bill rate shown is the average yield weighted by the cash actually waiting each day.
> - History page: when cash earns something, the metrics table gets an "Interest on cash" row and the "Good to know" box says what the cash earned.
> - Strategy lab: the spread-out card's description, a new "Interest on cash" row and the "What this shows" text now match the chosen rate. At 0% it still says waiting money earns nothing.
> - The rate box is shown, and submitted, only when "A fixed rate" is picked.
> - Added unit and UI tests, and regenerated docs/shots 20-history-10y, 21-history-2008 (now with T-bill rates) and 41-strategy-lab (now with 4% a year).


### T15 store-purchase-prices

- **Origin:** Filed by the Tasks Manager from the plan of T6 portfolio-builder-watch
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 15:58 to 2026-10-27 16:01 (3m 01s)
- **Outcome:** done; committed [`08f02824bfc7`](https://github.com/wingware-dev/investaround/commit/08f02824bfc7570852788b6a390239bdb6fa1dc4)
- **Usage:** 1,954 input, 16k output, 3.66M cache read, 25k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Store purchase prices on holdings
>
> Follow-up proposed by T6 portfolio-builder-watch (b0a3ff12). Record each holding's start price and date in the Portfolio model (investaround/models.py, storage.py) when it is created. Gains would then not depend on fetching history around the creation date, and a shares view becomes possible.
>
> [Tasks Manager, 2026-10-27 15:58] Manager: T19 cash-rate-option-in-pages is changing web/history.py, web/learn.py and their screenshots at the same time, so stay out of those files. Portfolios saved without start prices must still load, so make the new fields optional in storage.

**Judgement calls**

1. **Re-fetch the start day's price bar instead of relying only on the stored price**
   Yahoo's close is split-adjusted after the fact, and the adjusted close changes with each dividend. A stored price alone would show a split as a crash and leave dividends out. The stored date makes the fetch exact, a single day with no lookback guessing, and the stored price is the fallback.
   Alternatives: Use only the stored price (no dividends, and wrong after a split)
2. **Record missing start prices the first time a portfolio is viewed, saving to the store during a page load**
   Portfolios saved earlier, and those copied from Examples (which build Portfolio objects themselves), would otherwise keep using the history lookup. Recording on first view fixes their start once without touching examples.py.
   Alternatives: Have examples.py record them when copying; Never backfill old portfolios
3. **Show share count and 'bought at' price on the watch table**
   This is the shares view the follow-up mentioned. It is shown as small text under Weight and Price, so the table layout stays the same.

**Summary**

> Holdings now record the price and date they were "bought" at:
> - `Holding` has optional `start_price` and `start_date`, set together and saved in portfolios.json only when present. Portfolios saved without them still load.
> - Creating a portfolio records them, and so does an edit that changes investments or weights. Renaming or editing notes keeps them. Portfolios saved before this change, or copied from an example, get them on first view of My portfolios or the watch page.
> - Gains are computed from the start day's price bar, re-fetched for that exact day so later dividends and splits still count. If the bar can't be fetched, the recorded price is used, so gains no longer depend on searching history around the creation date.
> - The watch table now shows the share count and "bought at" price under each holding. Screenshot 11-watch-portfolio.png is regenerated, and model, storage, valuation and UI tests are added.


### T18 regression-tests-paper-app

- **Origin:** Filed by the Tasks Manager
- **Goal:** Paper investing app
- **Ran:** 2026-10-27 16:01 to 2026-10-27 16:02 (1m 15s)
- **Outcome:** done
- **Usage:** 1,745 input, 1,298 output, 164k cache read, 19k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Regression tests for the paper investing app build\n\nA sweep under wing_guide topic 'research' over the work of T2-T20: the paper investing app plan steps and their follow-ups, including the cash interest work in T12, T19 and T20. Each worker ran only its own tests, and several pages share the nav, the base template and the shot registry. Make one test_run (wing-testing) per batch: tests/unit, then tests/ui. File each failure with report_finding (next_step fix); don't fix anything here.
>
> See <project>/.TASKS/notes/regression-tests-for-the-paper-investing-app-build-n-na-s.md

**Summary**

> Regression sweep over the paper investing app work (T2-T20, including the cash interest work in T12, T19, T20) found no failures.
> - tests/unit: 297 passed (run 1793131304710)
> - tests/ui: 46 passed (run 1793131311602)
> - No findings filed; nothing fixed in place.


### T22 run-set-main-entry

- **Origin:** Written by the user
- **Goal:** Ungrouped Tasks
- **Ran:**  to 2026-10-27 16:11 ()
- **Outcome:** done
- **Usage:** 0 input, 0 output, 0 cache read, 0 cache write (model not recorded)

**Prompt**

> How do I run this?  Can you set the main entry point in Wing?
>
> See <project>/.TASKS/notes/how-do-i-run-this-can-you-set-the-main-entry-point-in-w.md

**Summary**

> The main entry point is already set to investaround/__main__.py, so Wing's Debug or Run (with no other file chosen) starts the app at http://127.0.0.1:8765/ and opens it in your browser. From a terminal, run `.venv/bin/python -m investaround`. The README's Run section lists the options, such as `--source fake` for offline sample prices. I haven't launched it from Wing myself. If Wing reports an ImportError about relative imports (that file uses `from .app import ...`), make T22 Ready again and I'll file a task to add a small top-level launcher script and point the entry point at it.


### T23 running-wing-doesn-work

- **Origin:** Written by the user
- **Goal:** Ungrouped Tasks
- **Ran:** 2026-10-27 16:12 to 2026-10-27 16:13 (0m 29s)
- **Outcome:** done; committed [`5a0f7b5cb767`](https://github.com/wingware-dev/investaround/commit/5a0f7b5cb767dfadf955f17929c21a5b29fb2457)
- **Usage:** 1,809 input, 3,241 output, 265k cache read, 24k cache write (claude-haiku-5-5, claude-opus-5-5)

**Prompt**

> Running in Wing doesn't work:
> ￼ File "<project>/investaround/__main__.py", line 9, in <module>
>   from .app import create_app
>
> builtins.ImportError: attempted relative import with no known parent package
>
> [Tasks Manager, 2026-10-27 16:12] Manager: Wing runs investaround/__main__.py as a plain file, so its relative import fails. Add a small top-level launcher, e.g. run_investaround.py at the project root, that calls investaround.__main__.main(), and create it with create_tracked_file. Then set Wing's main_entry_point to it with project_set. Don't change investaround/__main__.py: `python -m investaround` must keep working. Check both ways start the server, using --no-browser --source fake on a spare port and a real HTTP request, then stop them. Mention the launcher in the README's Run section.

**Judgement calls**

1. **Launcher named run_investaround.py, at the project root**
   This is the name the Tasks Manager suggested. At the root the package imports without any sys.path changes.

**Summary**

> Added a top-level launcher so Wing can run the app:
> - New `run_investaround.py` at the project root calls `investaround.__main__.main()`. Wing ran `investaround/__main__.py` as a plain file, so its relative import failed.
> - Changed Wing's main entry point to the launcher. `investaround/__main__.py` is unchanged.
> - Added the launcher to the README's Run section.
> - Checked `python -m investaround` and `python run_investaround.py` (also run from another cwd) with `--no-browser --source fake` on spare ports. Each answered a real HTTP request with 200, then I stopped it.


## Tasks Manager

### Decisions

| Time | Change | Task | Detail |
|---|---|---|---|
| 2026-10-27 15:20 | annotate_task | T1 new-investing-want-software | Added a note: Manager: the project is empty apart from .venv and an empty requirements.txt, so plan this before building it. Pick a free price source that needs no account or API key, and check it really works for both daily current prices and historical ranges. Plan the app's form (for example a lo |
| 2026-10-27 15:20 | queue_assign | T1 new-investing-want-software | Queued in Research: Paper investing app |
| 2026-10-27 15:23 | escalate | T1 new-investing-want-software | Passed to you on the Questions tab |
| 2026-10-27 15:24 | propose_tasks | T2 app-foundation | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T3 ui-harness-and-shots | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T4 yahoo-price-source | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T5 analytics-engine | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T6 portfolio-builder-watch | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T7 history-backtest-page | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T8 example-portfolios | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T9 learn-strategy-lab | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T10 home-dashboard-docs | Filed Ready from the plan of T1 new-investing-want-software (691d1322) |
| 2026-10-27 15:24 | propose_tasks | T1 new-investing-want-software | Split its plan into 9 Ready tasks |
| 2026-10-27 15:24 | queue_assign | T2 app-foundation | Queued in App foundation |
| 2026-10-27 15:30 | annotate_task | T4 yahoo-price-source | Added a note: Manager, from T2 app-foundation (9fa9251e): in investaround/app.py, implement `_make_yahoo(app)` to return CachingPriceSource(YahooPriceSource(...)) with the cache under app.config['DATA_DIR'], and set DEFAULT_PRICE_SOURCE = 'yahoo'. Nothing else in app.py needs to change. Note that T3 |
| 2026-10-27 15:30 | annotate_task | T3 ui-harness-and-shots | Added a note: Manager, from T2 app-foundation (9fa9251e): build test apps with create_app({'DATA_DIR': tmp, 'PRICE_SOURCE': 'fake'}). For error-path tests, pass PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={...}). pytest is already configured (pyproject.toml sets pythonpath=['.']). Both installed C |
| 2026-10-27 15:31 | queue_assign | T4 yahoo-price-source | Queued in App foundation |
| 2026-10-27 15:31 | queue_assign | T3 ui-harness-and-shots | Queued in UI harness |
| 2026-10-27 15:31 | queue_assign | T5 analytics-engine | Queued in Analytics engine |
| 2026-10-27 15:34 | queue_assign | T8 example-portfolios | Queued in Example portfolios |
| 2026-10-27 15:37 | annotate_task | T7 history-backtest-page | Added a note: Manager, from T4 yahoo-price-source (ea97e03c): Yahoo's `close` is already split-adjusted, and `adjclose` only adds dividends. Use `adjclose` for total return. No split handling is needed. |
| 2026-10-27 15:37 | queue_assign | T6 portfolio-builder-watch | Queued in Portfolio builder |
| 2026-10-27 15:38 | annotate_task | T7 history-backtest-page | Added a note: Manager, from T5 analytics-engine (6cb78b44): use investaround.analytics: portfolio_value_series() and compare_to_benchmark(). Explain the ValueSeries' late_starts (holdings kept as cash until their first price) and no_data on the page. cagr and best/worst year are None for short range |
| 2026-10-27 15:38 | annotate_task | T9 learn-strategy-lab | Added a note: Manager, from T5 analytics-engine (6cb78b44): use investaround.analytics.strategies: buy_and_hold, rebalanced(period in REBALANCE_PERIODS), dollar_cost_average, and lump_sum_vs_dca, which returns lump, dca, difference and winner. Each StrategyResult has key, label, series and metrics.  |
| 2026-10-27 15:38 | propose_tasks | T12 interest-on-uninvested-cash | Proposed as a Draft |
| 2026-10-27 15:38 | queue_assign | T7 history-backtest-page | Queued in History page |
| 2026-10-27 15:38 | queue_assign | T9 learn-strategy-lab | Queued in Learn and strategy lab |
| 2026-10-27 15:39 | annotate_task | T10 home-dashboard-docs | Added a note: Manager, from T8 example-portfolios (5868efa4): as part of integration, change POST /examples/<id>/try (or the link in its "Added …" notice) to go to the new portfolio's own watch page from T6, not to /portfolios/. |
| 2026-10-27 15:39 | propose_tasks | T13 richer-example-fixtures | Proposed as a Draft |
| 2026-10-27 15:39 | mark_ready | T13 richer-example-fixtures | Made Ready as a follow-up of 'Paper investing app step 7: example portfolios gallery': Completes the accepted plan's example set (it called for 10 blue-chip stocks), which T8 could only partly build with the recorded fixtures. |
| 2026-10-27 15:40 | queue_assign | T13 richer-example-fixtures | Queued in Example portfolios |
| 2026-10-27 15:43 | annotate_task | T12 interest-on-uninvested-cash | Added a note: Manager: T7 history-backtest-page and T9 learn-strategy-lab are calling investaround.analytics right now. Add the cash rate as an optional keyword that defaults to 0%, so existing calls and results stay unchanged. Don't edit web/, templates/ or static/; the pages can offer the option l |
| 2026-10-27 15:43 | queue_assign | T12 interest-on-uninvested-cash | Queued in Analytics engine |
| 2026-10-27 15:44 | annotate_task | T10 home-dashboard-docs | Added a note: Manager, from T9 learn-strategy-lab (341d042b): link /learn/ (lessons) and /learn/lab (strategy lab) from the home dashboard's "start here" path. |
| 2026-10-27 15:44 | propose_tasks | T14 examples-in-strategy-lab | Proposed as a Draft |
| 2026-10-27 15:44 | mark_ready | T14 examples-in-strategy-lab | Made Ready as a follow-up of 'Paper investing app step 8: Learn and Strategies lab': Joins two features the plan built so a new investor can run the strategies on the examples the plan asked for. |
| 2026-10-27 15:44 | queue_assign | T14 examples-in-strategy-lab | Queued in Learn and strategy lab |
| 2026-10-27 15:45 | annotate_task | T10 home-dashboard-docs | Added a note: Manager, from T6 portfolio-builder-watch (b0a3ff12): for each portfolio's value, today's change and gain, call investaround.web.portfolios.value_portfolio(p, prices) instead of computing them again. |
| 2026-10-27 15:45 | propose_tasks | T15 store-purchase-prices | Proposed as a Draft |
| 2026-10-27 15:45 | propose_tasks | T18 regression-tests-paper-app | Proposed as a Draft |
| 2026-10-27 15:46 | propose_tasks | T19 cash-rate-option-in-pages | Proposed as a Draft |
| 2026-10-27 15:46 | mark_ready | T19 cash-rate-option-in-pages | Made Ready as a follow-up of 'Interest on uninvested cash': The user readied T12; without these follow-ups its cash rate can't be chosen anywhere in the app. |
| 2026-10-27 15:46 | propose_tasks | T20 irx-tbill-fixture | Proposed as a Draft |
| 2026-10-27 15:46 | mark_ready | T20 irx-tbill-fixture | Made Ready as a follow-up of 'Interest on uninvested cash': The user readied T12; without these follow-ups its cash rate can't be chosen anywhere in the app. |
| 2026-10-27 15:46 | queue_assign | T10 home-dashboard-docs | Queued in Home dashboard and docs |
| 2026-10-27 15:46 | queue_assign | T20 irx-tbill-fixture | Queued in Analytics engine |
| 2026-10-27 15:52 | annotate_task | T19 cash-rate-option-in-pages | Added a note: Manager, from T10 home-dashboard-docs (f91681c3): the strategy lab's "what this shows" text still says waiting money "earns nothing (0%)". Once the cash option exists, make that text match the chosen rate. The T-bill choice can use the ^IRX fixture that T20 irx-tbill-fixture recorded ( |
| 2026-10-27 15:52 | revise_task | T18 regression-tests-paper-app | Rewrote it: Covers the follow-ups that landed since, and T10's request for a full pass. |
| 2026-10-27 15:53 | queue_assign | T19 cash-rate-option-in-pages | Queued in Analytics and cash interest |
| 2026-10-27 15:58 | annotate_task | T15 store-purchase-prices | Added a note: Manager: T19 cash-rate-option-in-pages is changing web/history.py, web/learn.py and their screenshots at the same time, so stay out of those files. Portfolios saved without start prices must still load, so make the new fields optional in storage. |
| 2026-10-27 15:58 | queue_assign | T15 store-purchase-prices | Queued in Portfolio builder |
| 2026-10-27 16:01 | mark_ready | T18 regression-tests-paper-app | Made Ready as a follow-up of 'Paper investing app step 1: foundation, contracts and app...': Full unit and UI test pass that T6, T7, T10 and T15 asked for, now that the plan steps and their follow-ups are in. |
| 2026-10-27 16:01 | queue_assign | T18 regression-tests-paper-app | Queued in Research: Regression tests |
| 2026-10-27 16:11 | answer_on_review | T22 run-set-main-entry | Answered and moved to Review: The main entry point is already set to investaround/__main__.py, so Wing's Debug or Run (with no other file chosen) starts the app at http://127.0.0.1:8765/ and opens it in your browser. From a terminal, run `.venv/bin/python -m investaround`. The README's Run section l |
| 2026-10-27 16:12 | annotate_task | T23 running-wing-doesn-work | Added a note: Manager: Wing runs investaround/__main__.py as a plain file, so its relative import fails. Add a small top-level launcher, e.g. run_investaround.py at the project root, that calls investaround.__main__.main(), and create it with create_tracked_file. Then set Wing's main_entry_point to  |
| 2026-10-27 16:12 | queue_assign | T23 running-wing-doesn-work | Queued in Wing run launcher |

## What went wrong

- 2026-10-27 15:37 **T5 analytics-engine**: The Manager redirected the worker: From T4 yahoo-price-source, verified on AAPL's 2020 4:1 split: Yahoo's `close` is already split-adjusted, and `adjclose` only adds dividends on top. So use `adjclose` for total return, and the analytics need no split handling of their own.
- 2026-10-27 15:39 **T7 history-backtest-page**: The Manager redirected the worker: From T8 example-portfolios (just finished): the Examples page links "See how it would have done" to /history/?example=<id>. Have the history page read that parameter and preload the example's holdings with investaround.web.examples.get_example(id). That function...

## Tasks not run

- T11 dca-money-weighted-return (pending): Money-weighted return (IRR) for DCA results
- T16 history-late-start-markers (pending): Mark late starts on the history chart
- T17 history-yearly-returns (pending): Year-by-year returns on the history page
- T21 site-wide-price-status-banner (pending): Site-wide price-source status banner

## Other commits in the run's window

- [`2a570968be33`](https://github.com/wingware-dev/investaround/commit/2a570968be338ef532bec14603ce25ab8e2e0392) Initial commit

