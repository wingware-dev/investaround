""""What if?" history backtests (filled in by step 6)."""

from flask import Blueprint, render_template

bp = Blueprint("history", __name__, url_prefix="/history")


@bp.get("/")
def index():
    return render_template("history/index.html")
