"""Pretty-printer for the demo cast — calls the real Quality Gate library."""
from __future__ import annotations

import json
import sys

from quality_gate import (
    cta_clarity,
    detect_pixels,
    get_campaign_metrics,
    score_page,
)

GREEN, RED, YEL, DIM, BOLD, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"


def _fetch(url: str) -> int:  # offline fetcher for the demo (no network)
    return 404 if "broken" in url else 200


def grade_color(g: str) -> str:
    return {"A": GREEN, "B": GREEN, "C": YEL, "D": YEL, "F": RED}.get(g, OFF)


def load(name: str) -> str:
    return open(f"fixtures/{name}").read()


def show_score(name: str) -> None:
    r = score_page(load(name), base_url="https://site.example.com", fetcher=_fetch)
    g = r["grade"]
    print(f"  {BOLD}{grade_color(g)}{g}{OFF}  ({r['score']}/100)   {DIM}{name}{OFF}")
    s = r["signals"]
    print(f"    pixels {s['pixels']:>3}  mobile {s['mobile']:>3}  cta {s['cta']:>3}  links {s['links']:>3}")


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "score":
        show_score(sys.argv[2])
    elif cmd == "pixels":
        print("  " + json.dumps(detect_pixels(load(sys.argv[2]))))
    elif cmd == "cta":
        print("  " + json.dumps(cta_clarity(load(sys.argv[2]))))
    elif cmd == "metrics":
        print("  " + json.dumps(get_campaign_metrics(sys.argv[2]), indent=2))


if __name__ == "__main__":
    main()
