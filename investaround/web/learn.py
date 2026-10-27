"""Lessons, glossary and strategy lab (filled in by step 8)."""

from flask import Blueprint, render_template

bp = Blueprint("learn", __name__, url_prefix="/learn")


@bp.get("/")
def index():
    return render_template("learn/index.html")
