"""Build, edit and watch paper portfolios (filled in by step 5)."""

from flask import Blueprint, render_template

bp = Blueprint("portfolios", __name__, url_prefix="/portfolios")


@bp.get("/")
def index():
    return render_template("portfolios/index.html")
