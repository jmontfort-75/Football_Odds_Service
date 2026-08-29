# Oddschecker GW3 Full-Coverage Spike

Second feasibility gate, answering: **does the proven single-fixture
Oddschecker approach (docs/oddschecker-gw3-feasibility-spike.md) scale
cleanly across all 10 Premier League GW3 fixtures, and how much useful
market coverage is actually available?**

## Executive verdict

**GW3 COVERAGE VIABLE WITH LIMITATIONS**

Fixture discovery and 1X2 extraction are 10/10, deterministic, and cheap
(~8s/fixture, sequential). The limitation is unchanged from the first
spike and now confirmed fixture-wide: this far ahead of kickoff (7-8 days),
Oddschecker has not yet priced Over/Under 2.5, BTTS, or team totals for
*any* of the 10 fixtures, and player markets (goalscorer, shots, shots on
target) are not present anywhere in this pipeline's reach for any fixture
checked. Both are genuine source-side data-availability gaps, not scraper
failures.

## Fixture list discrepancy (resolved before extraction)

Per spike instructions, a discrepancy was found and resolved before any
extraction was attempted. An initial WebFetch summary of a premierleague.com
news article mislabeled GW3 as the 12-14 September round (with fixtures
like Man Utd v Man City and Coventry v Brighton). This was cross-checked
against three independent sources and rejected:

- **mancity.com's own ticket page** states Coventry is Man City's "third
  league opponent of the new era" (i.e. GW3), kicking off **5 September 2026**.
- **ESPN's fixture schedule** for 4-6 September 2026 lists the same 10
  fixtures, matching pairing-for-pairing.
- **SportsMole's fixture list**, independently fetched, gives the identical
  10-fixture GW3 list for 4-6 September 2026.
- Re-fetching the original premierleague.com article and asking it to quote
  its own matchweek labels directly showed **the article contains no
  explicit matchweek numbers at all** -- the initial "GW3 = 12-14 Sept"
  answer was a summarization artifact of the fetch, not sourced from the
  page.

This also matches the kickoff timestamp already verified live in the first
spike (`2026-09-05T14:00:00Z` for Man City v Coventry). The 10-fixture list
below is the one used for the rest of this spike.

## GW3 fixture list (verified)

| # | Home | Away | Kickoff (UTC) | Oddschecker slug |
|---|------|------|----------------|-------------------|
| 1 | Ipswich Town | Liverpool | 2026-09-04T19:00Z | `ipswich-v-liverpool` |
| 2 | Newcastle United | AFC Bournemouth | 2026-09-05T11:30Z | `newcastle-v-bournemouth` |
| 3 | Brentford | Sunderland | 2026-09-05T14:00Z | `brentford-v-sunderland` |
| 4 | Brighton & Hove Albion | Leeds United | 2026-09-05T14:00Z | `brighton-v-leeds` |
| 5 | Fulham | Crystal Palace | 2026-09-05T14:00Z | `fulham-v-crystal-palace` |
| 6 | Manchester City | Coventry City | 2026-09-05T14:00Z | `man-city-v-coventry` |
| 7 | Nottingham Forest | Tottenham Hotspur | 2026-09-05T14:00Z | `nottingham-forest-v-tottenham` |
| 8 | Hull City | Aston Villa | 2026-09-05T16:30Z | `hull-v-aston-villa` |
| 9 | Everton | Manchester United | 2026-09-06T13:00Z | `everton-v-man-utd` |
| 10 | Arsenal | Chelsea | 2026-09-06T15:30Z | `arsenal-v-chelsea` |

## Fixture discovery results

All 10 slugs follow Oddschecker's own `{home}-v-{away}` convention and were
**independently confirmed** by fetching Oddschecker's live Premier League
index page (`/football/english/premier-league`) and finding all 10 slugs
embedded in its own upcoming-fixtures data -- discovery did not rely on
guessing alone.

| Fixture | Expected URL | Found | Page title / source name | Identity match |
|---|---|---|---|---|
| Ipswich Town v Liverpool | `.../ipswich-v-liverpool` | YES | Ipswich v Liverpool | YES |
| Newcastle United v AFC Bournemouth | `.../newcastle-v-bournemouth` | YES | Newcastle v Bournemouth | YES |
| Brentford v Sunderland | `.../brentford-v-sunderland` | YES | Brentford v Sunderland | YES |
| Brighton & Hove Albion v Leeds United | `.../brighton-v-leeds` | YES | Brighton v Leeds | YES |
| Fulham v Crystal Palace | `.../fulham-v-crystal-palace` | YES | Fulham v Crystal Palace | YES |
| Manchester City v Coventry City | `.../man-city-v-coventry` | YES | Man City v Coventry | YES |
| Nottingham Forest v Tottenham Hotspur | `.../nottingham-forest-v-tottenham` | YES | Nottingham Forest v Tottenham | YES |
| Hull City v Aston Villa | `.../hull-v-aston-villa` | YES | Hull v Aston Villa | YES |
| Everton v Manchester United | `.../everton-v-man-utd` | YES | Everton v Man Utd | YES |
| Arsenal v Chelsea | `.../arsenal-v-chelsea` | YES | Arsenal v Chelsea | YES |

**10/10 found, 10/10 identity-matched.** No wrong-fixture acceptances.

One implementation bug surfaced and was fixed during this spike: the first
identity-matching pass flagged Man City v Coventry and Everton v Man Utd as
**false-positive mismatches**, because Oddschecker labels fixtures with its
own short names ("Man City", "Man Utd") and the naive substring matcher
didn't see "Manchester City" and "Man City" as the same team. Fixed by
expanding known abbreviations (`manchester`→`man`, `united`→`utd`) before
comparison (`app/providers/oddschecker.py::_normalize_team_name`), then
re-verified against both fixtures and the full 10-fixture run. This is
exactly the class of bug Phase 2's "be strict, don't silently accept a
lookalike" instruction is meant to catch -- and this one initially
undershot rather than overshot, rejecting *correct* matches, which is the
safer failure direction.

## Core market coverage

| Fixture | Found | 1X2 | O/U 2.5 | BTTS | Home Team Total | Away Team Total |
|---|---|---|---|---|---|---|
| Ipswich v Liverpool | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Newcastle v Bournemouth | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Brentford v Sunderland | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Brighton v Leeds | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Fulham v Crystal Palace | YES | YES (25 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Man City v Coventry | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Nott'm Forest v Tottenham | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Hull v Aston Villa | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Everton v Man Utd | YES | YES (27 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |
| Arsenal v Chelsea | YES | YES (26 bks) | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET | NOT PRICED YET |

"NOT PRICED YET" here specifically means: the market's structure/entity
**is present** in the source's embedded payload (Oddschecker knows the
market exists and shows its accordion on the page), but it currently has
zero ACTIVE bookmaker prices -- distinct from "market/page does not exist",
which did not occur for any core market on any fixture. This mirrors the
first spike's single-fixture finding, now confirmed across all 10.

Markets found but not requested by this spike's core list (evidence the
extraction generalizes, per fixture): Correct Score, Half Time/Full Time,
and 58-63 other match-level market types (Asian Handicap, Winning Margin,
Total Corners, Clean Sheet, etc.) all present in the source's market
catalogue for every fixture checked, all similarly unpriced this far out.

## Player-market discovery

**Not found, for any fixture, via any route investigated.** Specifically:

1. **Embedded payload**: the same `bestOdds.markets.entities` JSON blob that
   holds all match-level markets was inspected in full for 3 fixtures (Man
   City v Coventry: 6 market types in the payload used for parsing;
   Arsenal v Chelsea: 60 types; Hull v Aston Villa: 64 types) -- **zero**
   goalscorer, shots, or shots-on-target market types appeared in any of
   them.
2. **Predictable sub-page URLs**: 8 plausible market-tab URL patterns were
   probed directly against the Man City v Coventry fixture (e.g.
   `.../man-city-v-coventry/anytime-goalscorer`, `.../player-shots`,
   `.../shots-on-target`, `.../to-score-2-or-more-goals`) -- **all returned
   HTTP 404**, including guesses for markets we *know* exist on the main
   page (`.../correct-score`, `.../both-teams-to-score` also 404'd),
   confirming match-level markets are not split across per-market URLs at
   all -- everything lives on the one fixture page.
3. **Site-wide specials hub** (`/football/specials/football-specials`) was
   checked as the most likely place for player-prop content: it returned
   200 but contains zero mentions of any GW3 team or "goalscorer" -- it's a
   transfer-betting/outrights hub, not a player-props page.

**Conclusion**: for GW3 fixtures at 7-8 days out, Oddschecker is not
currently exposing anytime-goalscorer, 2+ goals, shots, or shots-on-target
markets through any URL structure this investigation could find. This is
consistent with the site's general pattern of not pricing secondary/niche
markets until much closer to kickoff (matches the O/U 2.5 / BTTS finding
above) -- but per the spike's own time-boxing instruction, deeper reverse
engineering (e.g. searching for an internal API, or checking after
kickoff-week odds populate) was not pursued and would be the natural next
step if/when this gate is revisited closer to kickoff.

## Bookmaker coverage

1X2 bookmaker counts across the 10 fixtures: **[27, 26, 26, 26, 25, 26, 26,
26, 26, 26]** -- avg **26.0**, min **25** (Fulham v Crystal Palace), max
**27** (Everton v Man Utd). Coverage is tight and consistent: no fixture
had a materially degraded bookmaker panel. **780 individual bookmaker/
selection 1X2 prices** were captured in total across all 10 fixtures (avg
78 per fixture: 3 outcomes x ~26 bookmakers), all preserved individually
with no collapsing into consensus/average figures.

## Access / reliability

- **Playwright ran headless throughout** (`ODDSCHECKER_HEADLESS=true`, the
  repo default) -- no visible Chromium window was opened at any point.
- **10/10 fetches succeeded on the first attempt** -- zero retries, zero
  Cloudflare blocks, zero timeouts. Sequential fetching (one browser launch
  per fixture, `asyncio.sleep(4)` between fixtures) took **7.5-9.4s per
  fixture** (avg **7.98s**), ~95s total wall time for all 10 plus pacing
  delays.
- **No browser-session reuse was attempted** -- each fetch launches and
  closes its own Chromium instance (matching the first spike's approach).
  Reusing a single browser context across fixtures is a plausible future
  optimization but wasn't necessary for 10 sequential fetches to complete
  reliably.
- Access was **deterministic**: identical method, identical UA, identical
  wait strategy worked unmodified across all 10 fixtures with no
  fixture-specific tuning.

## Validation

Manually cross-checked against source values for 3 fixtures (not just Man
City v Coventry from the first spike):

| Fixture | Selection | Bookmaker | Source fractional | Parsed `raw_odds` | Our `decimal_odds` | Source `oddsDecimal` |
|---|---|---|---|---|---|---|
| Man City v Coventry | Man City (1X2) | bet365 | `2/9` | `2/9` | 1.222 | 1.222 |
| Man City v Coventry | Man City (1X2) | AK Bets | `2/9` | `2/9` | 1.222 | 1.22 (2dp rounding, as noted in the first spike) |
| Hull v Aston Villa | Aston Villa (1X2) | BetMGM UK | `9/10` | `9/10` | 1.9 | 1.9 |
| Hull v Aston Villa | Aston Villa (1X2) | Betfair | `5/6` | `5/6` | 1.833 | **1.89** |
| Arsenal v Chelsea | Arsenal (1X2) | William Hill | `7/10` | `7/10` | 1.7 | 1.7 |
| Arsenal v Chelsea | Arsenal (1X2) | Betfred | `4/6` | `4/6` | 1.667 | 1.67 |

All but one match the source's own decimal figure exactly (or within
expected 2dp/3dp rounding). **One real discrepancy was found and is
reported honestly rather than hidden**: Betfair's `5/6` on Aston Villa
converts to 1.833, but Betfair's own `oddsDecimal` field for that same bet
says 1.89 -- a ~3% gap too large to be rounding. This is most likely
Oddschecker's fractional and decimal feed fields updating asynchronously
(the price moved between the two snapshots), not a conversion bug on our
side -- `fractional_to_decimal("5/6")` is unambiguously 1.8333. This is
worth re-checking closer to kickoff if Betfair prices are relied on
specifically.

O/U 2.5, BTTS, and player-market prices could not be validated for any of
the 3 fixtures because none are currently priced by any bookmaker for any
GW3 fixture -- consistent with the coverage table above, not a validation
gap.

## Test results

**31 passed**, 0 failed (`backend/.venv/bin/python -m pytest -q`). 6 new
deterministic tests were added against the existing saved fixture
(`tests/fixtures/oddschecker_man_city_coventry.html`) covering: GW3 fixture
list shape, URL construction, identity matching (exact names, Oddschecker
abbreviations, and a deliberate mismatch), and the market-present-vs-
unpriced distinction. No live network calls are part of the automated
suite -- the 10-fixture live crawl is a manually-run script
(`backend/scripts/gw3_coverage_spike.py`), not wired into CI.

## Files created/modified

- `backend/app/providers/oddschecker.py` -- added `GW3_FIXTURES` (10-fixture
  catalog), `fixture_url()`, `fixture_identity_matches()`, `get_fixture_odds()`
  (generic version of the existing single-fixture fetch+parse pipeline).
  Existing `get_man_city_v_coventry_odds`, `parse_oddschecker_html`,
  `fetch_fixture_html`, and both exception classes are unchanged.
- `backend/tests/test_gw3_fixture_discovery.py` -- new, 6 tests.
- `backend/scripts/gw3_coverage_spike.py` -- new, the manual live-crawl
  runner used to produce this report's evidence.
- `backend/scripts/gw3_coverage_spike_output.json` -- new, full raw evidence
  (per-bookmaker prices, provenance, fetch timings) for all 10 fixtures.
- `docs/oddschecker-gw3-full-coverage-spike.md` -- this document.

No changes were made to `Dockerfile.backend`, `app/api/v1/routes.py`, the
frontend, CI workflows, or anything database/scheduler-related.

## Limitations

- **Unpriced ≠ broken.** Over/Under 2.5, BTTS, and team totals are
  genuinely not priced by any bookmaker yet for any of the 10 fixtures --
  the source's own DOM/JSON confirms this, it is not a parsing gap. This
  should be re-tested closer to kickoff (the first spike already flagged
  this as untested-over-time; it remains untested here too, since this
  spike ran on the same day, 7-8 days out).
- **Player markets are a genuine unknown, not a confirmed absence.** This
  spike time-boxed its search (embedded payload + 8 URL guesses + the
  specials hub) per its own scope instructions. It did not find them, but
  it also did not exhaustively search Oddschecker's full site map or
  network requests for an internal API that might serve them. Treat "not
  found" as "not found by this method in this time-box," not as proof
  Oddschecker never offers these markets for EPL fixtures.
- **One real (small) odds-value discrepancy** was found for a single
  Betfair price (see Validation) and is not fully explained -- most likely
  benign feed-timing skew, but not proven.
- **Still not containerized.** Per Phase 13, `Dockerfile.backend` was
  deliberately left untouched. Chromium + Playwright system deps are still
  absent from the deployed image.
- **Still no persistence.** Every fixture's odds are a live snapshot from
  this spike's single run; nothing is stored, scheduled, or diffed over
  time.

## Recommendation

1. **Oddschecker as the first production provider: YES.** 10/10 fixture
   discovery, 10/10 identity-match, 10/10 1X2 extraction, consistent
   ~26-bookmaker panels, zero Cloudflare blocks across 10 sequential live
   fetches. The approach scales cleanly, not just as a one-fixture fluke.
2. **Is GW3 fixture coverage sufficient: YES**, for 1X2. **NOT YET** for
   O/U 2.5 / BTTS / team totals / player markets, pending a re-check closer
   to kickoff -- this is a timing question, not a viability question.
3. **Continue player-market work: NOT YET.** No evidence they're reachable
   via this method at this point in time; worth one more time-boxed check
   closer to kickoff before investing further, rather than continuing to
   dig now.
4. **Containerize Playwright for staging: YES**, conditionally -- the
   access method is now proven across 10 fixtures, not just 1, which was
   exactly the gate Phase 13 set for making this call. This spike does not
   perform that containerization itself (out of scope per Phase 13/14).
5. **Build persistence/scheduled ingestion next: NOT YET** -- per the hard
   stop below, and because the unpriced-market timing question (do O/U 2.5
   /BTTS/player markets populate closer to kickoff?) should inform how a
   scheduler would need to behave before one is designed.

## Hard stop confirmation

No persistent odds storage, database, scheduler, recurring/background
scraping, additional odds providers (Racing Post, MightyTips, etc.), fair-
probability or consensus modelling, FPL/Hermes_FPL integration, frontend
odds UI, or deployment/staging changes were performed. `Dockerfile.backend`,
CI workflows, and production/staging configuration were not touched. This
spike is scoped to Oddschecker fixture discovery and market coverage
measurement across the 10 GW3 fixtures, as instructed.
