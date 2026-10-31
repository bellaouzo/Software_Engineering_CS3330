import logging

from flask import Blueprint, flash, redirect, render_template, session, url_for
from supabase import AuthError, PostgrestAPIError, SupabaseException

from routes.tickets import TICKET_LIST_COLUMNS, TICKET_STATUSES
from supabase_client import get_user_client

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)

# Anything in these statuses still needs work. Resolved and Closed count as done.
OPEN_STATUSES = ["Submitted", "Acknowledged", "In Progress"]
# Max tickets shown in each dashboard list, the full list is on /tickets
RECENT_TICKET_LIMIT = 5

DB_ERROR = "Could not reach the database. Try again in a moment."
LOGIN_EXPIRED = "Your login expired. Log in again."


def _count_by_status(tickets):
    # Start every status at 0 so the staff tiles still show up when a status has no tickets
    counts = {status: 0 for status in TICKET_STATUSES}
    for ticket in tickets:
        if ticket["status"] in counts:
            counts[ticket["status"]] += 1
    return counts


def _load_dashboard():
    # Get the user's profile first, we need the role to know which dashboard to show
    client = get_user_client()
    profile = (
        client.table("profiles")
        .select("name, username, role")
        .eq("id", session["user_id"])
        .single()
        .execute()
        .data
    )
    is_staff = profile["role"] == "staff"
    query = (
        client.table("tickets")
        .select(TICKET_LIST_COLUMNS)
        .order("updated_at", desc=True)
    )
    # RLS already does this, but filter requesters to their own tickets anyway (same as F-004 fix)
    if not is_staff:
        query = query.eq("created_by", session["user_id"])
    return profile, is_staff, query.execute().data


@dashboard_bp.get("/")
@dashboard_bp.get("/dashboard")
def home():
    # Not logged in, just show the normal welcome page instead of kicking them to login
    if "user_id" not in session:
        return render_template("dashboard.html", profile=None)

    try:
        profile, is_staff, tickets = _load_dashboard()
    except AuthError:
        session.clear()
        flash(LOGIN_EXPIRED, "error")
        return redirect(url_for("auth.login"))
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not load dashboard")
        flash(DB_ERROR, "error")
        return render_template("dashboard.html", profile=None)

    # Tickets are already newest first, so slicing gives the most recent ones
    counts = _count_by_status(tickets)
    open_tickets = [t for t in tickets if t["status"] in OPEN_STATUSES]
    new_tickets = [t for t in tickets if t["status"] == "Submitted"]
    return render_template(
        "dashboard.html",
        profile=profile,
        is_staff=is_staff,
        counts=counts,
        total_count=len(tickets),
        open_count=len(open_tickets),
        open_tickets=open_tickets[:RECENT_TICKET_LIMIT],
        new_tickets=new_tickets[:RECENT_TICKET_LIMIT],
        recent_tickets=tickets[:RECENT_TICKET_LIMIT],
    )
