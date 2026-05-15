"""Record the REAL /map time-slider demo as the README hero GIF.

Serves the production site build, drives the actual MapLibre time slider with
Playwright while capturing video, then ffmpeg-optimises to a looping GIF.
This is a real recording of the running site, never a mock-up.

Usage: python scripts/record_hero.py
Prereqs: site built (`cd site && pnpm build`), playwright + chromium,
ffmpeg on PATH.
"""

from __future__ import annotations

import http.server
import shutil
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "site" / "dist"
OUT = REPO / "docs" / "screenshots" / "hero.gif"
PORT = 4399


def _serve(directory: Path):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *a, directory=str(directory), **k
    )
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> int:
    if not DIST.exists():
        print("[record_hero] site/dist missing — run `cd site && pnpm build`",
              file=sys.stderr)
        return 1
    if not shutil.which("ffmpeg"):
        print("[record_hero] ffmpeg not found", file=sys.stderr)
        return 1
    from playwright.sync_api import sync_playwright

    httpd = _serve(DIST)
    vid_dir = REPO / "docs" / "screenshots" / "_vid"
    vid_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(
                viewport={"width": 1280, "height": 760},
                record_video_dir=str(vid_dir),
                record_video_size={"width": 1280, "height": 760},
            )
            pg = ctx.new_page()
            pg.goto(f"http://127.0.0.1:{PORT}/map", wait_until="networkidle")
            pg.wait_for_timeout(3500)  # MapLibre tiles + geojson load
            sliders = pg.query_selector_all('input[type="range"]')
            if sliders:
                s = sliders[0]
                mn = int(s.get_attribute("min") or 0)
                mx = int(s.get_attribute("max") or 3)
                for v in list(range(mn, mx + 1)) + list(range(mx, mn - 1, -1)):
                    s.evaluate(
                        "(el,val)=>{el.value=val;"
                        "el.dispatchEvent(new Event('input',{bubbles:true}));"
                        "el.dispatchEvent(new Event('change',{bubbles:true}));}",
                        v,
                    )
                    pg.wait_for_timeout(1100)
            else:
                pg.wait_for_timeout(4000)
            ctx.close()
            b.close()
        webm = sorted(vid_dir.glob("*.webm"))[-1]
        OUT.parent.mkdir(parents=True, exist_ok=True)
        palette = vid_dir / "pal.png"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(webm), "-vf",
             "fps=10,scale=960:-1:flags=lanczos,palettegen", str(palette)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(webm), "-i", str(palette),
             "-lavfi", "fps=10,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse",
             "-loop", "0", str(OUT)],
            check=True, capture_output=True,
        )
        print(f"[record_hero] wrote {OUT} "
              f"({OUT.stat().st_size / 1e6:.2f} MB)")
    finally:
        httpd.shutdown()
        shutil.rmtree(vid_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
