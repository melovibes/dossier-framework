# Research guide (for a person or an AI agent)

Read ETHICS.md first. If the subject is a private individual, stop.

## Workflow
1. **Configure.** `python tools/new_dossier.py --subject "Name" --kind person|event|place|object|movement|topic`. Fill in `subject.toml`: aliases, period, scope, research questions. Set `public_subject_confirmed = true` only once the subject is historical or public.
2. **Survey the evidence.** List what survives before arguing anything. Walk `checklist.md` item by item and note where each will be covered. Capture each web source with `python tools/add_source.py <dossier> <url> --reliability A|B|C` (metadata plus a Wayback copy), or `new_dossier.py add-source` for offline works. Prefer primary sources; record how far each is from the subject in time and dependence.
3. **Mirror public-domain texts** into `collections/<name>/` with a `_meta/<slug>.json` (title, source_url, license, fetched). Link everything else.
4. **Extract claims.** One file per claim (`add-claim`), each citing at least one source and carrying a grade.
5. **Build the timeline** — every row cites sources.
6. **Write chapters** in `dossier/`, one per research question. Every factual paragraph ends with `[Sxx]` citations. Leave gaps visible; say what the evidence does not establish.
7. **Validate** with `python tools/validate.py <dossier> --strict --write-summary --write-bibliography --report` until it passes, then read `coverage.md` for thin chapters, single-source claims and checklist gaps.
8. **Record contradictions** in `contradictions.md` whenever sources disagree: what each says, which you prefer, and why.
9. **Build the reading site** with `python tools/build_site.py <dossier>` (or `--all`), which writes `site/<slug>/`. Open `site/<slug>/index.html` in a browser; no server is needed. It has a sidebar of contents, grade badges, clickable `[Sxx]`/`(Cxx)` links, claim and source cards, a timeline, a filter box (press `/`), dark mode and a mobile layout.

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

## Dates
Timeline rows and claim `date:` fields use one format so they sort and show their precision: `2018-09-11` (day), `2018-09` (month), `2018` (year), `1970s` or `mid-2010s` (decade), `c. 1992` (circa), and `355 BCE`. Join ranges with `–` (`1993–1998`, `1992–93`). validate.py rejects dates it can't parse and warns when timeline rows are out of order.

## Contradictions

When sources disagree on a fact (a date, a place, a cause), add a row to `contradictions.md`: the question, each position with its sources, a resolution starting **Resolved:** or **Open:**, and the affected claims. Don't silently pick one. Every claim graded `disputed` must appear there; the validator enforces this and the site renders it as the Contradictions page.

## Source reliability
Every source carries `reliability:`.
| Grade | Meaning |
|---|---|
| `A` | Major outlet with named author, scholarly work, or first-hand primary record |
| `B` | Reputable but limited: single critic, trade/regional outlet, partisan, or the subject's own account |
| `C` | Tertiary or fan-maintained (wikis, transcripts sites, databases); use for wording, never for contested facts |

The validator enforces this. A `strong` or `widely-accepted` claim needs two or more sources. A `strong` claim can't rest only on `C` or `reference` sources. Paywalled hosts need an `archived:` copy, and claim IDs must have no gaps (`tools/renumber.py`).

## Research playbook (lessons from the Norm Macdonald run)
1. **Checklist first.** Fill `checklist.md` before writing. Most gaps found after the first draft were checklist items (awards, faith, controversies, finances).
2. **Two independent sources for anything confident.** Syndicated copies and obituaries quoting the same wire count once.
3. **Check who said a quote.** A widely shared "$400,000, three times" gambling quote was Dana White's, not the subject's. Find the original interview before using any quote.
4. **Self-reports are labelled.** Money, counts and dates the subject gave are "his own account" and graded no higher than `probable` unless corroborated.
5. **Paywalls.** Use `tools/add_source.py` (it records a Wayback copy). If a page blocks fetching, look for a syndicated copy (for example, the Washington Post via the National Post) and cite both.
6. **Replace tertiary sources.** Wikipedia and fan wikis are leads, not citations. Follow them to the primary or news source.
7. **Resolve disagreements explicitly.** Record them in `contradictions.md`, and regrade the losing claim (`unsupported` or `false`) rather than deleting it.
8. **Controversies:** quote reputable reporting directly, give the subject's response, and add no commentary.
9. **Privacy:** give cities or regions only, keep living relatives to published basics, and leave out rumors (ETHICS.md).
10. **Finish:** run `--strict --report`, build, check links and run the tests, then commit with a noreply identity and merge locally (CONTRIBUTING.md).

## Agent prompt
> You are compiling an evidence dossier on {subject} ({kind}) using dossier-framework. Read ETHICS.md, GUIDE.md and CONTRIBUTING.md first and follow them exactly.
> 1. Scaffold with `tools/new_dossier.py --kind {kind}`. Fill `checklist.md` with the chapter that will cover each item, or `n/a` plus a reason.
> 2. Research with web search. Capture every source with `tools/add_source.py`, setting `--reliability` honestly. Never fabricate a citation, URL or quote, and verify who said every quote.
> 3. Write claims (two or more independent sources for strong or widely-accepted), timeline rows with precise dates, and chapters where every factual paragraph ends in [Sxx] citations. Label self-reported figures and record conflicts in `contradictions.md`.
> 4. Loop `tools/validate.py <dossier> --strict --write-summary --write-bibliography --report` until it shows 0 errors and 0 warnings. Fix the evidence, not the rules.
> 5. Run `tools/build_site.py --all`, `tools/check_links.py site` and `python -m pytest -q`.
> 6. Report: what the evidence establishes and doesn't, source and claim counts by grade, single-source claims, and open questions.
