"""Pre-deploy gate for the near-real-time data chain.

The refresh pipeline regenerates three public GeoJSON files:

  site/public/data/flood_latest.geojson         (Track A, Sentinel-1 SAR)
  site/public/data/current_risk.geojson         (rainfall context, GPM IMERG)
  site/public/data/road_flood_exposure.geojson  (expressway exposure join)

This script runs BEFORE any deploy. The audit flagged the old loop as a
Critical reliability gap: a failed Earth-Engine run could write an empty or
garbage file and the site would ship it silently. This gate stops that.

v1.2 NOTE: the three NEW Corridor watch layers (RainViewer rain radar,
Copernicus GFM SAR, NASA VIIRS NRT) are fetched CLIENT-SIDE in the browser at
page-view and emit NO server GeoJSON, so they intentionally bypass this
pre-deploy cron gate. Their integrity is enforced at runtime by qa_live.py's
__fwCorridor honest-empty assertions, not here. No logic change to this gate.

THE CENTRAL DISTINCTION
-----------------------
There are two very different "empty" states and the gate must not conflate
them:

  HONEST EMPTY  — scan_status says, truthfully, that no usable observation
                  exists right now (flood_latest "no_usable_pass" /
                  "degenerate_threshold" / "low_confidence"; current_risk
                  "no_data" / "low_confidence"). The file is well-formed, the
                  feature list is empty (or "unknown" for roads), and the site
                  is designed to render the honest "no recent usable pass"
                  message. THIS MUST DEPLOY — the site telling the truth is the
                  product working, not failing.

  BROKEN/GARBAGE — the file is not valid JSON, not a FeatureCollection, is
                  missing required _meta keys, carries an unknown scan_status,
                  has an unparseable as_of, or is internally inconsistent
                  (claims scan_status=="ok" with zero features, or claims a
                  non-ok status while shipping fabricated geometry). THIS MUST
                  BLOCK — keep the last known-good copy live.

A stale-but-honest file (old as_of) is a WARNING, not a hard fail: an old
"no_usable_pass" is still the truth and the site must be allowed to say so.

Exit code 0 == safe to deploy (PASS, possibly with warnings).
Exit code 1 == BLOCK deploy, keep last good live.

Usage:
    python scripts/gate_realtime.py [--data-dir site/public/data]
                                    [--s1-max-age-days 20]
                                    [--gpm-max-age-hours 24]
                                    [--strict-stale]   # treat staleness as fail
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Authoritative scan_status enums (from docs/research/SCHEMA-latest.md and the
# module docstrings in realtime/current_risk.py and pipeline/road_exposure.py).
FLOOD_STATUSES = {"ok", "no_usable_pass", "degenerate_threshold", "low_confidence"}
RISK_STATUSES = {"ok", "no_data", "low_confidence"}
ROAD_STATUSES = {"ok", "no_usable_pass", "degenerate_threshold", "low_confidence"}

# scan_status values that mean "honest empty" — site shows the truthful
# message, the deploy is allowed precisely so it can.
HONEST_EMPTY = {
    "no_usable_pass",
    "degenerate_threshold",
    "low_confidence",
    "no_data",
}


class Report:
    def __init__(self) -> None:
        self.fail: list[str] = []
        self.warn: list[str] = []
        self.ok: list[str] = []

    def check(self, name: str, cond: bool, detail: str = "", hard: bool = True) -> bool:
        if cond:
            self.ok.append(name)
            print(f"  [PASS] {name}{(' — ' + detail) if detail else ''}")
            return True
        bucket = self.fail if hard else self.warn
        bucket.append(f"{name}{(' :: ' + detail) if detail else ''}")
        tag = "FAIL" if hard else "WARN"
        print(f"  [{tag}] {name}{(' — ' + detail) if detail else ''}")
        return False

    def note_warn(self, name: str, detail: str = "") -> None:
        self.warn.append(f"{name}{(' :: ' + detail) if detail else ''}")
        print(f"  [WARN] {name}{(' — ' + detail) if detail else ''}")

    def note_ok(self, name: str, detail: str = "") -> None:
        self.ok.append(name)
        print(f"  [PASS] {name}{(' — ' + detail) if detail else ''}")


def _load(path: Path, rpt: Report) -> dict | None:
    """Valid-JSON + FeatureCollection structural gate. None == hard fail."""
    if not path.exists():
        rpt.check(f"{path.name} exists", False, str(path))
        return None
    try:
        data = json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001 - any parse error is a hard block
        rpt.check(f"{path.name} valid JSON", False, repr(e)[:140])
        return None
    rpt.note_ok(f"{path.name} valid JSON")
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        rpt.check(f"{path.name} is FeatureCollection", False,
                  str(data.get("type") if isinstance(data, dict) else type(data)))
        return None
    if not isinstance(data.get("features"), list):
        rpt.check(f"{path.name} features is array", False)
        return None
    if not isinstance(data.get("_meta"), dict):
        rpt.check(f"{path.name} _meta present", False)
        return None
    rpt.note_ok(f"{path.name} FeatureCollection + _meta + features[]")
    return data


def _parse_as_of(raw) -> dt.datetime | None:
    """Accept ISO date 'YYYY-MM-DD' or ISO-8601 UTC timestamp. None on fail."""
    if raw is None or not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip().replace("Z", "+00:00")
    for parse in (
        lambda x: dt.datetime.fromisoformat(x),
        lambda x: dt.datetime.strptime(x, "%Y-%m-%d"),
    ):
        try:
            d = parse(s)
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d
        except Exception:  # noqa: BLE001
            continue
    return None


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def gate_flood(path: Path, rpt: Report, max_age_days: int, strict_stale: bool) -> None:
    print(f"\n--- {path.name} (Track A — Sentinel-1 observed flood) ---")
    data = _load(path, rpt)
    if data is None:
        return
    meta = data["_meta"]
    feats = data["features"]

    # Required keys that the schema guarantees ALWAYS present (any status).
    required = ["event", "role", "permanent_water_masked", "scan_status",
                "as_of", "generated_at", "feature_count", "s1_scene_ids",
                "observed_not_forecast", "disclaimer"]
    missing = [k for k in required if k not in meta]
    if not rpt.check(f"{path.name} _meta has required keys", not missing,
                     f"missing {missing}" if missing else "all present"):
        return

    status = meta.get("scan_status")
    rpt.check(f"{path.name} scan_status is a known enum",
              status in FLOOD_STATUSES, str(status))
    rpt.check(f"{path.name} permanent_water_masked is true",
              meta.get("permanent_water_masked") is True, str(meta.get("permanent_water_masked")))
    rpt.check(f"{path.name} observed_not_forecast is true",
              meta.get("observed_not_forecast") is True)

    fcount = meta.get("feature_count")
    rpt.check(f"{path.name} feature_count matches features[]",
              isinstance(fcount, int) and fcount == len(feats),
              f"meta={fcount} actual={len(feats)}")

    # Internal-consistency: the contradictory-envelope bug class.
    if status == "ok":
        rpt.check(f"{path.name} status==ok implies real polygons",
                  len(feats) > 0,
                  f"{len(feats)} polygons"
                  if len(feats) > 0 else
                  "scan_status=ok but ZERO features — broken/garbage, NOT honest empty")
        as_of = _parse_as_of(meta.get("as_of"))
        rpt.check(f"{path.name} status==ok has parseable as_of",
                  as_of is not None, str(meta.get("as_of")))
        if as_of is not None:
            age_days = (_now() - as_of).total_seconds() / 86400.0
            stale = age_days > max_age_days
            rpt.check(f"{path.name} as_of within {max_age_days}d (S1 revisit)",
                      not stale, f"as_of={meta.get('as_of')} age={age_days:.1f}d",
                      hard=strict_stale)
    elif status in HONEST_EMPTY:
        # Honest empty: MUST be empty geometry. A non-ok status shipping
        # fabricated polygons is the garbage case and must block.
        rpt.check(f"{path.name} honest-empty ({status}) has no fabricated geometry",
                  len(feats) == 0,
                  f"{len(feats)} features under non-ok status — fabricated geometry")
        rpt.note_ok(f"{path.name} honest empty ({status}) — site shows truthful "
                    f"message, deploy ALLOWED")
    # unknown status already hard-failed by the enum check above.


def gate_risk(path: Path, rpt: Report, max_age_hours: int, strict_stale: bool) -> None:
    print(f"\n--- {path.name} (rainfall context — GPM IMERG) ---")
    data = _load(path, rpt)
    if data is None:
        return
    meta = data["_meta"]
    feats = data["features"]

    required = ["as_of", "generated_at", "source", "scan_status",
                "feature_count", "disclaimer", "windows", "aoi"]
    missing = [k for k in required if k not in meta]
    if not rpt.check(f"{path.name} _meta has required keys", not missing,
                     f"missing {missing}" if missing else "all present"):
        return

    status = meta.get("scan_status")
    rpt.check(f"{path.name} scan_status is a known enum",
              status in RISK_STATUSES, str(status))

    fcount = meta.get("feature_count")
    rpt.check(f"{path.name} feature_count matches features[]",
              isinstance(fcount, int) and fcount == len(feats),
              f"meta={fcount} actual={len(feats)}")

    if status == "ok":
        rpt.check(f"{path.name} status==ok implies sampled points",
                  len(feats) > 0,
                  f"{len(feats)} sample points"
                  if len(feats) > 0 else
                  "scan_status=ok but ZERO features — broken/garbage")
        as_of = _parse_as_of(meta.get("as_of"))
        rpt.check(f"{path.name} status==ok has parseable as_of",
                  as_of is not None, str(meta.get("as_of")))
        if as_of is not None:
            age_h = (_now() - as_of).total_seconds() / 3600.0
            stale = age_h > max_age_hours
            rpt.check(f"{path.name} as_of within {max_age_hours}h (IMERG latency)",
                      not stale, f"as_of={meta.get('as_of')} age={age_h:.1f}h",
                      hard=strict_stale)
    elif status in HONEST_EMPTY:
        rpt.check(f"{path.name} honest-empty ({status}) has no fabricated points",
                  len(feats) == 0,
                  f"{len(feats)} features under non-ok status — fabricated data")
        rpt.note_ok(f"{path.name} honest empty ({status}) — context layer "
                    f"truthfully empty, deploy ALLOWED")


def gate_roads(path: Path, rpt: Report) -> None:
    print(f"\n--- {path.name} (expressway exposure join) ---")
    data = _load(path, rpt)
    if data is None:
        return
    meta = data["_meta"]
    feats = data["features"]

    required = ["as_of", "generated_at", "source", "scan_status",
                "feature_count", "expressway_summary", "observed_not_forecast"]
    missing = [k for k in required if k not in meta]
    if not rpt.check(f"{path.name} _meta has required keys", not missing,
                     f"missing {missing}" if missing else "all present"):
        return

    status = meta.get("scan_status")
    rpt.check(f"{path.name} scan_status is a known enum",
              status in ROAD_STATUSES, str(status))

    fcount = meta.get("feature_count")
    rpt.check(f"{path.name} feature_count matches features[]",
              isinstance(fcount, int) and fcount == len(feats),
              f"meta={fcount} actual={len(feats)}")

    # Roads always emits every monitored segment (even on non-ok status the
    # segments are present with exposure="unknown"), so an empty feature list
    # is itself broken regardless of status.
    rpt.check(f"{path.name} has monitored segments", len(feats) > 0,
              f"{len(feats)} segments"
              if len(feats) > 0 else
              "0 features — road network missing, broken")

    if status in HONEST_EMPTY:
        exposures = {
            f.get("properties", {}).get("exposure") for f in feats[:5000]
        }
        rpt.check(f"{path.name} non-ok status segments are 'unknown'",
                  exposures.issubset({"unknown"}) or "unknown" in exposures,
                  f"exposures sampled={sorted(x for x in exposures if x)}")
        rpt.note_ok(f"{path.name} honest empty ({status}) — segments marked "
                    f"unknown, deploy ALLOWED")
    elif status == "ok":
        rpt.note_ok(f"{path.name} status==ok — real intersections computed")


def run_existing_gates(rpt: Report) -> None:
    """Reuse the locked integrity gates that already exist."""
    print("\n--- existing integrity gates ---")
    import importlib.util

    for label, rel in (
        ("permanent-water mask (flood_latest covered by flood_*.geojson glob)",
         "scripts/check_permanent_water.py"),
        ("no-PII / barangay-aggregate", "scripts/check_no_pii.py"),
    ):
        mod_path = REPO / rel
        try:
            spec = importlib.util.spec_from_file_location("_gate_chk", mod_path)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            rc = mod.main()
            rpt.check(f"existing gate: {label}", rc == 0, f"exit={rc}")
        except Exception as e:  # noqa: BLE001
            rpt.check(f"existing gate: {label}", False, repr(e)[:140])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pre-deploy gate for the realtime data chain")
    ap.add_argument("--data-dir", default=str(REPO / "site" / "public" / "data"))
    ap.add_argument("--s1-max-age-days", type=int, default=20)
    ap.add_argument("--gpm-max-age-hours", type=int, default=24)
    ap.add_argument("--strict-stale", action="store_true",
                    help="treat stale-but-honest as a hard fail (default: warn only)")
    args = ap.parse_args(argv)

    data_dir = Path(args.data_dir)
    rpt = Report()

    print("=== FloodWatch.PH pre-deploy realtime gate ===")
    print(f"data-dir: {data_dir}")

    gate_flood(data_dir / "flood_latest.geojson", rpt,
               args.s1_max_age_days, args.strict_stale)
    gate_risk(data_dir / "current_risk.geojson", rpt,
              args.gpm_max_age_hours, args.strict_stale)
    gate_roads(data_dir / "road_flood_exposure.geojson", rpt)
    run_existing_gates(rpt)

    print("\n==== GATE SUMMARY ====")
    print(f"PASS {len(rpt.ok)}  WARN {len(rpt.warn)}  FAIL {len(rpt.fail)}")
    for w in rpt.warn:
        print("  WARN:", w)
    for f in rpt.fail:
        print("  FAIL:", f)

    if rpt.fail:
        print("\nRESULT: BLOCK — broken/garbage data detected. "
              "Keeping last known-good deploy live.")
        return 1
    if rpt.warn:
        print("\nRESULT: PASS (with warnings) — data is honest. Deploy allowed; "
              "the site will show the truthful state.")
        return 0
    print("\nRESULT: PASS — safe to deploy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
