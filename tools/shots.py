"""Take the named screenshots in docs/shots/ by driving the app headlessly.

Shots are registered in tools/shots/<feature>.py (see tools/shots/__init__.py).
Each runs against its own fresh app (fake price source, temp data dir, OS
port) through the UI test harness, so this never touches ./data or the network.

  .venv/bin/python tools/shots.py                 # every shot
  .venv/bin/python tools/shots.py 01-home-skeleton '1*'
  .venv/bin/python tools/shots.py --list
  .venv/bin/python tools/shots.py --out /tmp/shots 01-home-skeleton
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.ui.harness import launch_browser, new_page, start_app  # noqa: E402
from tools.shots import Shot, load_all  # noqa: E402

DEFAULT_OUT = ROOT / "docs" / "shots"


def select(registry: dict[str, Shot], patterns: list[str]) -> list[Shot]:
    """Shots matching any of ``patterns`` (exact names or globs); all if none."""
    if not patterns:
        return list(registry.values())
    chosen = [s for s in registry.values() if any(fnmatch.fnmatchcase(s.name, p) for p in patterns)]
    unmatched = [p for p in patterns if not any(fnmatch.fnmatchcase(n, p) for n in registry)]
    if unmatched:
        raise SystemExit(f"No shot matches {', '.join(unmatched)}; see --list")
    return chosen


def take(shots: list[Shot], out_dir: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with sync_playwright() as pw:
        browser = launch_browser(pw)
        try:
            for s in shots:
                with tempfile.TemporaryDirectory(prefix="investaround-shot-") as tmp:
                    live = start_app(Path(tmp) / "data")
                    errors: list[str] = []
                    page = new_page(browser, live, errors)
                    try:
                        s.func(page, live)
                        path = out_dir / f"{s.name}.png"
                        page.screenshot(path=str(path), full_page=s.full_page)
                    finally:
                        page.context.close()
                        live.stop()
                if errors:
                    raise RuntimeError(f"Shot {s.name}: JavaScript errors in page: {errors}")
                print(f"wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
                written.append(path)
        finally:
            browser.close()
    return written


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("patterns", nargs="*", help="shot names or globs (default: all)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output dir (default {DEFAULT_OUT.relative_to(ROOT)})")
    ap.add_argument("--list", action="store_true", help="list registered shots and exit")
    args = ap.parse_args(argv)

    registry = load_all()
    if args.list:
        for s in registry.values():
            print(f"{s.name:28} {s.description}  [{s.module}]")
        return
    take(select(registry, args.patterns), args.out)


if __name__ == "__main__":
    main()
