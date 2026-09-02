"""Build public/architecture.html.

Every code excerpt is pulled from the real source at build time, so the page
cannot quote code that no longer exists.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic_network import load_config                    # noqa: E402
from tools import diagram, excerpt, hl, page               # noqa: E402

TRAVEL = load_config(ROOT / "config/config_travel.xml")


def build():
    py = lambda s: hl.block(s, "python")
    xm = lambda s: hl.block(s, "xml")

    sm = diagram.state_machine(
        list(TRAVEL.agents),
        "The graph as it is compiled",
        "Node names are the agent ids from the config. Nothing here is written by hand.",
    )

    body = page.head(
        filename="architecture.html",
        title="Architecture",
        tab_title="Architecture · A Config-Driven Agent Network",
        description=(
            "How the LangGraph state machine is built from an XML config: shared state with a "
            "reducer, nodes generated at load time, and a terminal human approval gate."
        ),
        card_title="Architecture of a config-driven agent network",
        card_desc=(
            "Shared state with a reducer for parallel writes, nodes generated from config at "
            "load time, an output channel that keeps the graph front-end agnostic, and a human "
            "gate that returns exactly what was approved."
        ),
        kicker="How it is put together",
        byline="The state machine, the dynamic construction, and the gate.",
    )

    body += f"""
  <section>
    <p class="lede">The interesting constraint in this project is that the roster is not known
    when the code is written. There is no class per agent and no branch per destination. The
    graph is assembled at load time from whatever the config declares, which means the same
    module compiles a five-agent travel network or a five-agent consulting firm without knowing
    the difference.</p>
  </section>

  <section>
    <h2>Shared state, and why it needs a reducer</h2>
    <p>Every node reads and writes one state object. Most of its fields are ordinary, written by
    one node at a time. <code>agent_outputs</code> is not: the specialists run in parallel and
    all write to it at once, so LangGraph needs to be told how to combine their writes.</p>

    {py(excerpt.named("agentic_network/graph.py", "_merge"))}
    {py(excerpt.named("agentic_network/graph.py", "AgentState"))}

    <p>The <code>Annotated</code> wrapper attaches the reducer to that one field. Without it,
    parallel writes to the same key are a conflict, and with a naive reducer the specialists
    would overwrite each other and the broker would synthesise from whichever happened to
    finish last.</p>
  </section>

  <section>
    <h2>Nodes are generated, not written</h2>
    <p>Each agent in the config becomes a node through a closure that captures its own
    definition. The node itself does almost nothing: it looks up the fixture for the current
    scenario and returns it under the agent's name.</p>

    {py(excerpt.named("agentic_network/graph.py", "build_network", inner="specialist"))}

    <p>The edges are wired the same way, in a loop over the roster. The conditional edge out of
    the broker has to declare every possible destination up front, which is the one place the
    roster has to be enumerated.</p>

    {py(excerpt.between("agentic_network/graph.py",
                        'graph.set_entry_point("broker")',
                        'graph.add_edge("human_approval", END)'))}

    <figure>
      <div class="figbox">{sm}</div>
      <figcaption>Figure 1. The compiled graph for <code>config_travel.xml</code>. The node
      names are the agent ids from the XML. Dashed edges are conditional, chosen by the router
      at run time; solid edges are unconditional.</figcaption>
    </figure>
  </section>

  <section>
    <h2>Routing, and admitting when it fails</h2>
    <p>The broker asks the model which specialists to consult and expects a JSON list of agent
    ids back. Models do not always oblige, so the parser treats three failures as distinct:
    output that is not JSON, JSON that is not a list, and names that are not in the roster.</p>

    {py(excerpt.named("agentic_network/graph.py", "_parse_plan"))}

    <p>All three fall back to consulting one agent rather than raising, because a demo that
    stops on a bad parse is less useful than one that degrades. Each is logged on the way past.
    The third case matters most: a model that invents a plausible agent name produces a run that
    looks entirely successful, and without the log there is nothing to distinguish it from a
    real routing decision.</p>
  </section>

  <section>
    <h2>Scenario selection</h2>
    <p>Which fixture an agent returns depends on the scenario, matched by keyword against the
    question. It is the least clever part of the system and the place where
    imprecision is hardest to notice.</p>

    {py(excerpt.named("agentic_network/config.py", "NetworkConfig", inner="scenario_for"))}

    <p>Matching is on word boundaries with an optional plural, so <code>crib</code> catches
    "cribs" while <code>ai</code> catches "AI" and "AI-driven" but not <em>retail</em>,
    <em>explain</em> or <em>email</em>. The precision is worth the regular expression, because
    a mis-selected scenario does not raise anything: the agents return confident, well-formed
    answers about the wrong situation. First match in document order wins, so scenarios are
    ordered from most specific to least.</p>
  </section>

  <section>
    <h2>The graph does not know where its output goes</h2>
    <p>The nodes never print and never call <code>input()</code>. They talk to a channel,
    handed in when the network is built, and that is the only route anything takes out of the
    graph or back into it.</p>

    {py(excerpt.named("agentic_network/channels.py", "Channel"))}

    <p>Three implementations. <code>ConsoleChannel</code> prints and can answer the approval
    gate automatically, which is what lets the notebook run unattended.
    <code>QueueChannel</code> pushes messages onto a queue the desktop UI polls, and blocks the
    worker thread on an <code>Event</code> until a person answers. A third, used by the tests,
    records everything and never prints.</p>

    <p>That indirection is what makes the tests possible. The suite runs the real graph with a
    stub model and a recording channel: no API key, no network, no cost.</p>
  </section>

  <section id="gate">
    <h2>The human gate</h2>
    <p>The synthesis prompt asks the model to score its own recommendation, and the config
    supplies the rule. In the travel network, changing prices or publishing content needs a
    person. In the consulting network it is layoffs, restructuring, or budget moves over $1M.
    The broker sets <code>requires_approval</code> when the answer contains
    <code>RISK: YES</code>, and the router sends it to the gate.</p>

    <p>The gate is <strong>terminal</strong>. It has one outgoing edge, to <code>END</code>,
    and it hands back exactly the text it showed the human.</p>

    {py(excerpt.named("agentic_network/graph.py", "build_network", inner="human_approval"))}

    <p>That the gate does not route back into the broker is the whole design, and it is worth
    being explicit about why. The broker's first action is to check whether agent outputs
    exist. After a fan-out they do, so any path that re-enters the broker runs synthesis a
    second time and produces a fresh answer. The person would then have authorised one piece of
    text and received another, generated after they clicked yes, potentially carrying a
    different risk verdict.</p>

    <p>Nothing about that looks wrong from outside: the system stops, a person approves, and a
    plausible answer appears. An approval gate that regenerates its answer is not an approval
    gate, so the test suite asserts that the proposal text survives verbatim into the final
    output, and that synthesis runs exactly once.</p>

  <section>
    <h2>Where the fixtures sit</h2>
    <p>Each agent carries a default reply and one per scenario. The node returns a string; it
    never parses it. The model receives the fixtures as text and does the interpreting, which is
    why a fixture can be JSON-shaped without being contractually JSON.</p>

    {xm(excerpt.xml_element("config/config_travel.xml", "agent", "id", "market_scout"))}

    <p>This is the seam where a real integration would go. <code>reply_for</code> is the only
    method a specialist node calls, so an agent backed by a live API is that one method doing
    something else. Nothing above it changes: not the graph, not the routing, not the gate.</p>

    {py(excerpt.named("agentic_network/config.py", "Agent", inner="reply_for"))}
  </section>
"""
    body += page.foot("architecture.html")
    page.write("architecture.html", body)


if __name__ == "__main__":
    build()
