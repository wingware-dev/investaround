"""Smoke tests: the app comes up in a real browser and the nav works."""

import subprocess
import sys
from pathlib import Path

import pytest

from tests.ui.harness import start_app

ROOT = Path(__file__).resolve().parents[2]

NAV = [
    ("Home", "/"),
    ("My portfolios", "/portfolios/"),
    ("What if?", "/history/"),
    ("Examples", "/examples/"),
    ("Learn", "/learn/"),
]


def test_home_loads(page):
    page.goto("/")
    assert page.title() == "Home · investaround"
    assert page.get_by_role("heading", level=1).is_visible()
    assert page.get_by_text("Pretend money only").is_visible()
    assert "made-up sample data" in page.locator("footer").inner_text()


def test_nav_reaches_every_section(page, live_app):
    page.goto("/")
    nav = page.get_by_role("navigation", name="Main")
    for label, path in NAV:
        nav.get_by_role("link", name=label, exact=True).click()
        page.wait_for_url(live_app.url + path)
        current = nav.locator('[aria-current="page"]')
        assert current.count() == 1
        assert current.inner_text() == label


def test_brand_link_goes_home(page, live_app):
    page.goto("/learn/")
    page.get_by_role("link", name="investaround").click()
    page.wait_for_url(live_app.url + "/")


def test_unknown_page_shows_not_found(page):
    resp = page.goto("/nowhere")
    assert resp.status == 404
    assert page.get_by_text("Page not found").first.is_visible()


def test_apps_run_side_by_side(tmp_path):
    a = start_app(tmp_path / "a")
    b = start_app(tmp_path / "b")
    try:
        assert a.url != b.url
        assert a.store.path != b.store.path
    finally:
        a.stop()
        b.stop()


def test_shot_registry():
    from tools.shots import REGISTRY, load_all, shot

    shots = load_all()
    assert "01-home-skeleton" in shots
    assert list(shots) == sorted(shots)
    with pytest.raises(ValueError):
        shot("home")
    with pytest.raises(ValueError):
        shot("01-home-skeleton")(lambda page, live: None)  # defined in another module
    assert REGISTRY["01-home-skeleton"].module == "tools.shots.skeleton"


def test_shots_tool_writes_png(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "shots.py"), "--out", str(tmp_path), "01-*"],
        capture_output=True, text=True, timeout=120, cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    png = tmp_path / "01-home-skeleton.png"
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_shots_tool_rejects_unknown_name(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "shots.py"), "--out", str(tmp_path), "99-nope"],
        capture_output=True, text=True, timeout=60, cwd=tmp_path,
    )
    assert proc.returncode != 0
    assert "No shot matches 99-nope" in proc.stderr
