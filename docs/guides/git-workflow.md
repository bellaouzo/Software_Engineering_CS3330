# Git workflow: branches, PRs, merging

Summary in `AGENTS.md` > Working on a change. Tool prerequisites (Git, repo
access, `gh`) are in `setup-and-running.md`.

## Branch names

- Name branches by feature, not by sprint: `feature/be-auth-supabase`,
  `feature/fe-polish`, etc. — never `feature/sprint1-...`. A branch's name
  describes what it does, not when it was planned, since work sometimes runs
  past a sprint boundary and renaming a branch breaks its PR history.
- Keep branches small enough to realistically merge within one sprint. If a
  branch is dragging, split it rather than letting it run long.
- Open PRs early (even as a draft) rather than only once "done," so review can
  happen incrementally.
- `main` is protected — no direct pushes, PRs required.

## When to start a new branch vs. keep working on the current one

Because this is a team project, **new work gets its own branch** — never pile
unrelated changes onto whatever branch happens to be checked out.

- **Start a new branch** when the work is a different feature, requirement, bug,
  or area than the current branch (e.g. moving from auth to ticket comments).
  Branch from an up-to-date `main`, not from the previous feature branch.
- **Stay on the current branch** when the work is the same concept or clearly
  related (follow-up fixes, tweaks, review feedback, more commits toward the same
  requirement). Don't create a branch per small change — extra commits on the
  same branch are fine, and the open PR updates automatically.
- If unsure, ask: "Could this be reviewed and merged on its own?" If yes, it's
  probably a new branch.
- **AI agents:** before making changes, check the current branch (`git branch
  --show-current`). If you're on `main`, or the task is unrelated to the branch's
  purpose, tell the user and create a new `feature/...` branch instead of
  committing there. Never commit directly to `main`.

## Merging to `main` — the required workflow

`main` has a GitHub branch ruleset: changes can only land through a pull request
(PR) with the required approval, and the branch must be **up to date with the
latest `main`** before merging. Not everyone on the team is comfortable with
GitHub yet, so **when a user is ready to merge, don't assume they know the
steps. Offer to run each one for them, say in plain language what it does and
why, and show the result.** Run the commands yourself when the user agrees; if a
tool is missing, give them the manual instruction or link instead. **Always ask
for confirmation before the push and before opening the PR** — those affect the
shared repo.

1. **Commit your work** on your feature branch (message references the
   requirement ID, e.g. "Implements 2.1.1").
2. **Update your branch with the latest `main`** (the ruleset requires this):
   `git fetch origin`, then `git merge origin/main` (or `git rebase origin/main`
   if the team prefers). If there are conflicts, Git marks them in the files —
   help the user resolve them, then `git add` the files and finish the merge.
   Re-run the app to confirm it still works.
3. **Push the branch**: `git push -u origin <branch-name>` (first push) or
   `git push` afterwards.
4. **Open a pull request** on GitHub into `main` (the push output prints a link,
   or use the "Compare & pull request" button on the repo page, or
   `gh pr create`). Give it a clear title, mention the requirement ID(s) in the
   description, and say what changed and how to test it. Use **Draft** if it's
   not ready yet.
5. **Request a review** from your cross-functional testing pair (see
   `testing.md`).
6. **Respond to feedback** by committing to the same branch and pushing — the PR
   updates itself. Don't open a new PR.
7. **Merge** once it's approved and shows as up to date with `main`. If GitHub
   says the branch is out of date, repeat step 2 and push again.
8. **Clean up**: switch back to `main`, `git pull`, and delete the merged branch
   (`git branch -d <branch-name>`). Start the next piece of work from this
   fresh `main`.

If a push to `main` is rejected, that's the ruleset working as intended — it
means the work needs to be on a feature branch and go through a PR.
