"""Shots of the "What if?" history page."""

from tools.shots import shot


def _run(page, query):
    page.goto("/history/?" + query)
    page.locator("#history-chart").wait_for()
    page.wait_for_function("() => !!Chart.getChart(document.getElementById('history-chart'))")


@shot("20-history-10y", "What if? page: the Three-fund example over 10 years against the S&P 500")
def history_10y(page, live):
    _run(page, "example=three-fund&range=10y")


@shot("21-history-2008", "What if? page: the 2008 crash, with VXUS starting late and its waiting cash "
                         "earning Treasury bill rates")
def history_2008(page, live):
    _run(page, "example=three-fund&range=2008&cash=tbill")
