"""Fill the social card templates and render them.

Two cards, two sizes, and they are not interchangeable:

  linkedin-card.png  1200x627  Open Graph, LinkedIn, Slack, Twitter. Copied to
                               public/assets/img/social-card.png, which every page references.
  github-card.png    1280x640  The repository preview. Uploaded by hand under
                               Settings > Social preview; GitHub exposes no API for it.

Numbers come from the config files, the same source the overview page uses, so a
card can never drift from the page.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agentic_network import load_config            # noqa: E402

SOCIAL = ROOT / "assets/social"
TRAVEL = load_config(ROOT / "config/config_travel.xml")
AGENCY = load_config(ROOT / "config/config_agency.xml")

AGENTS = len(TRAVEL.agents) + len(AGENCY.agents)

VALUES = {
    "TITLE": "A Config-Driven Agent Network",
    "SUBTITLE": "Specialist agents coordinated by a broker, with a human approval gate on "
                "anything risky. The roster lives in XML, so one graph serves two businesses.",
    "KICKER": "LangChain · LangGraph · Python",

    # LinkedIn card: three stat tiles
    "STAT1_N": "2",           "STAT1_L": "agent networks, one graph",
    "STAT2_N": str(AGENTS),   "STAT2_L": "agents across both",
    "STAT3_N": "0",           "STAT3_L": "code changes to swap domain",
    "FOOTNOTE": "The orchestration runs. Every agent answer is written into the config: nothing is fetched.",

    # GitHub card: four feature cards and four tags
    "CARD1_T": "Broker and specialists",
    "CARD1_D": "One question, fanned out to the agents that matter, synthesised into one answer.",
    "CARD2_T": "Human in the loop",
    "CARD2_D": "Risky recommendations stop for a person, and the approved text is what ships.",
    "CARD3_T": "The roster is data",
    "CARD3_D": "Agents, prompts, scenarios and the risk rule all live in an XML config file.",
    "CARD4_T": "Runs from a clone",
    "CARD4_D": "A Colab notebook, a CLI, a desktop client, and tests that need no API key.",
    "TAG1": "LangGraph", "TAG2": "Multi-agent", "TAG3": "Human-in-the-loop", "TAG4": "Python",
}


def fill(name: str) -> Path:
    src = (SOCIAL / name).read_text()
    for k, v in VALUES.items():
        src = src.replace("{{" + k + "}}", v)
    leftover = [t for t in ("{{",) if t in src]
    if leftover:
        import re
        raise SystemExit(f"  unfilled placeholders in {name}: {set(re.findall(r'{{[A-Z0-9_]+}}', src))}")
    out = SOCIAL / ("_filled_" + name)
    out.write_text(src)
    return out


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shot(html: Path, out: Path, w: int, h: int) -> None:
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--screenshot={out}",
         f"--window-size={w},{h}", f"file://{html}"],
        check=True, capture_output=True,
    )


def main() -> None:
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found at {CHROME}")
    jobs = [("card-linkedin.html", "linkedin-card.png", 1200, 627),
            ("card-github.html",   "github-card.png",   1280, 640)]
    for tpl, png, w, h in jobs:
        filled = fill(tpl)
        shot(filled, SOCIAL / png, w, h)
        filled.unlink()
        print(f"  {png}  {w}x{h}")

    img = ROOT / "public/assets/img"
    img.mkdir(parents=True, exist_ok=True)
    (img / "social-card.png").write_bytes((SOCIAL / "linkedin-card.png").read_bytes())
    print("  copied linkedin-card.png -> public/assets/img/social-card.png")


if __name__ == "__main__":
    main()
