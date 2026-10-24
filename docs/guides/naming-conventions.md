# Naming conventions

Summary in `AGENTS.md` > Key rules.

## Python (back end)

- Files/modules: `snake_case.py`. Functions/variables: `snake_case`, verb-first for
  functions (`create_ticket`, `get_ticket_by_id`, `update_ticket_status`).
- Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE` (e.g. `TICKET_STATUSES`).
- Blueprint objects: `<name>_bp` (`auth_bp`, `tickets_bp`).
- Route functions are named after the action (`list_tickets`, `new_ticket`,
  `ticket_detail`) — they double as `url_for` endpoints
  (`url_for("tickets.new_ticket")`, where the prefix is the short blueprint
  name, e.g. `Blueprint("tickets", ...)`), so keep them unique and descriptive.
- Private helpers get a leading underscore (`_require_staff()`).

## URLs

- Lowercase, plural nouns, hyphens (not underscores) for multiple words:
  `/tickets`, `/tickets/new`, `/tickets/<ticket_id>`.
- Ticket IDs are UUIDs, not integers — never use `<int:...>` converters for them.

## Templates (Jinja2)

- Files: `snake_case.html`, named after the page. `base.html` is the only layout.
- Partials live in `templates/partials/` and start with an underscore
  (`_ticket_card.html`, `_flash_messages.html`). Group related partials in
  subfolders when there are several (`templates/partials/tickets/_ticket_row.html`);
  see `file-size-and-splitting.md` > Folders and subfolders.
- Template variables: `snake_case`, matching the names passed from Python.
- Block names: short and lowercase (`title`, `content`, `scripts`).

## Database (Supabase/Postgres)

- Tables: plural `snake_case`. Columns: singular `snake_case`.
- Foreign keys: `<thing>_id`. Who/when columns: `created_by`, `*_at`
  (e.g. `updated_at`). Prefer `created_at` over `timestamp` for new columns.
- Migrations: `YYYYMMDDHHMMSS_descriptive_name.sql`, made by
  `supabase migration new` (see `database-schema.md`).
- Constraints, policies, triggers: descriptive names
  (e.g. `tickets_staff_update_policy`).

## CSS

- Classes: `kebab-case`, BEM-style when nesting is needed: `.ticket-card`,
  `.ticket-card__title`, `.ticket-card--urgent`.
- State classes use `is-`/`has-` prefixes (`.is-active`, `.has-error`).
- CSS variables: `--color-primary`, `--space-md`.

## JavaScript

- Variables/functions: `camelCase`. Constants: `UPPER_SNAKE_CASE`.
- Hook scripts to the DOM with `data-` attributes or `js-` prefixed classes
  (`.js-status-select`), never styling classes.
- Files: `kebab-case.js` (or `app.js`).

## Data values

- Statuses use the exact strings in `conventions.md`. Roles are lowercase:
  `requester`, `staff`.
- Other user-facing enum-like values (e.g. category) use Title Case.

## Branches

`feature/<area>-<what>`, named by feature, not by sprint. See
`git-workflow.md`.
