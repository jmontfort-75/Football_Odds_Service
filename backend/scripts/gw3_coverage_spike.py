"""GW3 full-coverage spike runner (see docs/oddschecker-gw3-full-coverage-spike.md).

Not part of the test suite -- this makes real, sequential, rate-limited
requests to the live Oddschecker site via headless Playwright for all 10
GW3 fixtures. Run manually:

    backend/.venv/bin/python scripts/gw3_coverage_spike.py

Writes a JSON evidence file (one record per fixture, full per-bookmaker
provenance preserved) and prints a markdown coverage matrix + aggregate
stats to stdout. This is a one-shot spike tool, not a scheduler -- it makes
no attempt to persist results anywhere beyond the JSON file, and is not
imported by the application.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.oddschecker import (  # noqa: E402
    GW3_FIXTURES,
    OddscheckerFetchError,
    OddscheckerParseError,
    fixture_identity_matches,
    fixture_url,
    get_fixture_odds,
)

OUTPUT_PATH = Path(__file__).parent / "gw3_coverage_spike_output.json"
PACING_SECONDS = 4.0  # deliberate, sequential, low-concurrency (Phase 5)


async def run() -> list[dict]:
    records: list[dict] = []
    for i, fixture in enumerate(GW3_FIXTURES):
        label = f"{fixture['home']} v {fixture['away']}"
        url = fixture_url(fixture["slug"])
        record: dict = {
            "fixture": label,
            "slug": fixture["slug"],
            "expected_home": fixture["home"],
            "expected_away": fixture["away"],
            "expected_url": url,
            "final_url": url,
            "found": False,
            "identity_match": None,
            "failure_category": None,
            "fetch_seconds": None,
            "odds": None,
        }
        start = time.monotonic()
        try:
            odds = await get_fixture_odds(fixture["slug"])
            record["fetch_seconds"] = round(time.monotonic() - start, 2)
            if not fixture_identity_matches(fixture, odds):
                record["failure_category"] = "FIXTURE_IDENTITY_MISMATCH"
                record["found"] = True
                record["identity_match"] = False
            else:
                record["found"] = True
                record["identity_match"] = True
                record["odds"] = json.loads(odds.model_dump_json())
        except OddscheckerFetchError as exc:
            record["fetch_seconds"] = round(time.monotonic() - start, 2)
            msg = str(exc).lower()
            if "403" in msg or "cloudflare" in msg:
                record["failure_category"] = "CLOUDFLARE_BLOCK"
            elif "timeout" in msg:
                record["failure_category"] = "TIMEOUT"
            else:
                record["failure_category"] = "PAGE_LOAD_FAILURE"
            record["error"] = str(exc)
        except OddscheckerParseError as exc:
            record["fetch_seconds"] = round(time.monotonic() - start, 2)
            record["found"] = True  # page loaded, but we couldn't parse it
            record["failure_category"] = "EMBEDDED_JSON_NOT_FOUND"
            record["error"] = str(exc)
        except Exception as exc:  # noqa: BLE001 - spike must record, never swallow
            record["fetch_seconds"] = round(time.monotonic() - start, 2)
            record["failure_category"] = "PARSE_FAILURE"
            record["error"] = f"{type(exc).__name__}: {exc}"

        records.append(record)
        print(f"[{i + 1}/{len(GW3_FIXTURES)}] {label}: "
              f"found={record['found']} identity_match={record['identity_match']} "
              f"failure={record['failure_category']} ({record['fetch_seconds']}s)")

        if i < len(GW3_FIXTURES) - 1:
            await asyncio.sleep(PACING_SECONDS)

    return records


def summarize(records: list[dict]) -> None:
    found = sum(1 for r in records if r["found"] and r["identity_match"])
    print(f"\nFixture discovery: {found}/{len(records)}")

    core_markets = ["1X2", "OVER_UNDER_2_5", "BTTS", "TEAM_TOTAL_HOME_GOALS", "TEAM_TOTAL_AWAY_GOALS"]
    per_market = {m: {"available": 0, "not_priced": 0, "missing": 0} for m in core_markets}
    bookmaker_counts_1x2 = []

    for r in records:
        odds = r.get("odds")
        if not odds:
            for m in core_markets:
                per_market[m]["missing"] += 1
            continue
        by_type = {m["market_type"]: m for m in odds["markets"]}
        for m in core_markets:
            entry = by_type.get(m)
            if entry is None:
                per_market[m]["missing"] += 1
            elif entry["available"]:
                per_market[m]["available"] += 1
                if m == "1X2":
                    bookmaker_counts_1x2.append(len({s["bookmaker"] for s in entry["selections"]}))
            else:
                per_market[m]["not_priced"] += 1

    print("\nCore market coverage (available / not-priced-yet / missing):")
    for m in core_markets:
        c = per_market[m]
        print(f"  {m}: {c['available']} / {c['not_priced']} / {c['missing']}")

    if bookmaker_counts_1x2:
        print(f"\n1X2 bookmaker counts per fixture: {bookmaker_counts_1x2}")
        print(f"  avg={sum(bookmaker_counts_1x2)/len(bookmaker_counts_1x2):.1f} "
              f"min={min(bookmaker_counts_1x2)} max={max(bookmaker_counts_1x2)}")

    failures = [r for r in records if r["failure_category"]]
    if failures:
        print("\nFailures:")
        for r in failures:
            print(f"  {r['fixture']}: {r['failure_category']} -- {r.get('error', '')}")


async def main() -> None:
    records = await run()
    OUTPUT_PATH.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }, indent=2))
    print(f"\nWrote evidence file: {OUTPUT_PATH}")
    summarize(records)


if __name__ == "__main__":
    asyncio.run(main())
