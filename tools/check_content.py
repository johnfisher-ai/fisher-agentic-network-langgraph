"""Assert the house rules and the canonical claims, against rendered text.

Written because ad-hoc greps kept giving false results: HTML entities, an
apostrophe written literally where the check expected &#x27;, and a bare
"#frag" resolved against the wrong file. Every check here compares against
tag-stripped, entity-decoded text, which is what a reader actually sees.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import page                                   # noqa: E402

PUB = ROOT / "public"
PAGES = ["index.html", "architecture.html", "code.html", "run.html"]

# Words that must never reach a reader, with the reason.
BANNED = [
    (r"\bfixtures?\b",              "testing jargon; say 'canned reply' or 'written in advance'"),
    (r"—",                     "prose em-dash"),
    (r"\b(licence|colour|behaviour|organis\w+)\b", "British spelling"),
    (r"\b(the original|first version|an earlier version|was broken)\b",
                                    "describes an earlier version instead of the current one"),
]


def visible(p: Path) -> str:
    h = p.read_text()
    h = re.sub(r"<pre.*?</pre>|<details.*?</details>", " ", h, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h)).split())


def main() -> int:
    bad = 0
    claim = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page.FIXTURES)).split())
    why = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", page.WHY)).split())

    for name in PAGES:
        f = PUB / name
        if not f.exists():
            print(f"  MISS  {name} does not exist")
            bad += 1
            continue
        text = visible(f)
        if claim not in text:
            print(f"  MISS  {name}: canonical claim absent")
            bad += 1
        if why not in text:
            print(f"  MISS  {name}: the reason (page.WHY) absent")
            bad += 1
        for pattern, reason in BANNED:
            for m in set(re.findall(pattern, text, re.I)):
                hit = m if isinstance(m, str) else m[0]
                print(f"  BAD   {name}: {hit!r} ({reason})")
                bad += 1

    print(f"  {'content checks pass' if not bad else f'*** {bad} problem(s) ***'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
