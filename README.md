# A Config-Driven Agent Network

An exploration of [LangChain](https://python.langchain.com/) and
[LangGraph](https://langchain-ai.github.io/langgraph/): a network of specialist AI agents
coordinated by a broker, with a human approval gate on anything risky.

The point of the project is that **the network is data, not code**. The agent roster, the
routing and synthesis prompts, the demo scenarios and every agent's reply live in an XML file.
Point the loader at a different file and the same graph becomes a different business.

```python
config  = load_config("config/config_travel.xml")     # an online travel agency
network = build_network(config)
network.run("My bookings for November are down 20%. Diagnose this.")
```

Swap one path and you have a management consulting firm instead, with five different
specialists and a different definition of what counts as risky. No node changes, no edge
changes, no code changes at all.

---

## What is real and what is not

**The orchestration is real.** The LangGraph state machine, the LLM-driven routing, the
synthesis step, the risk scoring and the human-in-the-loop interrupt all genuinely execute
against `gpt-4o`.

**Every agent response is a fixture read from the XML.** No vendor API is called. The design
notes name candidate integrations (rate-shopping feeds, property management systems, flight
capacity data, ticketing systems) and mention MCP servers; **none of that is implemented.**

That is deliberate. Canned agent replies make the demo deterministic, reproducible and nearly
free to run, so the orchestration is the thing under examination rather than five API
integrations. Replacing a fixture with a real call is a one-function change in
[`agentic_network/graph.py`](agentic_network/graph.py).

This is a study of a pattern. It is not a product, and no claim here about business outcomes
is supported by evidence.

---

## How it works

A question goes to the **broker**, which decides which specialists to consult. They fan out in
parallel, each returning its data. The broker synthesises one answer and scores its risk. If
the risk rule fires, the answer stops at a **human gate** before anything is called done.

```
  question
     |
  [broker]  ------------------ decides who to consult
     |  \  \
     |   \  +--> [market scout]      events, weather
     |    +----> [revenue strategist] pricing, rates
     +---------> [content specialist] photos, description
     |
  [broker]  ------------------ synthesises, scores risk
     |
  [human approval]  ---------- only when the risk rule fires
     |
   answer
```

The risk rule itself comes from the config. In the travel network, changing prices or
publishing content needs a human. In the consulting network, it is layoffs and budget moves
over $1M.

---

## What is in this repository

| File | What it is |
|---|---|
| [`agentic_network/`](agentic_network/) | The package. Config loader, graph builder, output channels, and two entry points. |
| [`config/config_travel.xml`](config/config_travel.xml) | Five agents for a fictional online travel agency. |
| [`config/config_agency.xml`](config/config_agency.xml) | Five agents for a management consulting firm. Same graph. |
| [`notebooks/agentic_network.ipynb`](notebooks/agentic_network.ipynb) | The design notes and a runnable walkthrough, with real executed output. |
| [`tests/test_network.py`](tests/test_network.py) | Smoke tests against a stub LLM. No API key, no network, no cost. |
| [`scripts/check_key.py`](scripts/check_key.py) | Confirms your key loads and works, without printing it. |

**[Open the notebook in Colab](https://colab.research.google.com/github/johnfisher-ai/fisher-agentic-network-langgraph/blob/main/notebooks/agentic_network.ipynb)**. It clones the repo and installs
its own dependencies. You supply a key.

---

## Live site

| Page | What it holds | Status |
|---|---|---|
| **Overview** | What the network is, the agent roles, and the business framing. | Planned |
| **Architecture** | The state machine, the fan-out and fan-in, the human gate, and the config-driven design. | Planned |
| **The code** | Python and XML side by side, showing one graph serving two domains. | Planned |
| **Running it** | Install, key setup, cost, and the Colab link. | Planned |

---

## Running it

Everything runs from the repository root. The package is a flat layout, so there is no install
step for the code itself.

```bash
git clone https://github.com/johnfisher-ai/fisher-agentic-network-langgraph.git
cd fisher-agentic-network-langgraph
python3 -m pip install -r requirements.txt
```

### Your API key

The key is read from the environment and is never written into a file that gets committed.

```bash
cp .env.example .env      # then put your key in .env
python3 scripts/check_key.py
```

`.env` is git-ignored. `check_key.py` makes one tiny call and prints a masked prefix, never the
key itself. In Colab, use the key icon in the sidebar and name the secret `OPENAI_API_KEY`.

**Cost:** two `gpt-4o` calls per question, one to route and one to synthesise. A fraction of a
cent. The agents themselves cost nothing, because their answers are fixtures.

### Ask it something

```bash
python3 -m agentic_network.cli "My bookings for November are down 20%. Diagnose this."
python3 -m agentic_network.cli -c config/config_agency.xml "Where are the post-merger synergies?"
python3 -m agentic_network.cli --verbose --yes "Should I match my competitor's rates?"
```

`--verbose` shows the agent trace. `--yes` and `--no` answer the human gate without prompting,
which is what lets the notebook run unattended.

### The desktop client

```bash
python3 -m agentic_network.gui
```

A tkinter window with a chat pane and a live trace log, where a real person answers the
approval gate. It needs a display, so it does not run in Colab; the notebook uses the headless
path throughout.

### The tests

```bash
python3 -m tests.test_network
```

Nineteen checks against a stub LLM. No key needed, nothing sent anywhere, no cost.

---

## Writing your own network

A config needs three things: the two prompts the broker uses, a list of scenarios with keywords,
and the agents. An agent declares what it is good at, which is what the router sees, plus a
canned reply per scenario.

```xml
<agent id="market_scout" name="Market Scout">
    <description>events, weather</description>
    <mock_data default="No significant market alerts.">
        <response scenario_id="3">{"event": "Stadium concert", "impact": "demand spike"}</response>
    </mock_data>
</agent>
```

Scenario keywords match on word boundaries with an optional plural, so `crib` matches "cribs".
First match in document order wins, so order scenarios from most specific to least.

---

## What building it corrected

Turning the prototype into a package surfaced defects that had been invisible while everything
sat in one cell. They are worth listing, because most of them failed silently.

- **The human gate delivered different text than the human approved.** Approval routed back
  through the broker, which re-ran synthesis, so the answer was a second generation that
  sometimes carried a different risk verdict than the one shown for approval. In a system whose
  whole purpose is authorising an action, the authorised text was not the delivered text. The
  gate is now terminal and returns the proposal verbatim.
- **Keywords matched as substrings**, so `ai` matched *retail*, *explain*, *email* and
  *available*, routing those questions to the wrong scenario with no sign it had happened.
- **A bare `except:`** around the router's JSON parse made a malformed reply indistinguishable
  from a real routing decision.
- **Two fixtures had duplicate JSON keys**, so one value in each was silently unreachable.
- **The notebook opened a GUI window and blocked**, because `__name__` really is `"__main__"`
  inside a notebook, and it failed outright in Colab, which has no display.

Each is covered by a test.

---

## Built with

Python 3.14, `langgraph` 1.0.10, `langchain` 1.2.10, `langchain-openai` 1.1.11, `gpt-4o`,
and tkinter for the desktop client. Versions are pinned in
[`requirements.txt`](requirements.txt).

---

## License

The **code** in this repository is released under the [MIT License](LICENSE): the package, the
notebook, the configs, and everything under `tools/` and `public/`.

"Ofishal" is a fictional company invented for the demo. The real products named in the design
notes as candidate integrations belong to their respective owners and are referenced only as
examples of what such a network could connect to.

---

## Credits

Code and site by John Fisher, [johnfisher-ai](https://github.com/johnfisher-ai).

Part of a set of public repositories covering applied statistics, data science and AI
engineering.
