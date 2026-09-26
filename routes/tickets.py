from flask import Blueprint, flash, redirect, render_template, request, url_for

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.get("/tickets")
def list_tickets():
    return render_template("tickets.html", tickets=[])


@tickets_bp.route("/tickets/new", methods=["GET", "POST"])
def new_ticket():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Add a title before submitting the ticket.")
            return render_template("new_ticket.html"), 400
        flash("This ticket was not saved. The database is not connected yet.")
        return redirect(url_for("tickets.list_tickets"))
    return render_template("new_ticket.html")


@tickets_bp.route("/tickets/<ticket_id>", methods=["GET", "POST"])
def ticket_detail(ticket_id):
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Write a comment before sending it.")
            return render_template("ticket_detail.html", ticket_id=ticket_id), 400
        flash("This comment was not saved. The database is not connected yet.")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))
    return render_template("ticket_detail.html", ticket_id=ticket_id)
