"""Smoke tests. No API key, no network, no cost: the LLM is a stub.

    python3 -m tests.test_network        (from the repo root)
"""

from __future__ import annotations

import json
import sys

from agentic_network import build_network, load_config
from agentic_network.channels import Channel


class StubLLM:
    """Stands in for ChatOpenAI. Returns a plan, then a canned synthesis."""

    def __init__(self, plan, verdict="RISK: NO"):
        self.plan, self.verdict, self.calls = plan, verdict, 0

    def invoke(self, messages):
        self.calls += 1
        text = messages[0].content
        if "{agent_data}" not in text and "Agent Data:" not in text:
            return type("R", (), {"content": json.dumps(self.plan)})()
        return type("R", (), {"content": f"Synthesised answer. {self.verdict}"})()


class Recorder(Channel):
    def __init__(self, approve=True):
        self.approve, self.chats, self.logs, self.proposals = approve, [], [], []

    def log(self, m): self.logs.append(m)
    def chat(self, m): self.chats.append(m)
    def ask_approval(self, p):
        self.proposals.append(p)
        return self.approve


FAILED = []


def check(label, condition, detail=""):
    print(f"  {'PASS' if condition else 'FAIL'}  {label}" + (f"   {detail}" if detail and not condition else ""))
    if not condition:
        FAILED.append(label)


def main() -> int:
    travel = load_config("config/config_travel.xml")
    agency = load_config("config/config_agency.xml")

    print("\nconfig loading")
    check("travel config has 5 agents", len(travel.agents) == 5, f"got {len(travel.agents)}")
    check("agency config has 5 agents", len(agency.agents) == 5, f"got {len(agency.agents)}")
    check("both expose a router prompt", bool(travel.router_prompt and agency.router_prompt))

    print("\nkeyword routing (the substring bug)")
    check("'november bookings' -> 1", travel.scenario_for("My bookings for November are down") == 1)
    check("'construction noise' -> 2", travel.scenario_for("There is construction noise") == 2)
    check("'cribs' matches the 'crib' keyword", travel.scenario_for("Do we have enough cribs?") == 4)
    check("'retail' no longer matches 'ai'", agency.scenario_for("our retail strategy") != 2,
          f"got {agency.scenario_for('our retail strategy')}")
    check("'explain' no longer matches 'ai'", agency.scenario_for("please explain this") != 2)
    check("'email' no longer matches 'ai'", agency.scenario_for("check the email volume") != 2)
    check("a real 'AI' mention still routes to 2", agency.scenario_for("a competitor launched an AI product") == 2)

    print("\nlow-risk path completes without a human")
    ch = Recorder()
    net = build_network(travel, llm=StubLLM(["market_scout"]), channel=ch)
    out = net.run("Check the recent guest reviews.")
    check("no approval was requested", ch.proposals == [])
    check("an answer came back", "Synthesised answer" in out)

    print("\nhigh-risk path stops for a human")
    ch = Recorder(approve=True)
    llm = StubLLM(["revenue_strategist"], verdict="RISK: YES")
    net = build_network(travel, llm=llm, channel=ch)
    out = net.run("Should I drop my rates?")
    check("approval was requested once", len(ch.proposals) == 1, f"got {len(ch.proposals)}")
    check("approved text is delivered verbatim", ch.proposals[0] in out)
    check("outcome is marked", "APPROVED BY HUMAN" in out)
    check("synthesis ran ONCE, not twice", llm.calls == 2, f"llm.calls={llm.calls} (1 route + 1 synthesis)")

    print("\nrejection is honoured")
    ch = Recorder(approve=False)
    net = build_network(travel, llm=StubLLM(["revenue_strategist"], verdict="RISK: YES"), channel=ch)
    out = net.run("Should I drop my rates?")
    check("cancelled", "CANCELLED" in out)

    print("\nmalformed router output is reported, not swallowed")
    ch = Recorder()
    net = build_network(travel, llm=StubLLM("not-a-list"), channel=ch)
    net.run("anything")
    check("fallback was logged", any("unparseable" in m or "expected a list" in m for m in ch.logs))

    print("\nsame code, second domain")
    ch = Recorder()
    net = build_network(agency, llm=StubLLM(["market_analyst", "financial_modeler"]), channel=ch)
    out = net.run("Advise on the supply chain delays.")
    check("agency network answers", "Synthesised answer" in out)

    print()
    if FAILED:
        print(f"{len(FAILED)} FAILED: {', '.join(FAILED)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
