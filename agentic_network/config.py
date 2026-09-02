"""Load an agent network definition from XML.

One XML file describes a whole network: the prompt the broker uses to route, the
prompt it uses to synthesise, the demo scenarios, and for each agent its identity,
its advertised capability and its canned reply per scenario.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Agent:
    """One specialist in the network."""

    id: str
    name: str
    description: str
    default_reply: str
    replies: dict[int, str] = field(default_factory=dict)

    def reply_for(self, scenario_id: int) -> str:
        """The fixture this agent returns for a scenario.

        Every reply is canned. No agent calls a real API; see the project README.
        """
        return self.replies.get(scenario_id, self.default_reply)


@dataclass
class Scenario:
    """A demo situation, selected by keyword match against the user's question."""

    id: int
    keywords: list[str]


@dataclass
class NetworkConfig:
    router_prompt: str
    synthesis_prompt: str
    scenarios: list[Scenario]
    default_scenario: int
    agents: dict[str, Agent]

    def scenario_for(self, prompt: str) -> int:
        """Pick a scenario by keyword.

        Keywords match on word boundaries with an optional plural, so "crib"
        matches "cribs" but "ai" no longer matches "retail", "explain" or "email".
        An earlier substring version of this routed those to the wrong scenario
        silently. First match in document order wins, so order the scenarios from
        most to least specific.
        """
        text = prompt.lower()
        for sc in self.scenarios:
            for kw in sc.keywords:
                if re.search(rf"\b{re.escape(kw)}(?:s|es)?\b", text):
                    return sc.id
        return self.default_scenario

    def roster(self) -> str:
        """The agent list as the router prompt wants to see it."""
        return "\n".join(f"- {a.id} ({a.description})" for a in self.agents.values())


def _text(node, path: str) -> str:
    found = node.find(path)
    if found is None or found.text is None:
        raise ValueError(f"config is missing required element: {path}")
    return found.text.strip()


def load_config(xml_path: str | Path) -> NetworkConfig:
    """Parse an agent network from XML."""
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"No config at {xml_path}")

    root = ET.parse(xml_path).getroot()

    scenarios: list[Scenario] = []
    default_scenario = 1
    for sc in root.findall("./scenarios/scenario"):
        sc_id = int(sc.get("id"))
        if sc.get("default") == "true":
            default_scenario = sc_id
        scenarios.append(
            Scenario(sc_id, [k.text.strip().lower() for k in sc.findall("keyword") if k.text])
        )

    agents: dict[str, Agent] = {}
    for ag in root.findall("./agents/agent"):
        data = ag.find("mock_data")
        agents[ag.get("id")] = Agent(
            id=ag.get("id"),
            name=ag.get("name"),
            description=_text(ag, "description"),
            default_reply=data.get("default", ""),
            replies={
                int(r.get("scenario_id")): (r.text or "").strip()
                for r in data.findall("response")
            },
        )

    if not agents:
        raise ValueError(f"{xml_path} defines no agents")

    return NetworkConfig(
        router_prompt=_text(root, "./prompts/router_prompt"),
        synthesis_prompt=_text(root, "./prompts/synthesis_prompt"),
        scenarios=scenarios,
        default_scenario=default_scenario,
        agents=agents,
    )
