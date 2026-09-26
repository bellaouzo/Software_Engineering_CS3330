from flask import Blueprint, flash, redirect, render_template, request, url_for

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Enter your email and password.")
            return render_template("login.html"), 400
        flash("Log in is not connected yet.")
        return redirect(url_for("auth.login"))
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Enter your name, email, and password.")
            return render_template("register.html"), 400
        flash("Account creation is not connected yet.")
        return redirect(url_for("auth.register"))
    return render_template("register.html")


@auth_bp.post("/logout")
def logout():
    flash("You are logged out.")
    return redirect(url_for("auth.login"))
