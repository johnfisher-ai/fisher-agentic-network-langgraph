"""Build public/code.html.

The file map, the config format, and the two configurations set against each
other. Line counts are measured, and every listing is read from disk.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic_network import load_config                    # noqa: E402
from tools import excerpt, hl, page                        # noqa: E402

TRAVEL = load_config(ROOT / "config/config_travel.xml")
AGENCY = load_config(ROOT / "config/config_agency.xml")

MODULES = [
    ("agentic_network/config.py",   "Parses a config into dataclasses and picks a scenario."),
    ("agentic_network/graph.py",    "Builds and compiles the state machine. The core."),
    ("agentic_network/channels.py", "Where output goes and where human answers come from."),
    ("agentic_network/cli.py",      "Headless entry point. What the notebook and Colab use."),
    ("agentic_network/gui.py",      "The tkinter desktop client."),
    ("agentic_network/__init__.py", "The public surface: three names."),
    ("tests/test_network.py",       "Nineteen checks against a stub model. No key needed."),
    ("config/config_travel.xml",    "The travel partner network."),
    ("config/config_agency.xml",    "The consulting firm."),
]


def loc(rel: str) -> int:
    return len((ROOT / rel).read_text().splitlines())


def build():
    rows = "".join(
        f'<tr><td class="item"><code>{r}</code></td>'
        f'<td class="num">{loc(r)}</td><td>{d}</td></tr>'
        for r, d in MODULES
    )
    total = sum(loc(r) for r, _ in MODULES)

    read = lambda p: (ROOT / p).read_text()

    run_link = ('<a href="run.html">Running it</a>'
                if (page.PUBLIC / "run.html").exists() else "the README")

    body = page.head(
        filename="code.html",
        title="The code",
        tab_title="The code · A Config-Driven Agent Network",
        description=(
            "The package, the config format, and the two XML files that turn one LangGraph "
            "state machine into a travel partner network or a consulting firm."
        ),
        card_title="The code behind a config-driven agent network",
        card_desc=(
            "Six Python modules and two XML files. The Python never changes between domains; "
            "the XML is the whole difference."
        ),
        kicker="Every file, and what it does",
        byline="Python and XML, with the two configurations set against each other.",
    )

    body += f"""
  <section>
    <p class="lede">The project is small on purpose. Six Python modules hold the machinery, and
    two XML files hold everything that makes one network different from another. The Python
    does not know which domain it is running.</p>

    <div class="scroll">
      <table class="stats">
        <thead><tr><th>File</th><th class="num">Lines</th><th>What it does</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr><td class="item"><strong>Total</strong></td>
          <td class="num"><strong>{total}</strong></td><td></td></tr></tfoot>
      </table>
    </div>
  </section>

  <section>
    <h2>What a config declares</h2>
    <p>Four things: the prompt the broker routes with, the prompt it synthesises and scores risk
    with, the scenarios that select which fixture each agent returns, and the agents
    themselves.</p>

    {hl.wrap(excerpt.xml_element("config/config_travel.xml", "agent", "id", "revenue_strategist"),
             "xml", name="config/config_travel.xml", note="one agent")}

    <p>The <code>description</code> is the only thing the broker sees when it decides who to
    consult, so it is doing real work despite being three words. Each
    <code>response</code> is the fixture that agent returns for one scenario, and
    <code>default</code> covers anything unmatched.</p>

    <p>Scenarios are keyword lists. A question is tested against them in document order and the
    first hit wins, so the most specific scenario goes first.</p>

    {hl.wrap(excerpt.between("config/config_travel.xml", "<scenarios>", "</scenarios>"),
             "xml", name="config/config_travel.xml", note="all five scenarios")}
  </section>

  <section>
    <h2>Two configurations</h2>
    <p>Here is the whole difference between an online travel agency and a management consulting
    firm, as far as this codebase is concerned.</p>

    <div class="scroll">
      <table class="stats">
        <thead><tr><th></th><th>config_travel.xml</th><th>config_agency.xml</th></tr></thead>
        <tbody>
          <tr><td class="item">Agents</td>
              <td>{len(TRAVEL.agents)}</td><td>{len(AGENCY.agents)}</td></tr>
          <tr><td class="item">Roster</td>
              <td>{"<br>".join(a.name for a in TRAVEL.agents.values())}</td>
              <td>{"<br>".join(a.name for a in AGENCY.agents.values())}</td></tr>
          <tr><td class="item">Scenarios</td>
              <td>{len(TRAVEL.scenarios)}</td><td>{len(AGENCY.scenarios)}</td></tr>
          <tr><td class="item">Fixtures</td>
              <td>{sum(len(a.replies) for a in TRAVEL.agents.values())}</td>
              <td>{sum(len(a.replies) for a in AGENCY.agents.values())}</td></tr>
          <tr><td class="item">Lines of Python that differ</td>
              <td colspan="2"><strong>0</strong></td></tr>
        </tbody>
      </table>
    </div>

    <h3>The routing prompt</h3>
    <p>The travel network gives the model almost nothing. The consulting network gives it a
    role, which changes how it reads an ambiguous question.</p>
    <div class="side">
      {hl.wrap(TRAVEL.router_prompt, "xml", name="travel")}
      {hl.wrap(AGENCY.router_prompt, "xml", name="agency")}
    </div>

    <h3>The risk rule</h3>
    <p>This is the one that matters most, because it decides when a person is interrupted. It is
    prose in a prompt, not a policy engine, and the model is asked to apply it to its own
    recommendation.</p>
    <div class="side">
      {hl.wrap(TRAVEL.synthesis_prompt, "xml", name="travel")}
      {hl.wrap(AGENCY.synthesis_prompt, "xml", name="agency")}
    </div>

    <p>Prices and published content in one; layoffs, restructuring and budget moves over $1M in
    the other. Same gate, same graph, same code path.</p>
  </section>

  <section>
    <h2>The whole thing</h2>
    <p>Both configs and the module that turns them into a graph, in full.</p>

    {hl.collapsed("config/config_travel.xml, " + str(loc("config/config_travel.xml")) + " lines",
                  read("config/config_travel.xml"), "xml", name="config/config_travel.xml")}
    {hl.collapsed("config/config_agency.xml, " + str(loc("config/config_agency.xml")) + " lines",
                  read("config/config_agency.xml"), "xml", name="config/config_agency.xml")}
    {hl.collapsed("agentic_network/graph.py, " + str(loc("agentic_network/graph.py")) + " lines",
                  read("agentic_network/graph.py"), "python", name="agentic_network/graph.py")}
    {hl.collapsed("agentic_network/config.py, " + str(loc("agentic_network/config.py")) + " lines",
                  read("agentic_network/config.py"), "python", name="agentic_network/config.py")}
    {hl.collapsed("agentic_network/channels.py, " + str(loc("agentic_network/channels.py")) + " lines",
                  read("agentic_network/channels.py"), "python", name="agentic_network/channels.py")}

    <p>To run any of it, see {run_link}.</p>
  </section>
"""
    body += page.foot("code.html")
    page.write("code.html", body)


if __name__ == "__main__":
    build()
