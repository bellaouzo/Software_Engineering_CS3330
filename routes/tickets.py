import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from supabase import AuthError, PostgrestAPIError, SupabaseException

from auth_helpers import require_login, require_staff
from supabase_client import get_user_client

tickets_bp = Blueprint("tickets", __name__)
logger = logging.getLogger(__name__)

# Must match the status values listed in AGENTS.md.
TICKET_STATUSES = ["Submitted", "Acknowledged", "In Progress", "Resolved", "Closed"]
TICKET_CATEGORIES = ["Plumbing", "Electrical", "HVAC", "Furniture", "Cleaning", "Other"]

DB_ERROR = "Could not reach the database. Try again in a moment."
LOGIN_EXPIRED = "Your login expired. Log in again."


def _expired_login():
    session.clear()
    flash(LOGIN_EXPIRED)
    return redirect(url_for("auth.login"))


def _get_role():
    """Returns the logged-in user's role ("requester" or "staff")."""
    profile = (
        get_user_client()
        .table("profiles")
        .select("role")
        .eq("id", session["user_id"])
        .single()
        .execute()
    )
    return profile.data["role"]


def _render_new_ticket(status=200, **form):
    return (
        render_template("new_ticket.html", categories=TICKET_CATEGORIES, form=form),
        status,
    )


@tickets_bp.get("/tickets")
@require_login
def list_tickets():
    try:
        is_staff = _get_role() == "staff"
        query = (
            get_user_client()
            .table("tickets")
            .select("*, profiles(name, username)")
            .order("updated_at", desc=True)
        )
        # RLS should already hide other users' tickets; filter here too so a
        # misconfigured database can't leak them (F-004).
        if not is_staff:
            query = query.eq("created_by", session["user_id"])
        tickets = query.execute().data
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not load tickets")
        flash(DB_ERROR)
        tickets = []
        is_staff = False
    return render_template("tickets.html", tickets=tickets, is_staff=is_staff)


@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
@require_login
def new_ticket():
    if request.method == "GET":
        return _render_new_ticket()

    form = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "location": request.form.get("location", "").strip(),
        "category": request.form.get("category", ""),
    }
    if not form["title"]:
        flash("Add a title before submitting the ticket.")
        return _render_new_ticket(400, **form)
    if form["category"] not in TICKET_CATEGORIES:
        form["category"] = ""

    try:
        # created_by comes from the session, never the form (the insert policy checks it).
        created = (
            get_user_client()
            .table("tickets")
            .insert(
                {
                    "title": form["title"],
                    "description": form["description"] or None,
                    "location": form["location"] or None,
                    "category": form["category"] or None,
                    "created_by": session["user_id"],
                }
            )
            .execute()
        )
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        logger.exception("Could not create ticket")
        flash(DB_ERROR)
        return _render_new_ticket(503, **form)
    flash("Ticket submitted.")
    return redirect(url_for("tickets.ticket_detail", ticket_id=created.data[0]["id"]))


@tickets_bp.route("/tickets/<ticket_id>", methods=["GET", "POST"])
@require_login
def ticket_detail(ticket_id):
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Write a comment before sending it.")
        else:
            try:
                get_user_client().table("comments").insert(
                    {
                        "ticket_id": ticket_id,
                        "user_id": session["user_id"],
                        "text": text,
                    }
                ).execute()
            except AuthError:
                return _expired_login()
            except (PostgrestAPIError, SupabaseException):
                logger.exception("Could not add comment")
                flash(DB_ERROR)
            else:
                flash("Comment added.")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    try:
        client = get_user_client()
        ticket = (
            client.table("tickets")
            .select("*, profiles(name, username)")
            .eq("id", ticket_id)
            .maybe_single()
            .execute()
        )
        is_staff = _get_role() == "staff"
        if (
            ticket is None
            or ticket.data is None
            or (not is_staff and ticket.data["created_by"] != session["user_id"])
        ):
            flash("Ticket not found.")
            return redirect(url_for("tickets.list_tickets"))
        comments = (
            client.table("comments")
            .select("*, profiles(name, username)")
            .eq("ticket_id", ticket_id)
            .order("timestamp")
            .execute()
            .data
        )
    except AuthError:
        return _expired_login()
    except (PostgrestAPIError, SupabaseException):
        # A malformed id (not a UUID) also lands here.
        logger.exception("Could not load ticket %s", ticket_id)
        flash("Ticket not found.")
        return redirect(url_for("tickets.list_tickets"))
    return render_template(
        "ticket_detail.html",
        ticket=ticket.data,
        comments=comments,
        is_staff=is_staff,
        statuses=TICKET_STATUSES,
    )


@tickets_bp.post("/tickets/<ticket_id>/status")
@require_staff
def update_ticket_status(ticket_id):
    status = request.form.get("status", "")
    if status not in TICKET_STATUSES:
        flash("Pick a valid status.")
    else:
        try:
            get_user_client().table("tickets").update({"status": status}).eq(
                "id", ticket_id
            ).execute()
        except AuthError:
            return _expired_login()
        except (PostgrestAPIError, SupabaseException):
            logger.exception("Could not update status for ticket %s", ticket_id)
            flash(DB_ERROR)
        else:
            flash(f"Status changed to {status}.")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
