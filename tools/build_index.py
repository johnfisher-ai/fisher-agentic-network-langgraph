"""Build public/index.html, the overview page.

Every count on the page is read from the config files, not typed in.
"""

import sys
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic_network import load_config           # noqa: E402
from tools import diagram, page                   # noqa: E402

TRAVEL = load_config(ROOT / "config/config_travel.xml")
AGENCY = load_config(ROOT / "config/config_agency.xml")


def counts():
    fixtures = sum(len(a.replies) for c in (TRAVEL, AGENCY) for a in c.agents.values())
    return {
        "agents": len(TRAVEL.agents) + len(AGENCY.agents),
        "configs": 2,
        "scenarios": len(TRAVEL.scenarios) + len(AGENCY.scenarios),
        "fixtures": fixtures,
    }


ROLES = [
    ("Market Scout", "Watches events, weather and travel demand, so a booking dip can be traced to a cause outside the property."),
    ("Revenue Strategist", "Compares your rates against the competitive set and recommends a move, with the reasoning attached."),
    ("Content Specialist", "Audits the listing: photographs, description, amenity tags, and whether it will surface in the right filters."),
    ("Guest Experience", "Reads reviews for sentiment and recurring operational complaints."),
    ("Facilities Manager", "Knows the physical state of the property: housekeeping, maintenance, what is in the store cupboard."),
]


def build():
    c = counts()
    arch = page.PUBLIC / "architecture.html"
    arch_link = (' The <a href="architecture.html#gate">architecture page</a> has the detail.'
                 if arch.exists() else "")
    d = diagram.network_flow(
        [("Market Scout", "events, weather"),
         ("Revenue", "pricing, rates"),
         ("Content", "listing quality"),
         ("Guest Exp.", "reviews"),
         ("Facilities", "maintenance")],
        "One question through the network",
        "The broker decides who to consult, waits, synthesises, and scores the risk of its own recommendation.",
    )
    swap = diagram.config_swap(
        "Two businesses, one graph",
        "Nothing below the configs changes. No node, no edge, no line of Python.",
        ("config_travel.xml",
         ["Market Scout, Revenue Strategist,", "Content Specialist, Guest Experience,",
          "Facilities Manager", "", "Risk rule: changing prices or", "publishing content needs a human."]),
        ("config_agency.xml",
         ["Market Analyst, Financial Modeler,", "Organizational Strategist,",
          "Operations Specialist, Risk & Compliance", "", "Risk rule: layoffs, restructuring or",
          "budget moves over $1M need a human."]),
    )

    role_cards = "".join(
        f'<div class="card"><h3>{esc(n)}</h3><p>{esc(t)}</p></div>' for n, t in ROLES
    )

    body = page.head(
        filename="index.html",
        title="A Config-Driven Agent Network",
        tab_title="A Config-Driven Agent Network",
        description=(
            "A LangGraph multi-agent network where the agent roster, prompts and risk rules "
            "live in XML. Swap the config and the same graph becomes a different business."
        ),
        card_title="A Config-Driven Agent Network",
        card_desc=(
            "Specialist agents coordinated by a broker, with a human approval gate on anything "
            "risky. The roster lives in XML, so one graph serves two different businesses."
        ),
        kicker="An exploration of LangChain and LangGraph",
        byline='By John Fisher. A working prototype, with the orchestration live and the agent data mocked.',
    )

    body += f"""
  <section>
    <p class="lede">A network of specialist AI agents, coordinated by a broker, with a human
    approval gate on anything consequential. The point of the project is that the network is
    <strong>data, not code</strong>: the agent roster, the routing prompts, the demo scenarios
    and the definition of what counts as risky all live in an XML file. Point the loader at a
    different file and the same graph becomes a different business.</p>

    <div class="figures">
      <div><span class="n">{c['configs']}</span><span class="l">agent networks defined</span></div>
      <div><span class="n">{c['agents']}</span><span class="l">agents across both</span></div>
      <div><span class="n">{c['scenarios']}</span><span class="l">demo scenarios</span></div>
      <div><span class="n">0</span><span class="l">code changes to swap domain</span></div>
    </div>

    <div class="note">
      <p><strong>What is real, and what is not.</strong> {page.FIXTURES}
      The design notes name candidate integrations, rate-shopping feeds, property management
      systems, flight capacity data; none of them are built.</p>
      <p>That is deliberate. Canned agent replies keep the demo deterministic and nearly free to
      run, so the orchestration is the thing under examination rather than five integrations.
      This is a study of a pattern, not a product, and nothing here evidences a business
      outcome.</p>
    </div>
  </section>

  <section>
    <h2>How a question moves</h2>
    <p>A partner states a problem in their own words. They do not choose an agent, and they do
    not need to know the roster exists. The broker reads the intent, decides which specialists
    are relevant, and delegates. The specialists run in parallel and report back. The broker
    then does the part that makes the network worth having: it combines findings that no single
    agent could have reached alone, and it scores the risk of its own recommendation.</p>

    <figure>
      <div class="figbox">{d}</div>
      <figcaption>Figure 1. The broker fans out to the specialists it selected, fans back in, and
      routes to a human only when its own risk rule fires. Two calls to the model per question,
      one to route and one to synthesise; the specialists cost nothing because their answers are
      fixtures.</figcaption>
    </figure>
  </section>

  <section>
    <h2>The specialists</h2>
    <p>Each agent advertises what it is good at. That description is the only thing the broker
    sees when it decides who to consult, which means adding an agent is a matter of describing
    it well, not of editing a router.</p>
    <div class="cards">{role_cards}</div>
  </section>

  <section>
    <h2>The same code, a different business</h2>
    <p>The travel network is one configuration. Here is a second: a management consulting firm,
    with five different specialists, a different router prompt, and a different definition of
    risk. It runs on the same graph, loaded the same way, with nothing swapped but a path.</p>

    <figure>
      <div class="figbox">{swap}</div>
      <figcaption>Figure 2. Two configurations, one graph. The specialists, the prompts, the
      scenarios and the risk rule are all data.</figcaption>
    </figure>

    <p>This is the part worth taking away. In most agent frameworks the roster is expressed in
    code: a class per agent, a router with a branch per destination, edges wired by hand. That
    works until the roster changes. Here, the graph is constructed at load time from whatever
    the config declares, so a new agent is a new XML block and a new domain is a new file.</p>
  </section>

  <section id="gate">
    <h2>The human gate</h2>
    <p>Some recommendations are cheap to be wrong about. Reporting that guest sentiment is
    neutral costs nothing if it is mistaken. Dropping your room rate by $50 is different, and so
    is a recommendation to reduce headcount by ten percent. The synthesis step scores each
    answer against a rule from the config, and anything above the line stops for a person.</p>

    <p>Approval must return the approved text. It is tempting to route an approval back
    through the synthesis step, and that quietly defeats the gate: what the user receives is
    then a second generation, which can differ from what they authorised. Here the gate is
    terminal and hands back the proposal verbatim, with a test asserting that it appears
    unchanged in the final answer.</p>

      <p>Nothing about a regenerated answer looks wrong from outside: the system stops, a
      person approves, and a plausible answer appears.{arch_link}</p>
  </section>

"""
    body += page.foot("index.html")
    page.write("index.html", body)


if __name__ == "__main__":
    build()
