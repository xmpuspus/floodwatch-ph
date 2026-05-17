"""BetterGovPH DPWH flood-control data adapter.

Adapted from the ghostwatch PhilippinesAdapter
(/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/philippines.py,
lines 71-256): same fetch-retry, column-variant detection, status
normalization, title-keyword classification, geolocation extraction.

Differences from ghostwatch:
- Synchronous fetch with curl 3-retry plus backoff, then a huggingface_hub /
  datasets fallback, then a committed raw snapshot cache so the pipeline runs
  offline in CI.
- The parsed frame is filtered to the flood-control subset only.
- A geolocation_confidence column is carried: 1.0 when the row had usable
  source coordinates, 0.6 when the location must come from a province-centroid
  fallback downstream.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd

from floodwatch_ph.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# HuggingFace bettergovph dataset (CC0). The tabular parquet, not the
# all-details variant.
DATASET_REPO = "bettergovph/dpwh-transparency-data"
PARQUET_FILE = "dpwh_transparency_data.parquet"
PARQUET_URL = (
    f"https://huggingface.co/datasets/{DATASET_REPO}"
    f"/resolve/main/{PARQUET_FILE}"
)

# target_field -> [source column variants, case-insensitive]. The bettergovph
# dataset uses camelCase (contractId, startDate, ...).
DPWH_COLUMNS: dict[str, list[str]] = {
    "project_id": ["contractid", "project_id", "projectid", "id", "globalid"],
    "title": ["description", "title", "project_title", "project_name", "projectdescription"],
    "contract_amount": [
        "contractcost",
        "budget",
        "abc",
        "approvedbudgetforthecontract",
        "contract_amount",
        "amount",
        "cost",
        "fundingyear_cost",
    ],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lng", "lon", "long", "x"],
    "status": ["status", "projectstatus", "project_status", "physical_status"],
    "project_type": ["typeofwork", "category", "project_type", "type", "scopeofwork"],
    "category": ["category", "projectcomponentdescription", "infraproject", "typeofwork"],
    "region": ["region"],
    "province": ["province"],
}

_STATUS_MAP: dict[str, list[str]] = {
    "completed": ["completed", "complete", "finished", "done", "100"],
    "ongoing": ["ongoing", "on-going", "on going", "in progress", "started", "under construction"],
    "not_started": ["not yet started", "not started", "for implementation", "pending", "procurement"],
}

# Description-keyword set used only to rescue rows whose category is
# uninformative (blank or a non-descriptive program code). It never
# reclassifies a row that already carries an explicit infrastructure category.
_FLOOD_CONTROL_KEYWORDS = [
    "flood control",
    "drainage",
    "dike",
    "river control",
    "slope protection",
    "pumping station",
    "revetment",
    "seawall",
    "flood mitigation",
    "river wall",
    "bank protection",
]

# Canonical category value in the bettergovph dataset. An exact, stripped,
# case-insensitive match on this is the primary inclusion rule.
_FLOOD_CONTROL_CATEGORY = "flood control and drainage"

# Any of these words in the category means it carries an explicit
# infrastructure type. Such a row is never rescued by description keywords,
# even when the description mentions drainage or slope-protection components.
# A DPWH-categorized "Roads" project is road spending, not flood-control
# spending.
_EXPLICIT_INFRA_WORDS = [
    "road",
    "bridge",
    "building",
    "water supply",
    "water provision",
    "hospital",
    "school",
    "port",
    "harbor",
    "dam",
    "flood control",
    "drainage",
    "slope protection",
    "seawall",
    "revetment",
    "dike",
    "pumping",
    "bank protection",
    "rain water",
    "septage",
    "sewerage",
    "accessibility",
    "electrical",
    "consultancy",
    "waterway",
    "multi purpose",
]

# Program-code prefixes and tokens that mark a category as uninformative
# (a funding shell, not a project type). Only rows in this state are eligible
# for description-keyword rescue.
_PROGRAM_CODE_PREFIX = re.compile(
    r"^(gaa |unprogrammed|trust funds|contingent|sra |pamana|special road|"
    r"r\.a\.|support for|pagcor)"
)
_PROGRAM_CODE_TOKEN = re.compile(
    r"\b(cssp|mfo|oo-|lp|lfp|ssp|ndrrmf|faps|beff|hfep|cp|itemization|fmr|"
    r"augmentation)\b"
)


class FloodControlAdapter(BaseAdapter):
    name = "flood_control"
    column_map = DPWH_COLUMNS
    status_map = _STATUS_MAP

    def fetch(self, output_dir: Path) -> Path | None:
        """Resolve a raw parquet snapshot.

        Order: committed cache (offline / deterministic CI) -> curl with
        3-attempt retry and exponential backoff -> huggingface_hub
        hf_hub_download -> datasets library. The first successful network
        fetch is written to the committed cache path so later runs are
        offline and reproducible.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_path = output_dir / "_dpwh_flood_control_cache.parquet"

        if cache_path.exists() and cache_path.stat().st_size > 0:
            logger.info("Using committed snapshot cache %s", cache_path)
            return cache_path

        raw_path = output_dir / "_dpwh_raw_download.parquet"

        if self._fetch_curl(raw_path) or self._fetch_hf_hub(raw_path) or self._fetch_datasets(raw_path):
            cache_path.write_bytes(raw_path.read_bytes())
            raw_path.unlink(missing_ok=True)
            size_mb = cache_path.stat().st_size / (1024 * 1024)
            logger.info("Wrote %.1f MB snapshot cache to %s", size_mb, cache_path)
            return cache_path

        logger.error("All fetch paths failed and no cache present")
        return None

    def _fetch_curl(self, output_path: Path) -> bool:
        for attempt in range(3):
            try:
                result = subprocess.run(
                    [
                        "curl",
                        "-L",
                        "-f",
                        "--connect-timeout",
                        "30",
                        "--max-time",
                        "600",
                        "-o",
                        str(output_path),
                        PARQUET_URL,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=660,
                )
                if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                    size_mb = output_path.stat().st_size / (1024 * 1024)
                    logger.info("curl downloaded %.1f MB", size_mb)
                    return True
                logger.warning(
                    "curl attempt %d failed (rc=%d): %s",
                    attempt + 1,
                    result.returncode,
                    result.stderr[:200],
                )
            except subprocess.TimeoutExpired:
                logger.warning("curl attempt %d timed out", attempt + 1)
            except Exception as exc:
                logger.warning("curl attempt %d error: %s", attempt + 1, exc)
            if attempt < 2:
                wait = 2 ** (attempt + 1)
                logger.info("Retrying curl in %ds", wait)
                time.sleep(wait)
        return False

    def _fetch_hf_hub(self, output_path: Path) -> bool:
        try:
            from huggingface_hub import hf_hub_download

            logger.info("Falling back to huggingface_hub hf_hub_download")
            local = hf_hub_download(
                repo_id=DATASET_REPO,
                filename=PARQUET_FILE,
                repo_type="dataset",
            )
            output_path.write_bytes(Path(local).read_bytes())
            return output_path.exists() and output_path.stat().st_size > 0
        except ImportError:
            logger.warning("huggingface_hub not installed")
            return False
        except Exception as exc:
            logger.warning("hf_hub_download failed: %s", exc)
            return False

    def _fetch_datasets(self, output_path: Path) -> bool:
        try:
            from datasets import load_dataset

            logger.info("Falling back to datasets.load_dataset")
            ds = load_dataset(DATASET_REPO, split="train")
            ds.to_pandas().to_parquet(output_path, index=False)
            return output_path.exists() and output_path.stat().st_size > 0
        except ImportError:
            logger.warning("datasets library not installed")
            return False
        except Exception as exc:
            logger.warning("datasets load failed: %s", exc)
            return False

    def parse(self, filepath: Path) -> pd.DataFrame:
        """Parse the raw parquet into the flood-control subset.

        Returns a frame with: project_id, title, contract_amount (float or
        None), status (normalized), project_type (title-keyword class),
        latitude/longitude (float or None), geolocation_confidence (1.0 with
        source coords else 0.6), region, province.
        """
        df = pd.read_parquet(filepath)
        logger.info("Raw dataset: %d rows, %d columns", len(df), len(df.columns))

        col_map = self.detect_columns(df)
        logger.info("Mapped columns: %s", col_map)

        location_col = next((c for c in df.columns if c.lower() == "location"), None)

        records: list[dict[str, Any]] = []
        skipped = 0
        for idx, row in df.iterrows():
            try:
                title = str(row.get(col_map.get("title", ""), "")).strip()

                category_raw = ""
                if "category" in col_map:
                    category_raw = str(row.get(col_map["category"], "")).strip()
                if not category_raw and "project_type" in col_map:
                    category_raw = str(row.get(col_map["project_type"], "")).strip()

                if not self._is_flood_control(category_raw, title):
                    continue

                if location_col is not None:
                    region, province = self._extract_location(row.get(location_col))
                else:
                    region = str(row.get(col_map.get("region", ""), "")).strip()
                    province = str(row.get(col_map.get("province", ""), "")).strip()

                lat = self._maybe_float(row.get(col_map.get("latitude", ""))) if "latitude" in col_map else None
                lon = self._maybe_float(row.get(col_map.get("longitude", ""))) if "longitude" in col_map else None
                has_coords = lat is not None and lon is not None
                if has_coords and not self._coords_in_ph(lat, lon):
                    lat = lon = None
                    has_coords = False

                pid = str(row.get(col_map.get("project_id", ""), f"DPWH-{idx}")).strip()
                if not pid or pid.lower().startswith("nan"):
                    skipped += 1
                    continue

                records.append(
                    {
                        "project_id": pid,
                        "title": title,
                        "contract_amount": self.normalize_amount(
                            row.get(col_map.get("contract_amount", ""))
                        ),
                        "status": self.normalize_status(row.get(col_map.get("status", ""))),
                        "project_type": self._classify_flood_type(title, category_raw),
                        "latitude": lat,
                        "longitude": lon,
                        "geolocation_confidence": 1.0 if has_coords else 0.6,
                        "region": region,
                        "province": province,
                    }
                )
            except Exception as exc:
                logger.warning("Error parsing row %s: %s", idx, exc)
                skipped += 1

        result = pd.DataFrame(records)
        logger.info(
            "Flood-control subset: %d projects, skipped %d", len(result), skipped
        )
        return result

    @staticmethod
    def _category_uninformative(category: str) -> bool:
        """True when the category is a funding shell, not a project type.

        Blank or a non-descriptive program code (GAA 20XX ..., Unprogrammed
        ..., CSSP, MFO, OO-, LP, LFP, SSP, etc.) with no infrastructure-type
        word. A category carrying any explicit infra word is informative and
        therefore never uninformative.
        """
        s = category.strip().lower()
        if s in ("", "nan", "none", "null"):
            return True
        if any(w in s for w in _EXPLICIT_INFRA_WORDS):
            return False
        if _PROGRAM_CODE_PREFIX.match(s):
            return True
        if _PROGRAM_CODE_TOKEN.search(s):
            return True
        return False

    @staticmethod
    def _is_flood_control(category: str, title: str) -> bool:
        """Defensible flood-control membership.

        1. Exact (stripped, case-insensitive) match on the canonical DPWH
           category "Flood Control and Drainage" is always included.
        2. Otherwise, a row is rescued ONLY when its category is uninformative
           (a funding shell) AND its description clearly indicates flood
           control by keyword.
        3. A row carrying an explicit non-flood infrastructure category
           (Roads, Bridges, Buildings, ...) is never reclassified, even when
           the description mentions drainage or slope-protection components.
        """
        cat = category.strip().lower()
        if cat == _FLOOD_CONTROL_CATEGORY:
            return True
        if not FloodControlAdapter._category_uninformative(category):
            return False
        text = title.lower()
        return any(kw in text for kw in _FLOOD_CONTROL_KEYWORDS)

    @staticmethod
    def _classify_flood_type(title: str, category: str) -> str:
        """Sub-classify the flood-control project by title keyword.

        Returns the matched flood-control keyword, or 'flood control' as the
        default subset label.
        """
        text = f"{title} {category}".lower()
        for kw in _FLOOD_CONTROL_KEYWORDS:
            if kw in text:
                return kw
        return "flood control"

    @staticmethod
    def _extract_location(location_val: Any) -> tuple[str, str]:
        """Return (region, province) from the location column.

        The bettergovph dataset stores location as a dict, e.g.
        {"province": "Bulacan", "region": "Region III"}.
        """
        if isinstance(location_val, dict):
            return (
                str(location_val.get("region", "")).strip(),
                str(location_val.get("province", "")).strip(),
            )
        if isinstance(location_val, str):
            return "", location_val.strip()
        return "", ""

    @staticmethod
    def _maybe_float(val: Any) -> float | None:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        if f != f:  # NaN
            return None
        return f

    @staticmethod
    def _coords_in_ph(lat: float, lon: float) -> bool:
        # PH_BBOX = [116.7, 4.4, 126.7, 21.3] (lon_min, lat_min, lon_max, lat_max)
        return 4.4 <= lat <= 21.3 and 116.7 <= lon <= 126.7
