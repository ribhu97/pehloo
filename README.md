```
▶ SUITE / TOOL_01     ▶ STATUS: IN_DEVELOPMENT     ▶ ETA: Q4 2026
```

```
░░░░░░   ░░░░░░░  ░░   ░░  ░░        ░░░░░░    ░░░░░░
▒▒   ▒▒  ▒▒       ▒▒   ▒▒  ▒▒       ▒▒    ▒▒  ▒▒    ▒▒
▓▓▓▓▓▓   ▓▓▓▓▓▓   ▓▓▓▓▓▓▓  ▓▓       ▓▓    ▓▓  ▓▓    ▓▓
██       ██       ██   ██  ██       ██    ██  ██    ██
██       ███████  ██   ██  ███████   ██████    ██████
```

> A toolkit for automated multi-persona UX testing.
> Point it at a web app, give it personas and user journeys, and it walks
> each persona through the flow using a browser agent — then compiles a
> structured report of every point of friction and delight.

```
▶ KIND      : CLI / PYTHON_TOOLKIT
▶ RUNTIME   : PYTHON_3.11+
▶ ARCH      : HEXAGONAL / PORTS_AND_ADAPTERS
▶ LICENSE   : TBD
```

---

## ▸ WHAT_IT_DOES

Pehloo runs your product through the eyes of multiple users, in parallel,
without you watching them flail.

For each persona, it:

```
1. spawns a fresh browser agent
2. injects the persona's character, goals, and patience into the system prompt
3. walks the agent through a defined user journey, step by step
4. captures narration, friction, delight, and screenshots at every step
5. synthesises cross-persona findings into a single HTML report
```

Useful when you want to know *what your product feels like* to people
who are not you — before you ship.

---

## ▸ INSTALL

```bash
# clone
git clone https://github.com/ribhu97/pehloo.git
cd pehloo

# install (uv recommended)
uv sync

# or with pip
pip install -e .
```

Set up your environment:

```bash
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY
```

```
▶ REQUIRED   : OPENROUTER_API_KEY
▶ OPTIONAL   : PEHLOO_DEFAULT_MODEL, PEHLOO_MAX_STEPS_PER_TASK,
               PEHLOO_OUTPUT_DIR, PEHLOO_HEADLESS
```

---

## ▸ QUICKSTART

```bash
pehloo run \
  --url https://app.example.com \
  --personas ./personas.json \
  --journeys ./journeys.yaml
```

That's it. Pehloo will:

```
▸ load personas + journeys
▸ run each persona through each journey sequentially
▸ stream live step status to your terminal
▸ drop an HTML report into ./reports/<timestamp>.html
▸ print a Rich-formatted summary
```

Validate your journeys file before a full run:

```bash
pehloo validate --journeys ./journeys.yaml
```

---

## ▸ INPUTS

### PERSONAS_(.json)

```json
[
  {
    "id": "priya_01",
    "name": "Priya",
    "description": "Solo founder, ships fast, low patience for friction.",
    "goals": ["set up the product in under 5 minutes"],
    "pain_points": ["dense onboarding flows", "modal stacks"],
    "tech_literacy": "high",
    "patience_level": "low"
  }
]
```

### JOURNEYS_(.yaml)

```yaml
journeys:
  - id: onboarding_flow
    name: Onboarding Flow
    description: A new user discovers the product and sets up their first project.
    steps:
      - instruction: Navigate to the homepage and understand what the product does
        success: Can summarise the core value prop in one sentence

      - instruction: Sign up and complete the registration form
        success: Reaches the post-signup welcome screen

      - instruction: Create their first project
        success: Project appears in the dashboard
```

```
▶ RULES
  ▸ every step requires `instruction` AND `success`
  ▸ journey `id` must be unique
  ▸ `description` is optional but recommended (injected into agent prompt)
```

---

## ▸ OUTPUT

Each run produces:

```
▸ ./reports/<timestamp>.html   — per-persona tables + cross-persona summary
▸ terminal summary             — top frictions, critical issues, verdict
▸ exit code 0 on success       — non-zero on failure (CI-friendly)
```

The report includes, per persona:

```
✓ step status         (completed / stuck / failed / skipped)
✓ first-person narration
✓ friction score      (1–5)
✓ delight score       (1–5)
✓ URL captured at each step
✓ screenshots         (when enabled)
```

And across personas:

```
✓ LLM-synthesised summary of cross-persona friction patterns
✓ critical issues encountered by 2+ personas
✓ per-persona narrative findings
```

---

## ▸ CLI_REFERENCE

```
pehloo run
  --url TEXT           target web app URL                    [required]
  --personas PATH      path to personas JSON                  [required]
  --journeys PATH      path to journeys YAML                  [required]
  --output PATH        report output dir         [default: ./reports/]
  --max-personas INT   cap personas per run                 [default: 2]
  --verbose            stream agent narration live

pehloo validate
  --journeys PATH      validate a journeys YAML and exit
```

---

## ▸ ARCHITECTURE

Pehloo is built on a strict hexagonal architecture. Dependencies point
inward only.

```
ENTRYPOINTS  ─▶  USE_CASES  ─▶  DOMAIN_CORE
ADAPTERS     ─▶  PORTS      ─▶  DOMAIN_CORE
```

```
pehloo/
  domain/          ▸ pure dataclasses + abstract ports — no framework imports
  use_cases/       ▸ application logic — depends only on domain
  adapters/        ▸ browser-use, OpenRouter, parsers, renderers
  entrypoints/     ▸ Typer CLI — wiring only
  infrastructure/  ▸ config, logging
```

```
▶ WHY
  ▸ swap the browser driver (Figma, mobile sim) without touching domain
  ▸ swap the LLM provider without rewriting use cases
  ▸ in-memory adapters make every use case unit-testable
```

---

## ▸ ROADMAP

```
[ ] v1   ▸ CLI + browser-use + HTML report                  ◀  CURRENT
[ ] v2   ▸ scout agent (auto-discover journeys)
[ ] v2   ▸ Figma prototype driver
[ ] v2   ▸ MCP server entrypoint
[ ] v2   ▸ PDF/DOCX persona ingest
[ ] v3   ▸ Neuronpedia steering vectors per persona
```

---

## ▸ DEVELOPMENT

```bash
uv sync --extra dev

# tests
pytest

# lint + types
ruff check .
mypy pehloo
```

See [`CLAUDE.md`](./CLAUDE.md) for architectural rules, layering
constraints, and contribution conventions.

---

```
▶ STATUS    : IN_DEVELOPMENT
▶ FEEDBACK  : github.com/ribhu97/pehloo/issues
▶ SUITE     : TOOL_01
```
