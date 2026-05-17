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
        # Fixed content clip (below the nav) kept identical across every beat
        # so ffmpeg gets uniform frames. Three honest beats: the latest
        # observed pass, the area/route evidence lookup, then the validated
        # method on the Carina time series.
        CLIP = {"x": 0, "y": 96, "width": 1320, "height": 744}
        fi = 0

        def focus(pg, sel: str) -> None:
            # Pin the beat's subject (a map or the evidence card) just under
            # the nav so the fixed CLIP frames it instead of page text.
            pg.evaluate(
                "(s)=>{const e=document.querySelector(s);if(e){"
                "const y=e.getBoundingClientRect().top+window.scrollY-104;"
                "window.scrollTo(0,Math.max(0,y));}}",
                sel,
            )
            pg.wait_for_timeout(500)

        def grab(pg, n: int, gap_ms: int) -> None:
            nonlocal fi
            for _ in range(n):
                pg.screenshot(path=str(frames_dir / f"f{fi:03d}.png"), clip=CLIP)
                pg.wait_for_timeout(gap_ms)
                fi += 1

        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_context(viewport={"width": 1320, "height": 900}).new_page()

            # Beat 1: the Corridor watch (default /map) — the tiered
            # observation log of what the satellites and radar have observed
            # over the expressways, headline + gloss stating it is observed
            # and dated, not live and not a forecast.
            pg.goto(f"http://127.0.0.1:{PORT}/map", wait_until="networkidle")
            pg.wait_for_selector("canvas.maplibregl-canvas", timeout=30000)
            try:
                pg.wait_for_function(
                    "() => window.__fwReady === true", timeout=20000)
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(6000)  # tiles + overlays first paint settle
            focus(pg, "#now-map")
            grab(pg, 16, 300)

            # Beat 1b: realtime conditions — enable the RainViewer rain
            # heartbeat layer and let the per-layer freshness clocks tick.
            # Honest: the layer renders its own as-of time (or the
            # honest-empty state); nothing claims "live".
            rt = pg.query_selector("#cw-toggle-rain")
            if rt and not rt.is_checked():
                rt.click()
            pg.wait_for_timeout(3800)  # rain tiles fetch + 30s-clock first tick
            focus(pg, "#now-map")
            grab(pg, 16, 300)

            # Beat 2: the area/route lookup — type a gazetteer place, pick a
            # suggestion, show the layered as-of-dated evidence card.
            pg.goto(f"http://127.0.0.1:{PORT}/lookup",
                    wait_until="networkidle")
            pg.wait_for_timeout(1500)
            q = pg.query_selector("#al-q")
            if q:
                q.click()
                q.type("SLEX Alabang", delay=70)
                pg.wait_for_timeout(900)
                first = pg.query_selector("#al-suggest li")
                if first:
                    first.click()
                else:
                    pg.keyboard.press("Enter")
                try:
                    pg.wait_for_selector("#al-result:not(.hidden)",
                                         timeout=8000)
                except Exception:  # noqa: BLE001
                    pass
                pg.wait_for_timeout(1200)
                focus(pg, "#al-result")
            grab(pg, 14, 320)

            # Beat 3: the Carina 2024 validated-method time series. Hazard-gap
            # context off so the animating water is the unambiguous subject.
            pg.goto(f"http://127.0.0.1:{PORT}/map", wait_until="networkidle")
            ct = pg.query_selector("#view-carina")
            if ct:
                ct.click()
                try:
                    pg.wait_for_function(
                        "() => window.__fwCarinaMap "
                        "&& window.__fwCarinaMap.getLayer "
                        "&& window.__fwCarinaMap.getLayer('hazard-gap-fill')",
                        timeout=30000)
                except Exception:  # noqa: BLE001
                    pass
                pg.wait_for_timeout(3500)
                gap = pg.query_selector("#toggle-gap")
                if gap and gap.is_checked():
                    gap.click()
                    pg.wait_for_timeout(900)
                play = pg.query_selector("#play-btn")
                if play:
                    play.click()
            focus(pg, "#map")
            grab(pg, 44, 260)
            b.close()
        # sanity: a Now-view frame must not be mostly black (tiles failed)
        from PIL import Image
        mid = Image.open(frames_dir / "f008.png").convert("L")
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
