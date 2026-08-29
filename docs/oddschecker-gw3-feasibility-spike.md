# Oddschecker GW3 Feasibility Spike

Single-fixture spike answering: **can Football_Odds_Service reliably retrieve
and normalize useful Oddschecker markets for Manchester City vs Coventry City
at €0 additional cost?**

## Executive verdict

**VIABLE WITH LIMITATIONS**

The extraction pipeline works end-to-end, deterministically, at €0 cost, and
was validated live against the real fixture. The limitation is not technical:
this far ahead of kickoff, Oddschecker has only published prices for a subset
of markets (1X2, Correct Score, Half Time/Full Time) for this fixture —
Over/Under 2.5, BTTS, and team totals are genuinely not yet priced by any
bookmaker on the site, not merely unparsed.

## Target fixture

Manchester City vs Coventry City
Premier League GW3, Saturday 5 September 2026
Confirmed to exist on Oddschecker as **"Man City v Coventry"**, kickoff
`2026-09-05T14:00:00Z`, at:
`https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry`

## Access method

1. **Plain HTTP (curl, and the WebFetch tool) is blocked outright.** Every
   request — including the Oddschecker homepage, not just this fixture —
   returned HTTP 403 with a Cloudflare "Sorry, you have been blocked" page.
   This is a site-wide WAF rule, not something specific to this URL.
2. **A real, JS-executing browser (headless Chromium via Playwright) passes
   the Cloudflare check** and receives the actual page (HTTP 200). No CAPTCHA
   solving, no proxy, no stealth plugin was needed — a stock headless
   Chromium with a standard desktop Chrome user agent was sufficient.
3. **The odds are not in a clean server-rendered HTML table.** They live in a
   large (~500KB) `<script type="application/json">` block (wrapped in an
   HTML comment) that the page's React app hydrates from — a `bestOdds`
   object containing normalized `bets`, `odds`, `markets`, and `bookmakers`
   entity maps, keyed by numeric IDs. This is preference-order step 2
   (embedded page JSON), not step 4 (HTML table parsing) or step 1 (raw
   HTTP, which is blocked).
4. The visible market accordions on the page (Over/Under, BTTS, etc.) are
   collapsed by default and show "No odds available at the moment" in the
   DOM when expanded — confirming their absence is a genuine data gap, not a
   rendering/lazy-load artifact we failed to trigger.

**Implementation**: `backend/app/providers/oddschecker.py` renders the page
once with Playwright (`fetch_fixture_html`), then parses the embedded JSON
with a pure, network-free function (`parse_oddschecker_html`) that is unit
tested against a saved fixture.

## Anti-bot / reliability observations

- Requests **are** blocked — but only non-browser HTTP clients. A real
  browser was not challenged with a CAPTCHA; Cloudflare's check passed
  silently after JS execution (`/cdn-cgi/challenge-platform/...` and a
  `/verify` call observed in the network log, both resolved automatically).
- JavaScript execution **is required** (both for the Cloudflare check and
  because the odds JSON is inside a hydration script the framework needs to
  be present in the DOM for — though the JSON itself was present at
  `domcontentloaded`, so full hydration/interactivity wasn't actually needed).
- Access was deterministic across repeated runs in this session; no retries
  were needed to get through Cloudflare.
- **Fragility risks for future runs**: Cloudflare bot-detection posture can
  change without notice (this is the biggest long-term risk); a stock
  headless Chromium was enough today but may not remain so; the embedded
  JSON script's structure/index among the page's other JSON scripts could
  change with a frontend deploy (the parser searches all `<script
  type="application/json">` tags for one containing `bestOdds.markets`
  rather than hardcoding a script index, to reduce this risk).

## Markets found

| Market | Available (this fixture, as of 2026-08-29, 7 days pre-kickoff)? | Successfully parsed? | Notes |
|---|---|---|---|
| 1X2 (Match Result) | Yes | Yes | 25 bookmakers, 75 selections (3 outcomes × 25) |
| Over/Under 2.5 Goals | No | N/A (market has zero bets) | "No odds available at the moment" per source |
| Both Teams To Score | No | N/A (market has zero bets) | "No odds available at the moment" per source |
| Man City team total goals | No | N/A (market has zero bets) | "No odds available at the moment" per source |
| Coventry team total goals | No | N/A (market has zero bets) | "No odds available at the moment" per source |
| Anytime goalscorer | Not found on this fixture's main page | Not attempted | No goalscorer market appears in the embedded `bestOdds` payload; Oddschecker likely serves this under a separate URL/tab not investigated in this narrow spike (Priority B, time-boxed) |
| Player 2+ goals | Not found | Not attempted | Same as above |
| Player shots | Not found | Not attempted | Priority C, not investigated per spike scope |
| Player shots on target | Not found | Not attempted | Priority C, not investigated per spike scope |

Markets that *were* found but weren't requested by this spike (evidence the
page/pipeline generalizes): Correct Score (available, 40 bets), Half
Time/Full Time (available, 9 bets), plus 63 other market types present in
`markets.entities` with no current prices.

## Bookmaker coverage

**25 bookmakers** returned an ACTIVE 1X2 price at fetch time (bet365,
William Hill, Unibet, Betfred, Ladbrokes, Coral, Paddy Power, Betfair,
Betway, Skybet, BetMGM UK, and 14 others). Oddschecker's page tracks up to
27 bookmakers for this fixture overall. Individual bookmaker prices were
preserved, not collapsed into a single consensus figure (see Example output
below).

## Example extracted output

```json
{
  "source": "Oddschecker",
  "source_fixture_name": "Man City v Coventry",
  "source_url": "https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry",
  "home_team": "Man City",
  "away_team": "Coventry",
  "fetched_at": "2026-08-29T11:37:23.604881Z",
  "markets": [
    {
      "market_type": "1X2",
      "source_market_name": "Win Market",
      "available": true,
      "note": null,
      "selections": [
        {
          "name": "Man City",
          "bookmaker": "bet365",
          "raw_odds": "2/9",
          "decimal_odds": 1.222,
          "source_decimal_odds": 1.222,
          "bookmaker_updated_at": "2026-08-25T23:36:19.187726Z"
        }
      ]
    },
    {
      "market_type": "OVER_UNDER_2_5",
      "source_market_name": "Total Goals Over/Under",
      "available": false,
      "note": "No odds available at the moment (per source) -- likely too far ahead of kickoff",
      "selections": []
    }
  ]
}
```
(Full response has 75 selections under the 1X2 market alone; truncated here.)

## Manual validation

Comparing the source's own fractional text, our parsed raw value, and our
computed decimal, against the source's own decimal figure (fetched live
2026-08-29):

| Selection | Bookmaker | Source fractional | Parsed `raw_odds` | Our `decimal_odds` | Source `oddsDecimal` |
|---|---|---|---|---|---|
| Man City (1X2) | bet365 | `2/9` | `2/9` | 1.222 | 1.222 |
| Draw (1X2) | bet365 | `13/2` | `13/2` | 7.5 | 7.5 |
| Coventry (1X2) | Betfred | `12/1` | `12/1` | 13.0 | 13.0 |
| Coventry (1X2) | Betfair | `59/5` | `59/5` | 12.8 | 12.8 |

All four match the source's own decimal figure exactly. (One minor,
expected discrepancy: several non-bet365 bookmakers publish `oddsDecimal`
for `2/9` as `1.22` rather than `1.222` — a 2dp vs 3dp rounding difference
in Oddschecker's own feed, not a conversion error on our side; our
`fractional_to_decimal` rounds to 3dp consistently.)

Over/Under 2.5 and BTTS could not be validated against source values because
no bookmaker has priced them yet for this fixture — see Known limitations.

## Known limitations

- **Secondary markets aren't priced yet.** Over/Under 2.5, BTTS, and team
  totals had zero bookmaker prices as of this spike's run (7 days
  pre-kickoff). Whether they populate closer to kickoff is untested — retest
  nearer 2026-09-05 before deciding this is a blocker.
- **Player markets (goalscorer, shots) were not found** on this fixture's
  main page/embedded payload. A separate market tab/URL may exist but wasn't
  investigated (Priority B/C, time-boxed per spike scope).
- **A real headless browser is required per fetch** (~5-8s per page load).
  The API endpoint mitigates this with a temporary 5-minute in-memory cache
  (no persistence, single-process, documented in code) rather than launching
  a browser on every request.
- **Not wired into the production Docker image.** `Dockerfile.backend` /
  `requirements.txt` were deliberately left unchanged — adding Playwright +
  a system Chromium to the deployed container is a real image-size and
  build-time increase, and is a scaling decision that should wait for the
  "proceed to all GW3 fixtures" call, not be bundled into this spike. The
  new `playwright` dependency lives in `pyproject.toml` only; local dev/tests
  install it separately (`pip install playwright && playwright install
  chromium`).
- **Cloudflare posture can change.** Nothing here defeats a CAPTCHA or
  stealth-detects; if Oddschecker tightens bot detection, a stock headless
  browser may stop being enough, and this whole approach would need
  re-validation.
- **Odds are live and move.** Every value in this report is a snapshot;
  normal odds movement, not scraper unreliability, is why re-running the
  endpoint later would show different numbers.

## Recommendation

**Proceed to all 10 GW3 fixtures — YES, with two conditions:**

1. Re-run this spike (or the new endpoint) once for a couple of fixtures
   closer to kickoff to confirm Over/Under 2.5 / BTTS populate in time to be
   useful — if they consistently don't until very close to kickoff, that
   changes the service's usefulness window, not its technical viability.
2. Before scaling to 10 fixtures run concurrently/on a schedule, decide how
   the browser-per-fetch cost and Cloudflare risk should be managed (e.g.
   fetch sequentially with spacing, not in a tight parallel loop) — this
   spike deliberately did not build that orchestration.

The core technical questions are answered: the fixture is locatable
deterministically, the embedded-JSON extraction method is reliable and
reproducible at €0 cost, per-bookmaker raw+normalized odds with full
provenance can be preserved, and failures (missing market, malformed source,
fetch error) surface explicitly rather than being silently papered over.

## Hard stop

No further bookmaker/site expansion, database work, scheduling, consensus
modelling, or Hermes_FPL integration was performed. This spike is scoped to
one fixture on one site, as instructed.
