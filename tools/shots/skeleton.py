"""Shots of the app skeleton, before features fill it in."""

from tools.shots import shot


@shot("01-home-skeleton", "Home page with the full navigation and footer")
def home_skeleton(page, live):
    page.goto("/")
    page.get_by_role("heading", level=1).wait_for()
