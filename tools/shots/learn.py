"""Shots of the Learn page and the Strategy lab."""

from tools.shots import shot


@shot("40-learn", "Learn page: disclaimer, lessons and glossary")
def learn(page, live):
    page.goto("/learn/")


@shot("41-strategy-lab", "Strategy lab: all at once vs spread out vs rebalanced, 60/40 over 10 years")
def strategy_lab(page, live):
    page.goto("/learn/lab?portfolio=preset:sixty-forty&range=10y&months=12&period=yearly")
    page.locator("#what-this-shows").wait_for()
