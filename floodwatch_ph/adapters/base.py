"""Abstract base adapter for government infrastructure data sources.

Copied from the ghostwatch BaseAdapter pattern
(/Users/xavier/Desktop/ghostwatch/ghostwatch/adapters/base.py). Same
column-variant detection, status normalization, amount and date parsing.
Kept synchronous here because the FloodWatch pipeline is a plain script,
not an async service.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    name: str = "base"
    # target_field -> [source column name variants, case-insensitive]
    column_map: dict[str, list[str]] = {}
    # canonical status -> [raw value variants]
    status_map: dict[str, list[str]] = {}

    @abstractmethod
    def fetch(self, output_dir: Path) -> Path | None:
        """Download or locate raw data. Returns path to file, or None on failure."""
        ...

    @abstractmethod
    def parse(self, filepath: Path) -> pd.DataFrame:
        """Parse raw file into a standardized DataFrame."""
        ...

    def detect_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """Map DataFrame columns to standardized field names using column_map.

        Returns dict of target_field -> actual_column_name.
        """
        col_lower = {col.lower().strip(): col for col in df.columns}
        mapped = {}
        for target, variants in self.column_map.items():
            for variant in variants:
                if variant.lower() in col_lower:
                    mapped[target] = col_lower[variant.lower()]
                    break
        return mapped

    def normalize_status(self, status: Any) -> str:
        """Map raw status value to a canonical status string."""
        if pd.isna(status):
            return "unknown"
        s = str(status).lower().strip()
        for canonical, variants in self.status_map.items():
            if any(v in s for v in variants):
                return canonical
        return "unknown"

    def normalize_amount(self, amount: Any) -> float | None:
        """Parse a monetary amount to float, stripping currency symbols and commas."""
        if pd.isna(amount):
            return None
        if isinstance(amount, (int, float)):
            return float(amount) if amount > 0 else None
        amount_str = str(amount).strip()
        for char in ["₱", "P", "PHP", ",", " "]:
            amount_str = amount_str.replace(char, "")
        try:
            val = float(amount_str)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None

    def normalize_date(self, date_val: Any) -> str | None:
        """Parse dates in various formats to ISO YYYY-MM-DD."""
        if pd.isna(date_val):
            return None
        if isinstance(date_val, datetime):
            return date_val.strftime("%Y-%m-%d")
        if isinstance(date_val, pd.Timestamp):
            return date_val.strftime("%Y-%m-%d")
        date_str = str(date_val).strip()
        if not date_str or date_str.lower() in ("nat", "none", "null", ""):
            return None
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d-%b-%Y",
            "%d-%b-%y",
            "%B %d, %Y",
            "%d %B %Y",
            "%Y-%m-%dT%H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:20], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
