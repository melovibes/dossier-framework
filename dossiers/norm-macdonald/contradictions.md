# Contradiction register

Where sources disagree on a fact, log it here instead of silently picking one.
Each row names the question, every position with its sources, the current
resolution (start with **Resolved:** or **Open:**), and the claims it affects.
`tools/validate.py` checks that every row cites at least two existing sources
and at least one existing claim, and that every claim graded `disputed` appears here.

| ID | Question | Positions | Resolution | Claims |
|---|---|---|---|---|
| X01 | Birth year | October 17, 1959 [S01] [S02] [S05]. 1963, the year he gave for decades, still in The Canadian Encyclopedia [S03] and implied by EW calling him 34 in 1998 [S07]. | **Resolved:** 1959. CBC corrected its own 1963 error and the Globe says he "insisted" on 1963 [S02]. | (C01), (C02) |
| X02 | When was the cancer diagnosed? | About nine years before his death, i.e. c. 2012 [S04] [S05]. 2013 [S02] [S52]. | **Resolved:** 2013, from two independent sources including his producing partner; "nine years" looks like rounding. No medical record seen. | (C18), (C50) |
| X03 | When was *Nothing Special* taped? | Summer 2020 [S19] [S18]. Early 2020 [S22]. | **Resolved:** June 28, 2020, the day before a stem-cell transplant [S52]. | (C19) |
| X04 | Where did he die? | Los Angeles [S01]. Pasadena [S29]. City of Hope, where he spent his last six weeks [S52]. | **Resolved (metro level):** City of Hope's main campus is in Duarte, consistent with "Los Angeles" and "Pasadena" as metro labels. "Duarte" is inferred; no death record checked. | (C29) |
| X05 | Why was he removed from Weekend Update in 1998? | His O.J. Simpson jokes, Ohlmeyer being Simpson's friend [S09] [S11] [S10]. Ratings and a creative plateau, per Ohlmeyer's denial [S08]. Hosting the ESPYs as a trigger [S07]. | **Open:** the O.J. account has the most first-hand support (head writer Jim Downey) but Ohlmeyer denied it on record. | (C08), (C09) |
