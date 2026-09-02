"""Record real CLI output so the Running It page can quote it.

This is the one build stage that needs an API key. It writes tools/derived/runs.json,
which is committed, so every page rebuilds on a machine with no key and no network.

    python3 tools/capture_runs.py
"""

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic_network import ConsoleChannel, build_network, load_config   # noqa: E402
from agentic_network.cli import load_env                                 # noqa: E402

DERIVED = ROOT / "tools/derived"

RUNS = [
    ("low_risk", "config/config_travel.xml", True,
     "Check the recent guest reviews and tell me the general sentiment.",
     True, "A question that only reports. No approval needed."),
    ("high_risk", "config/config_travel.xml", False,
     "My bookings for November are down 20%. Diagnose this.",
     True, "A recommendation to change prices. The gate fires."),
    ("rejected", "config/config_travel.xml", False,
     "My competitor dropped their rates. Should I match them?",
     False, "The same kind of question, with the human declining."),
    ("agency", "config/config_agency.xml", True,
     "Our client has massive supply chain delays from overseas suppliers.",
     True, "The other config. Same command, same code."),
]


def main() -> None:
    load_env()
    out = {}
    for key, cfg, verbose, question, approve, blurb in RUNS:
        net = build_network(
            load_config(ROOT / cfg),
            channel=ConsoleChannel(verbose=verbose, auto_approve=approve),
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            net.run(question)
        cmd = f"python3 -m agentic_network.cli {'--verbose ' if verbose else ''}" \
              f"{'--yes ' if approve else '--no '}" \
              f"{'' if cfg.endswith('travel.xml') else f'-c {cfg} '}" \
              f'"{question}"'
        out[key] = {"cmd": cmd, "blurb": blurb, "output": buf.getvalue().rstrip()}
        print(f"  captured {key}: {len(out[key]['output'])} chars")

    DERIVED.mkdir(parents=True, exist_ok=True)
    (DERIVED / "runs.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"  wrote tools/derived/runs.json")


if __name__ == "__main__":
    main()
