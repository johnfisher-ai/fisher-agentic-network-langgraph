"""The LangGraph state machine: broker, specialists, and a human gate.

Shape of a run:

    user question
        -> broker            decides which specialists to consult
        -> specialists       fan out in parallel, each returns its canned reply
        -> broker            synthesises one answer and scores its risk
        -> human_approval    only when the risk score says so
        -> END

Every node is generated from the config, so the roster is data rather than code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from .channels import Channel, ConsoleChannel
from .config import NetworkConfig


def _merge(left: dict | None, right: dict | None) -> dict:
    """Reducer letting parallel agent nodes write into one dict without clobbering."""
    return {**(left or {}), **(right or {})}


class AgentState(TypedDict, total=False):
    input: str
    scenario_id: int
    broker_plan: list[str]
    agent_outputs: Annotated[dict[str, str], _merge]
    final_response: str
    requires_approval: bool
    approval_decision: str


def _default_llm():
    """A ChatOpenAI reading its key from the environment.

    Imported lazily so the rest of the package can be used, and tested, without
    langchain_openai installed or a key present.
    """
    from langchain_openai import ChatOpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and put your key "
            "there, or export it in your shell. See scripts/check_key.py."
        )
    return ChatOpenAI(model="gpt-4o", temperature=0)


@dataclass
class Network:
    """A compiled network, ready to answer questions."""

    config: NetworkConfig
    channel: Channel
    app: Any

    def run(self, question: str, scenario_id: int | None = None) -> str:
        """Answer one question. Returns the final text."""
        if scenario_id is None:
            scenario_id = self.config.scenario_for(question)
        self.channel.log(f"scenario {scenario_id} selected for: {question!r}")
        state = self.app.invoke(
            {"input": question, "scenario_id": scenario_id, "agent_outputs": {}}
        )
        return state.get("final_response", "")


def build_network(
    config: NetworkConfig,
    llm=None,
    channel: Channel | None = None,
) -> Network:
    """Turn a config into a runnable network."""
    llm = llm or _default_llm()
    channel = channel or ConsoleChannel()

    def specialist(agent_id: str):
        agent = config.agents[agent_id]

        def node(state: AgentState) -> dict:
            reply = agent.reply_for(state["scenario_id"])
            channel.status(f"Consulting {agent.name} ...")
            channel.log(f"{agent.name} returned: {reply}")
            return {"agent_outputs": {agent.name: reply}}

        return node

    def broker(state: AgentState) -> dict:
        outputs = state.get("agent_outputs") or {}

        if outputs:
            channel.status("Synthesising and scoring risk ...")
            prompt = (
                config.synthesis_prompt
                .replace("{user_input}", state["input"])
                .replace("{agent_data}", json.dumps(outputs))
            )
            answer = llm.invoke([SystemMessage(content=prompt)]).content
            needs_approval = "RISK: YES" in answer.upper()
            channel.log(f"synthesis complete, requires_approval={needs_approval}")
            if not needs_approval:
                channel.chat(answer)
                channel.status("Ready")
            return {"final_response": answer, "requires_approval": needs_approval}

        channel.status("Analysing intent ...")
        system = config.router_prompt.replace("{agent_list}", config.roster())
        raw = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=state["input"])]
        ).content
        plan = _parse_plan(raw, config, channel)
        channel.status(f"Delegating to {', '.join(plan)}")
        return {"broker_plan": plan}

    def human_approval(state: AgentState) -> dict:
        proposal = state["final_response"]
        channel.status("Waiting for human approval ...")
        channel.log(f"proposal put to a human:\n{proposal}")

        if channel.ask_approval(proposal):
            channel.log("human approved")
            # Deliver exactly the text that was approved. Routing back through the
            # broker would re-run synthesis and hand the user a different answer
            # from the one they authorised.
            final = proposal + "\n\n[STATUS: APPROVED BY HUMAN, EXECUTED]"
            channel.chat(final)
            channel.status("Ready")
            return {"approval_decision": "APPROVED", "final_response": final}

        channel.log("human rejected")
        final = "ACTION CANCELLED. The human operator rejected the proposal.\n\nWhat was proposed:\n" + proposal
        channel.chat(final)
        channel.status("Ready")
        return {"approval_decision": "REJECTED", "final_response": final}

    graph = StateGraph(AgentState)
    graph.add_node("broker", broker)
    graph.add_node("human_approval", human_approval)
    for agent_id in config.agents:
        graph.add_node(agent_id, specialist(agent_id))

    def route(state: AgentState):
        if state.get("requires_approval"):
            return "human_approval"
        if state.get("final_response"):
            return END
        return state.get("broker_plan") or [next(iter(config.agents))]

    graph.set_entry_point("broker")
    graph.add_conditional_edges(
        "broker", route, list(config.agents) + ["human_approval", END]
    )
    for agent_id in config.agents:
        graph.add_edge(agent_id, "broker")
    # The gate is terminal. Going back to the broker would re-synthesise.
    graph.add_edge("human_approval", END)

    return Network(config=config, channel=channel, app=graph.compile())


def _parse_plan(raw: str, config: NetworkConfig, channel: Channel) -> list[str]:
    """Read the router's JSON list of agent ids, and say so when it is malformed.

    Falls back to a single agent rather than raising, but logs every reason it
    did: unparseable output, a non-list, or names that are not in the roster.
    An unlogged fallback is indistinguishable from a real routing decision.
    """
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    fallback = [next(iter(config.agents))]
    try:
        plan = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        channel.log(f"router returned unparseable JSON ({exc}); falling back. Raw: {raw!r}")
        return fallback

    if not isinstance(plan, list):
        channel.log(f"router returned {type(plan).__name__}, expected a list; falling back.")
        return fallback

    known = [a for a in plan if a in config.agents]
    if unknown := [a for a in plan if a not in config.agents]:
        channel.log(f"router named agents that do not exist, ignoring: {unknown}")
    if not known:
        channel.log("router named no valid agents; falling back.")
        return fallback
    return known
