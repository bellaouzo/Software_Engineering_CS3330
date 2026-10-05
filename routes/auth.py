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

# Supabase error code -> (message shown to the user, HTTP status).
LOGIN_ERRORS = {
    "invalid_credentials": ("Wrong username or password.", 401),
}
REGISTER_ERRORS = {
    "user_already_exists": ("That username is taken. Pick another one.", 409),
    "email_exists": ("That username is taken. Pick another one.", 409),
    "weak_password": ("That password is too weak. Use a longer one.", 400),
}
UNKNOWN_ERROR = ("Something went wrong on our end. Try again in a moment.", 502)
UNREACHABLE_ERROR = ("Could not reach the database. Try again in a moment.", 503)


def _username_to_email(username):
    return f"{username}@{PLACEHOLDER_EMAIL_DOMAIN}"


def _redirect_to_dashboard():
    return redirect(url_for("dashboard.home"))


def _login_error(message, status):
    flash(message)
    return render_template("login.html"), status


def _register_error(message, status):
    flash(message)
    return render_template("register.html"), status


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return _redirect_to_dashboard()
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    if not username or not password:
        return _login_error("Enter your username and password.", 400)
    try:
        result = get_supabase_client().auth.sign_in_with_password(
            {"email": _username_to_email(username), "password": password}
        )
    except AuthApiError as error:
        return _login_error(*LOGIN_ERRORS.get(error.code, UNKNOWN_ERROR))
    except (AuthError, SupabaseException):
        return _login_error(*UNREACHABLE_ERROR)
    session["user_id"] = result.user.id
    session["access_token"] = result.session.access_token
    session["refresh_token"] = result.session.refresh_token
    return _redirect_to_dashboard()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return _redirect_to_dashboard()
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not username or not password:
        return _register_error("Enter your name, username, and password.", 400)
    if not USERNAME_PATTERN.match(username):
        return _register_error(
            "Usernames are 3 to 30 characters: letters, numbers, and underscores only.", 400
        )
    try:
        get_supabase_client().auth.sign_up(
            {
                "email": _username_to_email(username),
                "password": password,
                "options": {"data": {"name": name, "username": username}},
            }
        )
    except AuthApiError as error:
        return _register_error(*REGISTER_ERRORS.get(error.code, UNKNOWN_ERROR))
    except (AuthError, SupabaseException):
        return _register_error(*UNREACHABLE_ERROR)
    flash("Account created. Log in with your new username.")
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("You are logged out.")
    return redirect(url_for("auth.login"))
