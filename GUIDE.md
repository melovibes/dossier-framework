# Research guide (for a person or an AI agent)

Read ETHICS.md first. If the subject is a private individual, stop.

## Workflow
1. **Configure.** Fill in `subject.toml`: aliases, period, scope, research questions. Set `public_subject_confirmed = true` only once the subject is historical or public.
2. **Survey the evidence.** List what survives before arguing anything. Create one file per source: `python tools/new_dossier.py add-source <dossier> --title "..."`. Prefer primary sources; record how far each is from the subject in time and dependence.
3. **Mirror public-domain texts** into `collections/<name>/` with a `_meta/<slug>.json` (title, source_url, license, fetched). Link everything else.
4. **Extract claims.** One file per claim (`add-claim`), each citing at least one source and carrying a grade.
5. **Build the timeline** — every row cites sources.
6. **Write chapters** in `dossier/`, one per research question. Every factual paragraph ends with `[Sxx]` citations. Leave gaps visible; say what the evidence does not establish.
7. **Validate** with `python tools/validate.py <dossier> --write-summary --write-bibliography` until it passes.
8. **Build the reading site** with `python tools/build_site.py <dossier>`, which writes `site/<slug>/`. Open `site/<slug>/index.html` in a browser; no server is needed. It has a sidebar of contents, grade badges, clickable `[Sxx]`/`(Cxx)` links, claim and source cards, a timeline, a filter box (press `/`), dark mode and a mobile layout.

## Grading scale
| Grade | Meaning |
|---|---|
| `strong` | Multiple independent sources, broad scholarly agreement |
| `widely-accepted` | Most specialists accept it; some dependence among sources |
| `probable` | Better supported than not, but contested |
| `disputed` | Serious scholarship on both sides |
| `unproved` | A hypothesis without decisive evidence |
| `unsupported` | Claimed, but cited evidence does not show it |
| `false` | Evidence contradicts it |
| `unassessed` | Not graded yet (validation warns) |

## Rules
- Distinguish what a source says from what happened.
- Note independence: two sources copying a third count once.
- Record exact locators (book.chapter, page, URL anchor).
- Flag later tradition, relics, shrines and popular claims as such.
- No invented citations. If a source can't be verified, leave it out.

## Agent prompt
> You are compiling a historical evidence dossier on {subject} using dossier-framework. Follow GUIDE.md and ETHICS.md exactly. Use only published, verifiable sources; never fabricate a citation or URL. Create source files before claims, grade every claim, cite every factual paragraph, and run tools/validate.py until it passes. Report what the evidence does and does not establish.
