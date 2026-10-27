# Contributing

## Identity
Every commit must use a GitHub **noreply** address as author and committer, e.g.

    git config user.name  <user>
    git config user.email <id>+<user>@users.noreply.github.com

Install the hooks once per clone: `git config core.hooksPath .githooks`.
- `pre-commit` rejects non-noreply identities, runs `validate.py --strict` on every dossier, rebuilds `site/` when sources change (and stops if it's stale), and checks internal links.
- `pre-push` refuses to push any commit whose author or committer email is not a noreply address.

## Merging
**Merge locally, never with GitHub's merge button or the API.** A web merge stamps the merge commit with the account's primary email, which may be a personal address. Squash and rebase merges are disabled in the repo settings. Merge commits must stay enabled because GitHub requires at least one method, and pushing a local merge still auto-closes the PR as merged:

    git checkout main && git pull
    git merge --no-ff <branch> -m "Merge pull request #N from <owner>/<branch>"
    git push origin main

## Before pushing
    python tools/validate.py dossiers/<slug> --strict --write-summary --write-bibliography
    python tools/build_site.py --all
    python tools/check_links.py site
    python -m pytest -q
