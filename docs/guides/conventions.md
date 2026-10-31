# Code conventions

Summary in `AGENTS.md` > Key rules. Naming rules are in
`naming-conventions.md`; file size rules are in `file-size-and-splitting.md`.

## Pages: route + template

Routes are registered as **Blueprints**, not flat route files — each blueprint
(`auth_bp`, `tickets_bp`, `dashboard_bp`) is registered once in
`routes/__init__.py`. A "page" has two halves: the route function in
`routes/<name>.py` (back end) and the matching template in
`templates/<name>.html` (front end). Never put HTML in a routes file or Supabase
calls in a template.

Route functions handle both GET (show a form/page) and POST (process submitted
data) in one function, per Flask convention — don't split these into two routes.

## Talking to Supabase

- All ticket routes are wired to Supabase. Database errors are caught
  (`PostgrestAPIError`, `SupabaseException`, `AuthError`) and shown as a plain
  flash message; an expired login clears the session and goes to `/login`.
- Every `flash()` passes a category: `"success"` for things that worked
  ("Ticket submitted.") and `"error"` for anything that failed or was blocked.
  Templates read them with `get_flashed_messages(with_categories=true)`.
- The comments query on the ticket page joins `profiles(name, username, role)`,
  so a template can tell staff replies apart (`comment.profiles.role`).
- **Protecting routes and querying as the user:** put `@require_login` (or
  `@require_staff`) from `auth_helpers.py` under the route decorator. For any
  table query made on a user's behalf, use `get_user_client()` from
  `supabase_client.py` so RLS applies. Use `get_supabase_client()` only for
  calls with no logged-in user (login, register). Don't write your own session
  or token handling.

  ```python
  @tickets_bp.get("/tickets")
  @require_login          # directly under the route decorator
  def list_tickets():
      tickets = get_user_client().table("tickets").select("*").execute().data
      return render_template("tickets.html", tickets=tickets)
  ```

  Full examples (insert, staff-only, error handling) are in
  `auth-helpers-examples.md`.

## Login

Users log in with a **username and password**, not an email. Supabase Auth is
email-based, so `routes/auth.py` maps each username to a placeholder email
(`<username>@example.com`, never emailed) and passes the username in signup
metadata, where `handle_new_user()` copies it to `profiles.username`. Email
confirmation must stay **off** in Supabase Auth settings, since the placeholder
address can't receive mail. After login the Supabase `user_id`, `access_token`,
and `refresh_token` are stored in the Flask `session`. Live Supabase setup steps
are in `supabase-live-auth-setup.md`.

Registration asks for the password twice (`confirm_password`, checked in
`app.js` via `data-match-input` and again in `routes/auth.py`). A failed login
or registration re-renders the form with the name/username kept, never the
password. `MIN_PASSWORD_LENGTH` in `routes/auth.py` drives the password hint and
`minlength`; keep it equal to the Supabase setting.

## Form validation (Req 6.1)

Each form's rules are plain HTML attributes on the field (`required`,
`minlength`, `pattern`, `data-match-input`), plus `data-rule-message` for the
text shown when one of those rules is broken. `static/js/app.js` shows that
message in a `.field-error` under the field before the form is sent (it also
treats spaces-only as empty), and a `.field-hint` under a field shows its rule
up front. The server still checks everything. When the server rejects a form,
pass the typed values back to the template (never the password), like
`routes/auth.py` and `routes/tickets.py` do.

## Fixed values

- Ticket status values are exactly: `Submitted`, `Acknowledged`, `In Progress`,
  `Resolved`, `Closed` (`TICKET_STATUSES` in `routes/tickets.py`). Don't
  introduce new status strings without updating the requirements spreadsheet
  first.
- Ticket categories (Plumbing, Electrical, HVAC, Furniture, Cleaning, Other) are
  the `TICKET_CATEGORIES` list in `routes/tickets.py`.
- Roles are lowercase: `requester`, `staff`.

## Front end

- Raw HTML/CSS/JS only — no frontend framework (React, Vue, etc.) and no CSS
  framework or library (Bootstrap, Pico.css, Tailwind, etc.). Our own CSS lives
  in `static/css/app.css`.
- `base.html` is the only layout; every page extends it.
- Ticket rows in a `.ticket-list` come from `templates/partials/_ticket_row.html`
  (used by `tickets.html` and the dashboard). Turn on extra details with
  `{% with show_owner=..., show_updated=... %}`.
- The dashboard (`/`) is role-based: logged-out visitors get the welcome page,
  requesters get `partials/dashboard/_requester.html`, staff get
  `partials/dashboard/_staff.html`.
- The app's display name is **Ticketing System** (header brand and every page
  title in `templates/`). Don't use location wording like "on campus".
- `base.html` shows each flash as `<p class="flash flash--success">` or
  `flash--error` (errors get `role="alert"`). A flash with no category falls
  back to the plain yellow `.flash`.
- Status badges come from `templates/partials/_status_badge.html`. It adds a
  modifier from the status (`In Progress` → `status-badge--in-progress`), and
  each of the five statuses has its own color in `app.css`.
- Staff comments get a `<span class="role-tag">Staff</span>` next to the name
  (from `comment.profiles.role`).
- Phone styles (`@media (max-width: 640px)`) are the last section of `app.css`.
  Add new small-screen rules there. Long text (titles, descriptions, comments)
  uses `overflow-wrap: anywhere` so the page never scrolls sideways.

## Requirement IDs

When implementing a requirement, reference its ID from the requirements
spreadsheet in the commit message or PR description (e.g. "Implements 2.1.1").
