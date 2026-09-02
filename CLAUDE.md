# fisher-agentic-network-langgraph

A working prototype of a **multi-agent network built on LangChain and LangGraph**, where the
whole agent roster, the routing prompts, the demo scenarios and every agent's canned reply are
defined in an **XML config file** rather than in code. Swap the config and the same graph becomes
a different business: `config_travel.xml` is an online travel agency's partner network,
`config_agency.xml` is a management consulting firm. Neither required a code change.

The deliverable is a public repo plus a four-page site explaining the pattern, with a Colab
notebook a reader can run themselves.

**Author: John Fisher.** Repo: `johnfisher-ai/fisher-agentic-network-langgraph`.

---

## Hard rules

- **Never push.** The author pushes with `bash scripts/push_to_github.sh "message"` and reviews
  before publishing. Commit freely; pushing is the author's.
- **Never `git commit --amend`, rebase, or rewrite history.** Always make a new follow-up commit.
  The author pushes out of band, so treat every existing commit as possibly published. Recovery
  without a force push: `git fetch`, `git reset --soft origin/main`, re-commit the delta.
- **No `Co-Authored-By` trailer** on commits.
- **On resume:** `git log --oneline -5` and confirm what is already pushed before changing anything.

### This repo is PUBLIC, and it handles an API key

- **Never commit `.env`.** It is git-ignored on the first line of `.gitignore`. `.env.example`
  is the committed template and holds a placeholder, never a real key.
- **Never print an API key**, in code, in a notebook output, in a log line, or in chat. Mask it:
  `key[:11] + "..." + key[-4:]`. `scripts/check_key.py` is the pattern to copy.
- **Never accept a key pasted into conversation.** The author sets it in `.env` themselves.
- **Before any commit that touches a notebook, check saved outputs**, not only source cells.
  A key can leak through a traceback or an echoed variable:
  `grep -o 'sk-[A-Za-z0-9_-]\{20,\}' notebooks/*.ipynb`
- The original key for this project leaked into five notebooks in plain text and was rotated on
  2026-09-02. That is why these rules exist.

---

## Layout

| Path | What it is |
|---|---|
| `agentic_network/` | The package. `config.py` loads XML, `graph.py` builds the state machine, `channels.py` decides where output goes, `cli.py` and `gui.py` are the two entry points. |
| `notebooks/agentic_network.ipynb` | The runnable demo. This is what the Colab link opens. Thin: it imports the package. |
| `tests/test_network.py` | Smoke tests with a stub LLM. No key, no network, no cost. |
| `config/config_travel.xml` | Agent network for the fictional OTA, "Ofishal". |
| `config/config_agency.xml` | Same graph, consulting firm. Proof the pattern generalises. |
| `.env.example` | Template. Copy to `.env`, which is never committed. |
| `requirements.txt` | Pinned to the versions this was developed against. |
| `scripts/check_key.py` | Confirms the key loads and works without printing it. |
| `scripts/push_to_github.sh` | Commit and push in one command. The author runs this. |
| `public/` | The site. **The only folder Pages serves.** |
| `tools/` | Build machinery. GENERATED pages come from here; never hand-edit them. |
| `.github/workflows/pages.yml` | Publishes `public/` on every push to `main`. |

The workspace **above** this repo (`../source/`, `../scratch/`) holds raw material and throwaway
work, outside git. `../source/original/` keeps pristine copies of the notebook and configs as
they arrived. Read from it freely; never commit from it.

---

## House style

- **American English.** Deliberate non-standard spellings, do not "correct" them:
  **Ofishal** (the fictional company, a play on "official"), and the agent IDs in the XML
  (`market_scout`, `revenue_strategist`, `content_specialist`, `guest_experience`,
  `facilities_manager`, `market_analyst`, `financial_modeler`, `org_strategist`,
  `operations_specialist`, `risk_compliance`).
- **No prose em-dashes.** Use commas or parentheses.
- **Prose must read human, not AI.** Avoid precious superlatives, aphoristic one-liners, writerly
  meta-flourishes, cutesy filler adverbs, and stacked negative parallelism ("not X, it's Y").
- **Say what you actually found.** No claim in prose that has not been checked against a real
  run. If output is quoted, it came from an execution, not from a draft.

---

## Build and validate

All commands run from the repo root.

```
check the key:   python3 scripts/check_key.py
run the tests:   python3 -m tests.test_network          # no API key needed
run headless:    python3 -m agentic_network.cli "My bookings for November are down 20%."
  other config:  python3 -m agentic_network.cli -c config/config_agency.xml "..."
  no prompting:  python3 -m agentic_network.cli --yes "..."   (or --no)
run the GUI:     python3 -m agentic_network.gui
rebuild pages:   bash tools/build.sh
re-run notebook: python3 -m nbconvert --to notebook --execute --inplace notebooks/agentic_network.ipynb
```

The package is a flat layout, importable from the repo root with no install step, so a reader
can clone and run. The notebook's setup cell chdirs to the root when opened from `notebooks/`.

Note: on this machine `pip` does not exist. Use `python3 -m pip`, which also guarantees the
install lands in the same interpreter that runs the code.

**Validation checklist:**

```
python3 -m tests.test_network                  passes, all checks
no API key in any tracked file, source cells AND saved outputs
0 broken local links
no prose em-dashes
notebook runs top to bottom in a fresh kernel without launching a GUI
both config files load and produce a working graph
```

---

## Traps

- **`if __name__ == "__main__"` is TRUE inside a notebook.** The original V5 notebook ended with
  `launch_app()` inside such a block, so running that cell opened the tkinter window and blocked.
  In Colab it fails outright, there is no display. FIXED: the notebook is headless throughout and
  the GUI is a separate entry point.
- **The human-in-the-loop gate returned different text than the human approved.** The original
  routed `human_approval` back to `broker`, which re-ran synthesis, so the delivered answer was a
  second generation, sometimes with a different risk verdict than the one shown for approval.
  FIXED: the gate is terminal and returns the approved text verbatim. `tests/test_network.py`
  asserts the proposal appears in the final answer and that synthesis runs once.
- **nbformat wants newlines kept.** Building cells with `text.split("\n")` drops them, so a
  multi-line cell is written as one mashed line and fails to compile. Use
  `splitlines(keepends=True)`.
- **tkinter does not run in Colab.** The GUI is a desktop-only entry point. The Colab story is
  `run_scenario()`. Do not link a GUI notebook as "open in Colab".
- **Scenario keywords were matched as substrings**, so `"ai"` in `config_agency.xml` matched
  *retail*, *explain*, *email*, *available*, *maintain* and *campaign*, and routing misfired with
  no sign it had. FIXED: word boundaries with an optional plural, so `crib` still matches "cribs".
- **Scenario matching is first-match-wins over document order**, so when two scenarios could
  match, the result depends on XML ordering rather than on relevance.
- **A bare `except:` around the router's `json.loads`** turned a malformed LLM reply into a
  silent fallback to the first agent, indistinguishable from a real decision. FIXED: it catches
  `json.JSONDecodeError`, logs the raw reply, and also reports agent names that do not exist.
- **Duplicate JSON keys in the mock data**: `config_travel.xml` had `"suggested"` twice in
  scenario 1 and `"action"` twice in scenario 4, so the first value of each was invisible.
  FIXED, and a test now parses all 50 fixtures and fails on any key collision.
- **`langchain.debug = False` is deprecated** in LangChain 1.x. This project is on 1.2.10.
  FIXED: removed, nothing set it to anything but the default.
- **Python 3.14 warns about Pydantic v1** on import. Cosmetic, comes from inside LangChain.

---

## The site

`public/` is the only folder GitHub Pages serves. Everything else in the repo is reachable
through GitHub but is never on the site host. Do not change the workflow to publish the repo
root: that is how source material ends up on a public URL by accident. After the first deploy,
confirm it:

```
curl -s -o /dev/null -w "%{http_code}\n" https://johnfisher-ai.github.io/fisher-agentic-network-langgraph/CLAUDE.md   # expect 404
curl -s -o /dev/null -w "%{http_code}\n" https://johnfisher-ai.github.io/fisher-agentic-network-langgraph/.env        # expect 404
```

Pages must be enabled once by hand, with source **GitHub Actions**. See `.github/PAGES-SETUP.md`.
The workflow header records the two failure modes that cost real time: never use "Re-run jobs"
on a Pages workflow, and a wedged deployment blocks every later one until it is cancelled.

The four pages:

| Page | Holds |
|---|---|
| `index.html` | What the network is, the agent roles, the business-value framing. |
| `architecture.html` | The LangGraph state machine, broker fan-out and fan-in, the human-in-the-loop gate, the config-driven design. |
| `code.html` | Highlighted Python and XML, side by side, showing one graph serving two domains. |
| `run.html` | Install, `.env` setup, cost expectations, the Colab link. |

The syntax highlighter in `tools/` handles SAS and R from earlier projects. This one needs
**Python and XML**.

## Look and feel

`public/assets/css/site.css` is the design system. Use its classes rather than adding one-off
styles: `.wrap`, `.kicker`, `.lede`, `.figures`, `.cards`, `.card`, `.note`, `.scroll` +
`table.stats`, `.codewrap`, `figure` + `.figbox`.

Charts are inline SVG built in `tools/chart.py`, not image files, so they follow the reader's
light or dark setting. **The palette is validated, not chosen by eye.** Re-validate before
substituting any colour.

Wide tables, diagrams and code blocks scroll inside their own container. The page body must
never scroll horizontally; check at 375px before calling a page done.

Every page carries a full metadata block: canonical, description, Open Graph, Twitter card, and
image dimensions. Social cards are built from `assets/social/` at exactly 1200x627 (LinkedIn and
Open Graph) and 1280x640 (the GitHub repo preview). If the card dimensions change, update
`og:image:width` and `og:image:height` in every page.

## Be honest about what is built

The orchestration is real: the LangGraph state machine, the LLM-driven routing, the synthesis
step, the risk scoring and the human-in-the-loop interrupt all genuinely run.

**Every agent response is a fixture read from XML.** No vendor API is called. The notebook
markdown names real products (RateGain, Oracle Opera, Cloudbeds, PredictHQ, OAG, Cirium,
Zendesk, ServiceNow) as *candidate* integrations, and the goals section mentions MCP servers.
None of that is implemented.

Say so plainly and early on every page. The mocking is a legitimate design choice, it makes the
demo deterministic and nearly free to run, and swapping a fixture for a real call is a
one-function change. But a reader must never be left thinking those integrations exist. The
same overclaim was caught and fixed on an earlier project's social card; do not reintroduce it.

Similarly: this is an **exploration of a pattern**, not a product and not a research finding.
No claim about business outcomes ("increases RevPAR by X") is supported by anything here.
