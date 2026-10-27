"""Shots of the example portfolios gallery."""

from tools.shots import shot


@shot("30-examples", "Example portfolios gallery with mini growth charts")
def examples(page, live):
    page.goto("/examples/")
    page.locator("canvas[data-example]").last.wait_for()
