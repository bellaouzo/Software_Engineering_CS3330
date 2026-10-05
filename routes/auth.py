import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from supabase import AuthApiError, AuthError, SupabaseException

from supabase_client import get_supabase_client

auth_bp = Blueprint("auth", __name__)

# Matches the profiles_username_format_check constraint in the migrations.
USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")
# Supabase Auth needs an email, so each username maps to a placeholder address.
# Nothing is ever sent to it.
PLACEHOLDER_EMAIL_DOMAIN = "tickets.invalid"


def _username_to_email(username):
    return f"{username}@{PLACEHOLDER_EMAIL_DOMAIN}"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Enter your username and password.")
            return render_template("login.html"), 400
        try:
            result = get_supabase_client().auth.sign_in_with_password(
                {"email": _username_to_email(username), "password": password}
            )
        except AuthApiError as error:
            if error.code == "invalid_credentials":
                flash("Wrong username or password.")
                return render_template("login.html"), 401
            flash("Could not log you in. Try again in a moment.")
            return render_template("login.html"), 502
        except (AuthError, SupabaseException):
            flash("Could not reach the database. Try again in a moment.")
            return render_template("login.html"), 503
        session["user_id"] = result.user.id
        session["access_token"] = result.session.access_token
        session["refresh_token"] = result.session.refresh_token
        return redirect(url_for("dashboard.home"))
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not username or not password:
            flash("Enter your name, username, and password.")
            return render_template("register.html"), 400
        if not USERNAME_PATTERN.match(username):
            flash("Usernames are 3 to 30 characters: letters, numbers, and underscores only.")
            return render_template("register.html"), 400
        try:
            get_supabase_client().auth.sign_up(
                {
                    "email": _username_to_email(username),
                    "password": password,
                    "options": {"data": {"name": name, "username": username}},
                }
            )
        except AuthApiError as error:
            if error.code in ("user_already_exists", "email_exists"):
                flash("That username is taken. Pick another one.")
                return render_template("register.html"), 409
            if error.code == "weak_password":
                flash("That password is too weak. Use a longer one.")
                return render_template("register.html"), 400
            flash("Could not create your account. Try again in a moment.")
            return render_template("register.html"), 502
        except (AuthError, SupabaseException):
            flash("Could not reach the database. Try again in a moment.")
            return render_template("register.html"), 503
        flash("Account created. Log in with your new username.")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("You are logged out.")
    return redirect(url_for("auth.login"))
