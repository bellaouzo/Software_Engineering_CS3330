# Using the auth helpers in routes

Copy these patterns when a route needs a logged-in user or a database query.
The helpers live in `auth_helpers.py` and `supabase_client.py` at the repo root.

## Rules

1. Put `@require_login` (or `@require_staff`) **directly under** the route
   decorator. Order matters: the route decorator must be on top.
2. For any query made on a user's behalf, call `get_user_client()`. It acts as
   the logged-in user, so Row-Level Security applies. Never use the service-role
   key to get around RLS.
3. Use `get_supabase_client()` only when nobody is logged in (login, register).
4. The logged-in user's id is `session["user_id"]`. Don't read the tokens in the
   session yourself. `get_user_client()` handles them.
5. Supabase calls go in the route file, never in a template.

## Imports

```python
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from supabase import PostgrestAPIError

from auth_helpers import require_login, require_staff
from supabase_client import get_user_client
```

## Logged-in page that reads rows

```python
@tickets_bp.get("/tickets")
@require_login
def list_tickets():
    tickets = get_user_client().table("tickets").select("*").execute().data
    return render_template("tickets.html", tickets=tickets)
```

RLS already limits what comes back: requesters get their own tickets, staff get
all of them. Don't add your own filter to "enforce" it.

## Insert a row as the logged-in user

```python
@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
@require_login
def new_ticket():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Add a title before submitting the ticket.")
            return render_template("new_ticket.html"), 400
        get_user_client().table("tickets").insert(
            {"title": title, "created_by": session["user_id"]}
        ).execute()
        return redirect(url_for("tickets.list_tickets"))
    return render_template("new_ticket.html")
```

The tickets insert policy requires `created_by` to equal the logged-in user's id,
so always set it from `session["user_id"]`, never from the form.

## Staff-only route

```python
@tickets_bp.post("/tickets/<ticket_id>/status")
@require_staff
def update_ticket_status(ticket_id):
    ...
```

Non-staff users are sent to the dashboard with a message. `@require_staff`
already checks the login, so don't stack `@require_login` on top of it.

## Handling errors

Database calls can fail. Catch the error and show a plain-English message
instead of letting Flask show a raw error page:

```python
try:
    ticket = get_user_client().table("tickets").select("*").eq("id", ticket_id).single().execute().data
except PostgrestAPIError:
    flash("Ticket not found.")
    return redirect(url_for("tickets.list_tickets"))
```

`.single()` raises when no row comes back. That includes a ticket id that doesn't
exist and one RLS hides from the user.

## What not to do

- Don't write your own login check, session handling, or token refresh.
- Don't call `create_client()` directly. Use the two functions above.
- Don't keep or copy the access token anywhere else.

## Updating this file

If the helpers change (new decorator, new argument, new rule), update this guide
and the matching bullet in `AGENTS.md` in the same branch.
