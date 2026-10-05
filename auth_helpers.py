from functools import wraps

from flask import flash, redirect, session, url_for
from supabase import AuthError, SupabaseException

from supabase_client import get_user_client


def require_login(view):
    """Sends visitors who are not logged in to the login page.

    Put it under the route decorator: @tickets_bp.get("/tickets") then @require_login.
    """

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Log in to continue.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def require_staff(view):
    """Lets only staff through. Everyone else goes back to the dashboard.

    Checks the role on the user's profiles row, so it also covers the login check.
    """

    @wraps(view)
    @require_login
    def wrapped_view(*args, **kwargs):
        try:
            profile = (
                get_user_client()
                .table("profiles")
                .select("role")
                .eq("id", session["user_id"])
                .single()
                .execute()
            )
        except (AuthError, SupabaseException):
            session.clear()
            flash("Your login expired. Log in again.")
            return redirect(url_for("auth.login"))
        if profile.data["role"] != "staff":
            flash("Only staff can open that page.")
            return redirect(url_for("dashboard.home"))
        return view(*args, **kwargs)

    return wrapped_view
