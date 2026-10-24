import logging
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from supabase import AuthApiError, AuthError, SupabaseException

from supabase_client import get_supabase_client

# Everything for logging in, signing up, and logging out
auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

# Matches the profiles_username_format_check constraint in the migrations.
USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")
# Supabase Auth needs an email, so each username maps to a placeholder address.
# Nothing is ever sent to it ("Confirm email" must stay off in Supabase). Hosted
# Supabase rejects reserved TLDs like .invalid, but accepts example.com.
PLACEHOLDER_EMAIL_DOMAIN = "example.com"
# Shown as helper text and used as the form's minlength. Keep it equal to
# "Minimum password length" in Supabase Auth (local config.toml uses 6); if the
# live project is stricter, Supabase still rejects short ones as weak_password.
MIN_PASSWORD_LENGTH = 6

# Supabase error code -> (message shown to the user, HTTP status).
LOGIN_ERRORS = {
    "invalid_credentials": ("Wrong username or password.", 401),
}
REGISTER_ERRORS = {
    "user_already_exists": ("That username is taken. Pick another one.", 409),
    "email_exists": ("That username is taken. Pick another one.", 409),
    "weak_password": ("That password is too weak. Use a longer one.", 400),
    "over_email_send_rate_limit": (
        "Too many sign-ups right now. Try again in a few minutes.",
        429,
    ),
}
# Fallbacks for errors we didn't plan for or when Supabase is down
UNKNOWN_ERROR = ("Something went wrong on our end. Try again in a moment.", 502)
UNREACHABLE_ERROR = ("Could not reach the database. Try again in a moment.", 503)


# Turns "zach" into "zach@example.com" for Supabase
def _username_to_email(username):
    return f"{username}@{PLACEHOLDER_EMAIL_DOMAIN}"


# Used after login and when someone already logged in hits /login or /register
def _redirect_to_dashboard():
    return redirect(url_for("dashboard.home"))


def _lookup_error(errors, error):
    """Picks the user message for a Supabase error, logging ones we don't map."""
    if error.code not in errors:
        logger.error("Unmapped Supabase auth error: code=%s status=%s message=%s",
                     error.code, error.status, error.message)
    return errors.get(error.code, UNKNOWN_ERROR)


# Shows the login page again with the error and keeps the username typed in
def _login_error(message, status, username=""):
    flash(message)
    return render_template("login.html", username=username), status


# Shows the sign up form, also passes the min password length for the hint
def _render_register(name="", username=""):
    return render_template("register.html", name=name, username=username,
                           min_password_length=MIN_PASSWORD_LENGTH)


def _register_error(message, status, name="", username=""):
    """Re-shows the form with the name and username kept (never the password)."""
    flash(message)
    return _render_register(name, username), status


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in, no reason to see the login page
    if "user_id" in session:
        return _redirect_to_dashboard()
    if request.method == "GET":
        return render_template("login.html")

    # Usernames are saved lowercase so lower it here too
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    if not username or not password:
        return _login_error("Enter your username and password.", 400, username)
    try:
        result = get_supabase_client().auth.sign_in_with_password(
            {"email": _username_to_email(username), "password": password}
        )
    except AuthApiError as error:
        return _login_error(*_lookup_error(LOGIN_ERRORS, error), username)
    except (AuthError, SupabaseException):
        return _login_error(*UNREACHABLE_ERROR, username)
    # Save who they are and their tokens so get_user_client() can act as them
    session["user_id"] = result.user.id
    session["access_token"] = result.session.access_token
    session["refresh_token"] = result.session.refresh_token
    return _redirect_to_dashboard()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Same as login, logged in users skip this page
    if "user_id" in session:
        return _redirect_to_dashboard()
    if request.method == "GET":
        return _render_register()

    # Check the form ourselves first so we can give a clear message
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    if not name or not username or not password:
        return _register_error("Enter your name, username, and password.", 400,
                               name, username)
    if not USERNAME_PATTERN.match(username):
        return _register_error(
            "Usernames are 3 to 30 characters: letters, numbers, and underscores only.",
            400, name, username,
        )
    if password != confirm_password:
        return _register_error("The passwords don't match. Type them again.", 400,
                               name, username)
    # name and username go in metadata, handle_new_user() copies them into profiles
    try:
        get_supabase_client().auth.sign_up(
            {
                "email": _username_to_email(username),
                "password": password,
                "options": {"data": {"name": name, "username": username}},
            }
        )
    except AuthApiError as error:
        return _register_error(*_lookup_error(REGISTER_ERRORS, error), name, username)
    except (AuthError, SupabaseException):
        return _register_error(*UNREACHABLE_ERROR, name, username)
    flash("Account created. Log in with your new username.")
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout")
def logout():
    # Wiping the session logs them out on our side
    session.clear()
    flash("You are logged out.")
    return redirect(url_for("auth.login"))
