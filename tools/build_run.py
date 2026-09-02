"""Build public/run.html.

Terminal transcripts come from tools/derived/runs.json, captured by
tools/capture_runs.py against the live API. That is the only build stage needing
a key, and its output is committed, so this page rebuilds without one.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentic_network import load_config                    # noqa: E402
from tools import hl, page                                 # noqa: E402

RUNS = json.loads((ROOT / "tools/derived/runs.json").read_text())
REQS = [l for l in (ROOT / "requirements.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")]
NCHECKS = 19


def transcript(key: str) -> str:
    r = RUNS[key]
    return (f'<p>{r["blurb"]}</p>'
            + hl.wrap(r["cmd"], "text", name="command")
            + hl.wrap(r["output"], "text", name="output", note="a real run", clip=True))


def build():
    sh = lambda s, **kw: hl.wrap(s, "text", **kw)

    body = page.head(
        filename="run.html",
        title="Running it",
        tab_title="Running it · A Config-Driven Agent Network",
        description=(
            "Clone, install, supply an API key three different ways, and run the agent network "
            "from a terminal, a desktop window, or Colab. Tests run without a key."
        ),
        card_title="Run the agent network yourself",
        card_desc=(
            "Install, key setup, and what it costs. Two calls to the model per question, a "
            "fraction of a cent. The test suite needs no key at all."
        ),
        kicker="Clone it and ask it something",
        byline="Install, keys, cost, and the three ways to run it.",
    )

    body += f"""
  <section>
    <p class="lede">Everything runs from the repository root, and the package needs no install
    step of its own. The only thing you have to supply is an OpenAI key, and only for the two
    calls the broker makes per question. The test suite runs without one.</p>
  </section>

  <section>
    <h2>Get it</h2>
    <p>Python 3.10 or newer, which is what the LangChain packages require. Developed and tested
    on 3.14.</p>

    {sh('''git clone https://github.com/johnfisher-ai/fisher-agentic-network-langgraph.git
cd fisher-agentic-network-langgraph
python3 -m pip install -r requirements.txt''', name="shell")}

    <p>Four dependencies, pinned to the versions this was built against:</p>
    {sh(chr(10).join(REQS), name="requirements.txt")}

    <p>Use <code>python3 -m pip</code> rather than <code>pip</code>. It guarantees the install
    lands in the same interpreter that will run the code, which is the difference between
    working and a confusing import error on a machine with more than one Python.</p>
  </section>

  <section>
    <h2>Your API key</h2>
    <p>The key is read from the environment. It is never written into a file that gets
    committed, and nothing in the project prints it.</p>

    <p><strong>A .env file</strong>, which is the easiest locally. It is listed on the first
    line of <code>.gitignore</code>.</p>
    {sh('''cp .env.example .env
# then put your key in .env:
#     OPENAI_API_KEY=sk-...''', name="shell")}

    <p><strong>Your shell</strong>, if you would rather not have the file at all.</p>
    {sh("export OPENAI_API_KEY=sk-...", name="shell")}

    <p><strong>Colab</strong>: the key icon in the left sidebar, with the secret named
    <code>OPENAI_API_KEY</code>. The notebook picks it up without any edit.</p>

    <p>Check it worked. This makes one tiny call and prints a masked prefix, never the key
    itself.</p>
    {sh("python3 scripts/check_key.py", name="shell")}
    {sh('''loaded: sk-proj-abc...WXYZ  (length 164)
live call: ok
PASS - the new key works.''', name="output")}
  </section>

  <section>
    <h2>What it costs</h2>
    <p>Two calls to <code>gpt-4o</code> per question: one to choose which specialists to
    consult, one to synthesise their findings and score the risk. A fraction of a cent.</p>
    <p>The specialists themselves cost nothing. Their answers are fixtures read from the config
    file, so the number of agents consulted does not change the bill.</p>
  </section>

  <section>
    <h2>Ask it something</h2>
    {transcript("low_risk")}
    {transcript("high_risk")}

    <p><code>--yes</code> and <code>--no</code> answer the approval gate without prompting,
    which is what lets a notebook run unattended. Leave both off and it asks.</p>

    {transcript("rejected")}
    {transcript("agency")}

    <p>Note what changed in that last one: a config path. The command, the code and the graph
    are identical.</p>
  </section>

  <section>
    <h2>The desktop client</h2>
    <p>A tkinter window with a chat pane and a live agent trace log, where the approval gate is
    answered by a person rather than a flag.</p>
    {sh('''python3 -m agentic_network.gui
python3 -m agentic_network.gui --config config/config_agency.xml''', name="shell")}
    <p>It needs a display, so it does not run in Colab or over a plain SSH session. In those
    places use the headless path above.</p>
  </section>

  <section>
    <h2>The notebook</h2>
    <p>The notebook carries the design notes and a runnable walkthrough. On Colab it clones the
    repository and installs its own dependencies, so the only thing you supply is the key.</p>
    <p class="cta">
      <a href="{page.COLAB}">Open in Colab</a>
      <a href="{page.REPO}/blob/main/notebooks/agentic_network.ipynb">Notebook on GitHub</a>
    </p>
  </section>

  <section>
    <h2>The tests need no key</h2>
    <p>{NCHECKS} checks against a stub model: nothing is sent anywhere and nothing is spent.
    They cover scenario matching, both branches of the approval gate, malformed router output,
    and both configurations.</p>
    {sh("python3 -m tests.test_network", name="shell")}
    <p>This is the quickest way to confirm a clone is working before you decide whether to
    spend anything on a key.</p>
  </section>

  <section>
    <h2>Writing your own network</h2>
    <p>Copy either config and edit it. A network needs the two broker prompts, a list of
    scenarios with keywords, and the agents, each with a description and one canned reply per
    scenario. The <a href="code.html">code page</a> walks through the format.</p>
    {sh('''cp config/config_travel.xml config/config_mine.xml
python3 -m agentic_network.cli -c config/config_mine.xml "your question here"''', name="shell")}
    <p>Nothing in <code>agentic_network/</code> needs to change. If the file parses and declares
    at least one agent, it will run.</p>
  </section>
"""
    body += page.foot()
    page.write("run.html", body)


if __name__ == "__main__":
    build()
