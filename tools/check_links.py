"""Resolve every href in public/ and report anything that does not exist.

A bare "#frag" targets the page it appears on, not index.html. Getting that
wrong reports a false failure on any in-page anchor.
"""

import re
import sys
from pathlib import Path

PUB = Path(__file__).resolve().parent.parent / "public"


def main() -> int:
    bad = 0
    pages = {p.name: p.read_text() for p in sorted(PUB.glob("*.html"))}
    for name, html in pages.items():
        for href in sorted(set(re.findall(r'href="([^"]+)"', html))):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            base, _, frag = href.partition("#")
            if base in ("", "./"):
                target = name if not base else "index.html"
            else:
                target = base
            if target not in pages:
                if not (PUB / target).exists():
                    print(f"  MISS  {name} -> {href}  (no such file)")
                    bad += 1
                continue
            if frag and f'id="{frag}"' not in pages[target]:
                print(f"  MISS  {name} -> {href}  (no such anchor)")
                bad += 1
    print(f"  {'all links and anchors resolve' if not bad else f'*** {bad} broken ***'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
