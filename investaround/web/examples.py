"""Example portfolios gallery (filled in by step 7)."""

from flask import Blueprint, render_template

bp = Blueprint("examples", __name__, url_prefix="/examples")


@bp.get("/")
def index():
    return render_template("examples/index.html")
