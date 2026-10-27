# dossier-framework

A reusable framework for building a sourced, graded **historical evidence dossier** on any historical or public subject — modelled on the structure of [historical-evidence-for-john-the-baptist](https://github.com/sybil-solutions/historical-evidence-for-john-the-baptist) (structure only; none of its content is copied).

Each dossier has: a subject config, numbered sources (S01…), graded claims (C01…) that must cite sources, a timeline, a generated bibliography, a chaptered report with an "establishes / does not establish" table, and `collections/` for mirrored public-domain texts. Copyrighted work is linked, never copied.

## Quick start (Python 3.11+, no dependencies; Windows/macOS/Linux)
```sh
python tools/new_dossier.py --subject "Hypatia of Alexandria" --period "c. 355-415 CE" --alias "Hypatia"
python tools/new_dossier.py add-source dossiers/hypatia-of-alexandria --title "Socrates Scholasticus, Ecclesiastical History 7.15"
python tools/new_dossier.py add-claim  dossiers/hypatia-of-alexandria --claim "Hypatia was killed by a Christian mob in 415"
python tools/add_source.py dossiers/hypatia-of-alexandria https://example.org/article --reliability B   # metadata + Wayback copy
python tools/validate.py dossiers/hypatia-of-alexandria --strict --write-summary --write-bibliography --report
python tools/build_site.py --all && python tools/check_links.py
```
New subjects: `python tools/new_dossier.py --subject "..." --kind person|event|place|object|movement|topic` copies a coverage checklist.
Contributing (identity, hooks, merging locally): **[CONTRIBUTING.md](CONTRIBUTING.md)**.
Then follow **[GUIDE.md](GUIDE.md)** (includes an agent prompt). Read **[ETHICS.md](ETHICS.md)**: not for private individuals.

## Layout
| Path | Purpose |
|---|---|
| `templates/` | subject.toml, source, claim, timeline, contradictions, bibliography, chapter and summary templates; `checklists/<kind>.md` |
| `tools/new_dossier.py` | Scaffold a dossier; add numbered sources/claims |
| `tools/validate.py` | Every claim graded and cited; every `[Sxx]` resolves; reliability A/B/C and type set; paywalled sources archived; confident grades need 2+ sources; no claim-ID gaps; timeline dates parse and run in order; contradiction register and checklist resolve. `--report` writes coverage.md |
| `tools/renumber.py` | Close C/S ID gaps and rewrite every reference |
| `tools/check_links.py` | Internal links/anchors in `site/`; `--external` checks every source url and suggests Wayback copies |
| `tools/add_source.py` | Capture a URL as the next S-number: metadata from the page, reliability, Wayback `archived:` copy |
| `tools/build_site.py` | Render a dossier into `site/<slug>/` (stdlib only): chapters, claims, sources, timeline, contradictions, full-text search, print/PDF page, sitemap and Open Graph tags. `--all` builds every dossier plus `site/index.html` |
| `tests/` | pytest suite incl. headless-browser filter and search tests (`pip install -r requirements-dev.txt`) |
| `site/` | Built reading sites |
| `dossiers/` | Generated dossiers |
| `ci/*.yml` | GitHub Actions workflows (validate, Pages, link rot); copy to `.github/workflows/` once the token has the `workflow` scope |
| `.githooks/` | pre-commit/pre-push guards (noreply identity, strict validation, fresh site, links); see CONTRIBUTING.md |

## Grades
strong · widely-accepted · probable · disputed · unproved · unsupported · false · unassessed (see GUIDE.md).

## Credits
The structure and method of this framework (numbered sources, chaptered dossier, graded "establishes / does not establish" findings, mirrored public-domain collections with metadata sidecars, and "link, never copy" for copyrighted scholarship) are adapted from **[Historical Evidence for John the Baptist](https://github.com/sybil-solutions/historical-evidence-for-john-the-baptist)** by **[Sybil Solutions](https://github.com/sybil-solutions)**. No text or code was copied from that project.

## License
No license has been chosen yet. The project that inspired it doesn't publish one either.
