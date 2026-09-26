from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@dashboard_bp.get("/dashboard")
def home():
    return render_template("dashboard.html")
