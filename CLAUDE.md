# CLAUDE.md — Pehloo

> Automated multi-persona UX testing tool. Give it personas + user journeys + a URL, and it runs each persona through the journey using a browser agent, then compiles a structured report.

---

## Codebase Navigation — MANDATORY

You MUST use token-savior MCP tools FIRST.

- ALWAYS start with: find_symbol, get_function_source, get_class_source,
  search_codebase, get_dependencies, get_dependents, get_change_impact
- Only fall back to Read/Grep when token-savior tools genuinely don't cover it
- If you catch yourself reaching for grep to find code, STOP

---

## What You Are Building

**Pehloo** is a Python CLI tool. The user runs:

```bash
pehloo run \
  --url https://app.example.com \
  --personas ./personas.json \
  --journeys ./journeys.yaml
```

The tool:
1. Parses the personas and journeys into domain entities
2. For each persona (sequentially), runs a `browser-use` agent through the journey steps
3. Each agent is injected with the persona's character via system prompt — it navigates, narrates, and records friction/delight
4. Once all persona runs are complete, a report compiler agent synthesises cross-persona findings
5. Output: an HTML report file + a terminal summary

**MVP scope:** 2 personas, sequential execution, Case 1 only (user provides journeys), CLI entrypoint only.

---

## Architecture Pattern

**Hexagonal architecture (Ports and Adapters).**

The strict rule: **dependencies point inward only.**

```
Entrypoints → Use Cases → Domain Core
Adapters    → Ports     → Domain Core
```

- `domain/` — pure Python dataclasses, no framework imports, ever
- `use_cases/` — imports only from `domain/`; calls ports via injected interfaces
- `ports/` — abstract base classes; no implementations
- `adapters/` — concrete implementations of ports; framework imports live here only
- `entrypoints/` — CLI wiring; resolves DI, calls use cases, no business logic

If you find yourself importing from `adapters/` inside `use_cases/`, stop. That is a layering violation.

---

## Directory Structure

```
pehloo/
├── CLAUDE.md                        ← this file
├── README.md
├── pyproject.toml                   ← package config, deps, CLI entrypoint
├── experiments/                     ← this contains experimental files and sub-folders (should be gitignored) 
├── .env.example
│
├── pehloo/                          ← main package
│   │
│   ├── domain/                      ← Layer 0: pure business logic
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── persona.py           ← Persona dataclass
│   │   │   ├── journey.py           ← Journey + JourneyStep dataclasses
│   │   │   ├── test_run.py          ← TestRun dataclass (persona + journey + target)
│   │   │   ├── observation.py       ← Observation dataclass (core schema — see below)
│   │   │   └── report.py            ← Report dataclass (compiled findings)
│   │   └── ports/                   ← Abstract interfaces (no implementations)
│   │       ├── __init__.py
│   │       ├── i_browser_agent.py   ← IBrowserAgent
│   │       ├── i_persona_parser.py  ← IPersonaParser
│   │       ├── i_journey_parser.py  ← IJourneyParser
│   │       ├── i_report_renderer.py ← IReportRenderer
│   │       └── i_llm_client.py      ← ILLMClient
│   │
│   ├── use_cases/                   ← Layer 1: application logic
│   │   ├── __init__.py
│   │   ├── parse_inputs.py          ← ParseInputs use case
│   │   ├── execute_persona_run.py   ← ExecutePersonaRun use case
│   │   └── compile_report.py        ← CompileReport use case
│   │
│   ├── adapters/                    ← Layer 2: concrete implementations
│   │   ├── __init__.py
│   │   ├── browser/
│   │   │   ├── __init__.py
│   │   │   └── browser_use_agent.py ← BrowserUseAgent → IBrowserAgent
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── json_persona_parser.py   ← JSONPersonaParser → IPersonaParser
│   │   │   └── yaml_journey_parser.py   ← YAMLJourneyParser → IJourneyParser
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── openrouter_client.py ← OpenRouterClient → ILLMClient
│   │   └── renderers/
│   │       ├── __init__.py
│   │       └── html_report_renderer.py  ← HTMLReportRenderer → IReportRenderer
│   │
│   ├── entrypoints/                 ← Layer 3: wiring only
│   │   ├── __init__.py
│   │   └── cli.py                   ← Typer CLI; resolves DI, calls use cases
│   │
│   └── infrastructure/              ← Cross-cutting concerns
│       ├── __init__.py
│       ├── config.py                ← Env vars, settings (pydantic-settings)
│       └── logging.py               ← Structured logging setup
│
├── tests/
│   ├── unit/
│   │   ├── domain/                  ← Test entities and value logic
│   │   └── use_cases/               ← Test use cases with in-memory adapters
│   └── integration/
│       └── adapters/                ← Test real adapters (browser, LLM) separately
│
├── reports/                         ← Default output dir for generated HTML reports
│   └── .gitkeep
│
└── examples/
    ├── personas.json                ← Example PersonaForge export
    └── journeys.yaml                ← Example journey definition
```

---

## Domain Entities (implement these first)

### `Persona`
```python
@dataclass
class Persona:
    id: str
    name: str
    description: str           # freetext summary
    goals: list[str]           # what they want to accomplish
    pain_points: list[str]
    tech_literacy: str         # "low" | "medium" | "high"
    patience_level: str        # "low" | "medium" | "high"
    raw: dict                  # original source JSON (preserved for debugging)
```

### `JourneyStep`
```python
@dataclass
class JourneyStep:
    index: int
    instruction: str           # e.g. "Sign up for a free account"
    success_criteria: str      # e.g. "Reaches the dashboard"
```

### `Journey`
```python
@dataclass
class Journey:
    id: str
    name: str
    steps: list[JourneyStep]
```

### `TestRun`
```python
@dataclass
class TestRun:
    id: str
    persona: Persona
    journey: Journey
    target_url: str
    started_at: datetime
    completed_at: datetime | None = None
```

### `Observation`  ← the critical interface between ExecutePersonaRun and CompileReport
```python
@dataclass
class Observation:
    test_run_id: str
    step_index: int
    step_instruction: str
    status: str                # "completed" | "stuck" | "failed" | "skipped"
    narration: str             # agent's first-person narration as the persona
    friction_score: int        # 1–5 (1 = smooth, 5 = severely blocked)
    delight_score: int         # 1–5 (1 = neutral, 5 = genuinely delighted)
    url_at_step: str
    screenshot_path: str | None
    raw_agent_output: str      # full agent trace for debugging
    timestamp: datetime
```

### `Report`
```python
@dataclass
class Report:
    id: str
    test_runs: list[TestRun]
    observations: list[Observation]
    summary: str               # LLM-synthesised cross-persona summary
    critical_issues: list[str] # issues found by 2+ personas
    per_persona_findings: dict[str, str]  # persona_id → narrative findings
    generated_at: datetime
```

---

## Ports (define these second, as ABCs)

```python
# i_browser_agent.py
class IBrowserAgent(ABC):
    @abstractmethod
    async def run_step(
        self, persona: Persona, step: JourneyStep, url: str
    ) -> Observation: ...

# i_journey_parser.py
class IJourneyParser(ABC):
    @abstractmethod
    def parse(self, source: str) -> list[Journey]: ...
    # source = file path; raises ValueError with clear message if schema invalid

# i_persona_parser.py
class IPersonaParser(ABC):
    @abstractmethod
    def parse(self, source: str) -> list[Persona]: ...
    # source = file path

# i_report_renderer.py
class IReportRenderer(ABC):
    @abstractmethod
    def render(self, report: Report, output_path: str) -> None: ...

# i_llm_client.py
class ILLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str: ...
```

---

## Use Cases

### `ParseInputs`
- Accepts: `personas_path: str`, `journeys_path: str`
- Uses: `IPersonaParser`
- Returns: `(list[Persona], list[Journey])`
- Note: detects file type (`.json` → `JSONPersonaParser`, `.yaml` → `YAMLJourneyParser`); raises a parse error with a helpful message if a journey step is missing `success`

### `ExecutePersonaRun`
- Accepts: `TestRun`, `IBrowserAgent`
- Iterates through `journey.steps` sequentially
- Calls `browser_agent.run_step(persona, step, url)` for each step
- Streams step status to terminal as it goes
- Returns: `list[Observation]`

### `CompileReport`
- Accepts: `list[TestRun]`, `list[Observation]`, `ILLMClient`, `IReportRenderer`
- Calls LLM to synthesise cross-persona findings into `Report.summary` and `critical_issues`
- Calls renderer to write HTML file
- Returns: `Report`

---

## Key Adapter: BrowserUseAgent

This is the most complex adapter. Key implementation notes:

- Each call to `run_step` creates a fresh `browser-use` `Agent` instance
- The persona character is injected in the **system prompt** like:
  ```
  You are {persona.name}. {persona.description}
  Your goals: {persona.goals}
  Your tech literacy is {persona.tech_literacy} and patience is {persona.patience_level}.
  
  Complete this task: {step.instruction}
  Success looks like: {step.success_criteria}
  
  As you navigate, narrate your experience in first person. Note any confusion,
  friction, or delight. When done, return a structured JSON observation.
  ```
- The agent must return a structured JSON matching the `Observation` schema
- Use `browser-use`'s `output_model` / structured output feature to enforce this
- Cap steps per task to avoid runaway agents (default: 15 actions per step)

---

## CLI Interface (`entrypoints/cli.py`)

Built with **Typer**. Main command:

```bash
pehloo run \
  --url TEXT           # required: target web app URL
  --personas PATH      # required: path to personas JSON file
  --journeys PATH      # required: path to journeys YAML file
  --output PATH        # optional: output dir for HTML report (default: ./reports/)
  --max-personas INT   # optional: limit number of personas to run (default: 2)
  --verbose            # optional: stream agent narration to terminal live

pehloo validate \
  --journeys PATH      # validates journeys.yaml and prints any schema errors; exits 0 if valid
```

The CLI's only job: resolve dependencies, instantiate adapters, call use cases in order, print terminal summary.

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "pehloo"
version = "0.1.0"
requires-python = ">=3.11"

[project.scripts]
pehloo = "pehloo.entrypoints.cli:app"

[project.dependencies]
typer = ">=0.12"
browser-use = ">=0.1"          # browser automation
openai = ">=1.0"               # OpenRouter-compatible client (Chat Completions API)
langchain-openai = ">=0.1"     # ChatOpenAI for browser-use, pointed at OpenRouter
pydantic = ">=2.0"             # data validation
pydantic-settings = ">=2.0"    # env config
pyyaml = ">=6.0"               # journey YAML parsing
jinja2 = ">=3.1"               # HTML report templating
rich = ">=13.0"                # terminal output formatting
python-dotenv = ">=1.0"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "ruff", "mypy"]
```

---

## Environment Variables (`.env`)

```
OPENROUTER_API_KEY=sk-or-...
PEHLOO_DEFAULT_MODEL=anthropic/claude-sonnet-4-5   # OpenRouter model slug: <provider>/<model>
PEHLOO_MAX_STEPS_PER_TASK=15
PEHLOO_OUTPUT_DIR=./reports
PEHLOO_HEADLESS=true            # set false to watch the browser during dev
```

---

## Journey File Format (`journeys.yaml`)

Journeys are defined in YAML. The `YAMLJourneyParser` validates this against a Pydantic schema on load — missing fields produce a clear error before any browser is launched.

```yaml
journeys:
  - id: onboarding_flow
    name: Onboarding Flow
    description: >
      A new user discovers the product and sets up their first project
      for the first time.
    steps:
      - instruction: Navigate to the homepage and understand what the product does
        success: Can summarise the core value prop in one sentence

      - instruction: Click sign up and complete the registration form
        success: Reaches the post-signup welcome screen

      - instruction: Complete the onboarding checklist
        success: At least 3 checklist items marked done

      - instruction: Create their first project
        success: Project appears in the dashboard

  - id: upgrade_to_pro
    name: Upgrade to Pro
    description: >
      An existing free user hits their persona limit and decides
      to explore upgrading.
    steps:
      - instruction: Attempt to create a second persona set
        success: Sees the upgrade prompt

      - instruction: Navigate to the pricing page and compare plans
        success: Can identify what Pro offers over Free

      - instruction: Click upgrade and complete the payment flow
        success: Account shows Pro status
```

Rules enforced by the parser:
- `id` must be unique across journeys
- Every step must have both `instruction` and `success` — missing either raises `ValueError`
- `description` is optional but recommended; injected into the agent's system prompt as context
- Run `pehloo validate --journeys journeys.yaml` to check a file before a full run

---

## Build Order

Work in this order — each step produces something the next depends on:

1. **Domain entities** — `persona.py`, `journey.py`, `test_run.py`, `observation.py`, `report.py`
2. **Ports** — all four abstract interfaces
3. **Use case skeletons** — stubbed out, typed, no implementations yet
4. **`JSONPersonaParser`** — parse a PersonaForge export into `Persona` entities; write unit tests
5. **`YAMLJourneyParser`** — parse a `journeys.yaml` file into `Journey` entities via Pydantic validation; write unit tests; raise clear errors for missing `success` fields
6. **`OpenRouterClient`** — thin wrapper around the `openai` async SDK pointed at `https://openrouter.ai/api/v1`; test with a simple completion
7. **`BrowserUseAgent`** — the core adapter; start with a single step, get structured output working
8. **`ExecutePersonaRun`** use case — wire browser agent; test with one persona, one step
9. **`CompileReport`** use case — wire LLM client + renderer
10. **`HTMLReportRenderer`** — Jinja2 template; HTML with tables and per-persona sections
11. **CLI entrypoint** — wire everything together with Typer; test end-to-end
12. **Terminal summary** — Rich-formatted summary printed after report generation

---

## Roadmap Hooks (do not build, just don't make them impossible)

| Feature | What to add when the time comes |
|---|---|
| Scout agent (v2) | New port `IAppExplorer`, new use case `DiscoverJourneys`, new adapter `ScoutAgent`. Output is `list[Journey]` — same type `ExecutePersonaRun` already consumes. |
| Figma prototype driver (v2) | Rename/generalise `IBrowserAgent` → `IPrototypeDriver`. Add `FigmaDriver` adapter. Widen `TestRun.target_url` to a `Target` union type (`URLTarget \| FigmaTarget`). |
| Neuronpedia steering vectors (v3) | New port `ISteeringProvider`, new use case `BuildSteeringProfile`, new entity `SteeringProfile`. Add optional `steering_profile` field to `Persona`. `BrowserUseAgent` injects vectors into system prompt if present; falls back to text description if not. |
| MCP server (v2) | New entrypoint in `entrypoints/mcp_server.py`. Exposes `run_persona_test` and `get_report` as MCP tools. Same adapters, same use cases — different entrypoint only. |
| PDF/DOCX persona input (v2) | New adapter `PDFPersonaParser` implementing `IPersonaParser`. `ParseInputs` use case detects `.pdf` extension and routes to it. Zero other changes. |

---

## Testing Philosophy

Every use case must be testable with **in-memory adapters** — no browser, no LLM, no network.

```python
# Example: test ExecutePersonaRun without a real browser
class MockBrowserAgent(IBrowserAgent):
    async def run_step(self, persona, step, url) -> Observation:
        return Observation(status="completed", friction_score=1, ...)

async def test_execute_persona_run_collects_observations():
    use_case = ExecutePersonaRun(browser_agent=MockBrowserAgent())
    observations = await use_case.execute(test_run)
    assert len(observations) == len(test_run.journey.steps)
```

Integration tests (real browser, real LLM) live in `tests/integration/` and are opt-in.

---

## What "Done" Looks Like for MVP

Running `pehloo run --url https://someapp.com --personas examples/personas.json --journeys examples/journeys.yaml` should:

1. Print persona names and journey steps to terminal on start
2. Stream each step's status as agents run (`✓ Step 1 — Priya: completed (friction: 2)`)
3. Save an HTML report to `./reports/<timestamp>.html` with per-persona tables and a cross-persona summary section
4. Print a Rich-formatted terminal summary (top frictions, critical issues, per-persona verdict)
5. Exit cleanly with code 0 on success, non-zero on failure

<!-- dgc-policy-v11 -->
# Dual-Graph Context Policy

This project uses a local dual-graph MCP server for efficient context retrieval.

## MANDATORY: Always follow this order

1. **Call `graph_continue` first** — before any file exploration, grep, or code reading.

2. **If `graph_continue` returns `needs_project=true`**: call `graph_scan` with the
   current project directory (`pwd`). Do NOT ask the user.

3. **If `graph_continue` returns `skip=true`**: project has fewer than 5 files.
   Do NOT do broad or recursive exploration. Read only specific files if their names
   are mentioned, or ask the user what to work on.

4. **Read `recommended_files`** using `graph_read` — **one call per file**.
   - `graph_read` accepts a single `file` parameter (string). Call it separately for each
     recommended file. Do NOT pass an array or batch multiple files into one call.
   - `recommended_files` may contain `file::symbol` entries (e.g. `src/auth.ts::handleLogin`).
     Pass them verbatim to `graph_read(file: "src/auth.ts::handleLogin")` — it reads only
     that symbol's lines, not the full file.
   - Example: if `recommended_files` is `["src/auth.ts::handleLogin", "src/db.ts"]`,
     call `graph_read(file: "src/auth.ts::handleLogin")` and `graph_read(file: "src/db.ts")`
     as two separate calls (they can be parallel).

5. **Check `confidence` and obey the caps strictly:**
   - `confidence=high` -> Stop. Do NOT grep or explore further.
   - `confidence=medium` -> If recommended files are insufficient, call `fallback_rg`
     at most `max_supplementary_greps` time(s) with specific terms, then `graph_read`
     at most `max_supplementary_files` additional file(s). Then stop.
   - `confidence=low` -> Call `fallback_rg` at most `max_supplementary_greps` time(s),
     then `graph_read` at most `max_supplementary_files` file(s). Then stop.

## Token Usage

A `token-counter` MCP is available for tracking live token usage.

- To check how many tokens a large file or text will cost **before** reading it:
  `count_tokens({text: "<content>"})`
- To log actual usage after a task completes (if the user asks):
  `log_usage({input_tokens: <est>, output_tokens: <est>, description: "<task>"})`
- To show the user their running session cost:
  `get_session_stats()`

Live dashboard URL is printed at startup next to "Token usage".

## Rules

- Do NOT use `rg`, `grep`, or bash file exploration before calling `graph_continue`.
- Do NOT do broad/recursive exploration at any confidence level.
- `max_supplementary_greps` and `max_supplementary_files` are hard caps - never exceed them.
- Do NOT dump full chat history.
- Do NOT call `graph_retrieve` more than once per turn.
- After edits, call `graph_register_edit` with the changed files. Use `file::symbol` notation (e.g. `src/auth.ts::handleLogin`) when the edit targets a specific function, class, or hook.

## Context Store

Whenever you make a decision, identify a task, note a next step, fact, or blocker during a conversation, call `graph_add_memory`.

**To add an entry:**
```
graph_add_memory(type="decision|task|next|fact|blocker", content="one sentence max 15 words", tags=["topic"], files=["relevant/file.ts"])
```

**Do NOT write context-store.json directly** — always use `graph_add_memory`. It applies pruning and keeps the store healthy.

**Rules:**
- Only log things worth remembering across sessions (not every minor detail)
- `content` must be under 15 words
- `files` lists the files this decision/task relates to (can be empty)
- Log immediately when the item arises — not at session end

## Session End

When the user signals they are done (e.g. "bye", "done", "wrap up", "end session"), proactively update `CONTEXT.md` in the project root with:
- **Current Task**: one sentence on what was being worked on
- **Key Decisions**: bullet list, max 3 items
- **Next Steps**: bullet list, max 3 items

Keep `CONTEXT.md` under 20 lines total. Do NOT summarize the full conversation — only what's needed to resume next session.
