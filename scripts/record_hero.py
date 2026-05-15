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
    frames_dir = vid_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_context(viewport={"width": 1320, "height": 900}).new_page()
            pg.goto(f"http://127.0.0.1:{PORT}/map", wait_until="networkidle")
            # Wait until MapLibre has actually rendered (basemap tiles loaded),
            # not just a fixed sleep -- the old GIF was black because tiles had
            # not painted yet.
            pg.wait_for_selector("canvas.maplibregl-canvas", timeout=30000)
            try:
                pg.wait_for_function(
                    "() => { const m=document.querySelector('.maplibregl-map');"
                    "return m && window.__fwReady === true; }",
                    timeout=8000,
                )
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(7000)  # tiles + flood first paint settle
            mapEl = pg.query_selector("#map")
            box = mapEl.bounding_box()
            mapEl.scroll_into_view_if_needed()
            pg.wait_for_timeout(800)
            box = pg.query_selector("#map").bounding_box()
            clip = {"x": box["x"], "y": box["y"],
                    "width": box["width"], "height": box["height"]}
            # Hero = the pure SAR flood time-series. Turn the analytical
            # hazard-gap province layer OFF so the animating water is the
            # unambiguous subject (it is a toggle on the live site too).
            gap = pg.query_selector("#toggle-gap")
            if gap and gap.is_checked():
                gap.click()
                pg.wait_for_timeout(900)
            play = pg.query_selector("#play-btn")
            if play:
                play.click()
            # Tightly-framed map screenshots through ~2 PLAY loops so the GIF
            # shows the smooth cross-fade water (grow -> peak -> recede), no
            # page chrome, clean aspect for the README.
            n = 56
            for i in range(n):
                pg.screenshot(path=str(frames_dir / f"f{i:03d}.png"), clip=clip)
                pg.wait_for_timeout(260)
            b.close()
        # sanity: a mid frame must not be mostly black (tiles failed)
        from PIL import Image
        mid = Image.open(frames_dir / "f028.png").convert("L")
        px = list(mid.getdata())
        dark = sum(1 for v in px if v < 28) / len(px)
        if dark > 0.6:
            print(f"[record_hero] FAIL: map frame is {dark:.0%} black "
                  "(basemap tiles did not render)", file=sys.stderr)
            return 1
        OUT.parent.mkdir(parents=True, exist_ok=True)
        palette = vid_dir / "pal.png"
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", "8", "-i", str(frames_dir / "f%03d.png"),
             "-vf", "scale=1000:-1:flags=lanczos,palettegen=stats_mode=diff",
             str(palette)], check=True, capture_output=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", "8", "-i", str(frames_dir / "f%03d.png"),
             "-i", str(palette), "-lavfi",
             "scale=1000:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer",
             "-loop", "0", str(OUT)], check=True, capture_output=True,
        )
        print(f"[record_hero] wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB), "
              f"map frame {dark:.0%} dark (OK)")
    finally:
        httpd.shutdown()
        shutil.rmtree(vid_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
