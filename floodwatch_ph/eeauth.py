"""Earth Engine service-account init. Reads key path from EE_KEY_FILE
(default: repo-local .ee-key.json). project_id + client_email come from the
key JSON. Never commit the key — it is .gitignored."""

from __future__ import annotations

import json
import os
from pathlib import Path


def init_ee():
    import ee

    key = os.environ.get("EE_KEY_FILE") or str(
        Path(__file__).resolve().parent.parent / ".ee-key.json"
    )
    info = json.load(open(key))
    sa = info["client_email"]
    project = info["project_id"]
    creds = ee.ServiceAccountCredentials(sa, key)
    ee.Initialize(creds, project=project)
    return ee


# Philippines national bounding box (lon/lat). Wide enough for GFD events,
# tight enough to keep EE payloads small.
PH_BBOX = [116.7, 4.4, 126.7, 21.3]
