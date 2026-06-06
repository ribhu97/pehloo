import asyncio
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from pehloo.infrastructure.config import settings
from pehloo.infrastructure.logging import setup_logging
from pehloo.adapters.parsers.json_persona_parser import JSONPersonaParser
from pehloo.adapters.parsers.yaml_journey_parser import YAMLJourneyParser, dump_journeys
from pehloo.adapters.browser.browser_use_agent import BrowserUseAgent
from pehloo.adapters.llm.openrouter_client import OpenRouterClient
from pehloo.adapters.llm.llm_journey_generator import LLMJourneyGenerator
from pehloo.adapters.renderers.html_report_renderer import HTMLReportRenderer
from pehloo.use_cases.parse_inputs import ParseInputs
from pehloo.use_cases.execute_persona_run import ExecutePersonaRun
from pehloo.use_cases.compile_report import CompileReport
from pehloo.use_cases.generate_journeys import GenerateJourneys
from pehloo.domain.entities.journey import Journey
from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.report import Report
from pehloo.domain.entities.test_run import TestRun

app = typer.Typer(help="Pehloo — automated multi-persona UX testing")
console = Console()


@app.command()
def run(
    url: str = typer.Option(..., help="Target web app URL"),
    personas: Path = typer.Option(..., help="Path to personas JSON file"),
    journeys: Path = typer.Option(..., help="Path to journeys YAML file"),
    output: Path = typer.Option(Path(settings.pehloo_output_dir), help="Output directory for HTML report"),
    max_personas: int = typer.Option(2, help="Personas to preselect / take in non-interactive mode"),
    max_journeys: int = typer.Option(1, help="Journeys to preselect / take in non-interactive mode"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive prompts; use --max-* defaults"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Stream agent narration live"),
) -> None:
    setup_logging(verbose)
    asyncio.run(
        _run(
            url, str(personas), str(journeys), str(output),
            max_personas, max_journeys, yes, verbose,
        )
    )


async def _run(
    url: str,
    personas_path: str,
    journeys_path: str,
    output_dir: str,
    max_personas: int,
    max_journeys: int,
    yes: bool,
    verbose: bool,
) -> None:
    console.rule("[bold blue]Pehloo UX Test")

    parse_use_case = ParseInputs(
        persona_parser=JSONPersonaParser(),
        journey_parser=YAMLJourneyParser(),
    )
    all_personas, all_journeys = parse_use_case.execute(personas_path, journeys_path)

    interactive = not yes and sys.stdin.isatty()
    selected_personas = _select_items(
        all_personas, max_personas, interactive,
        label="persona",
        formatter=lambda p: f"{p.name}  —  {p.description[:60]}",
    )
    selected_journeys = _select_items(
        all_journeys, max_journeys, interactive,
        label="journey",
        formatter=lambda j: f"{j.name}  ({len(j.steps)} steps)",
    )

    console.print(f"[green]Personas:[/green] {', '.join(p.name for p in selected_personas)}")
    console.print(
        f"[green]Journeys:[/green] "
        + ", ".join(f"{j.name} ({len(j.steps)} steps)" for j in selected_journeys)
    )
    console.print(
        f"[green]Target:[/green] {url}  "
        f"[dim]({len(selected_personas)} × {len(selected_journeys)} = "
        f"{len(selected_personas) * len(selected_journeys)} test run(s))[/dim]\n"
    )

    browser_agent = BrowserUseAgent(
        api_key=settings.openrouter_api_key,
        model=settings.pehloo_default_model,
        max_steps=settings.pehloo_max_steps_per_task,
        headless=settings.pehloo_headless,
        login_email=settings.pehloo_login_email,
        login_password=settings.pehloo_login_password,
    )
    execute_use_case = ExecutePersonaRun(browser_agent=browser_agent)

    all_test_runs: list[TestRun] = []
    all_observations = []

    for persona in selected_personas:
        for journey in selected_journeys:
            test_run = TestRun(
                id=str(uuid.uuid4()),
                persona=persona,
                journey=journey,
                target_url=url,
                started_at=datetime.utcnow(),
            )
            console.print(f"\n[bold]{persona.name}[/bold] → [italic]{journey.name}[/italic]")

            observations = await execute_use_case.execute(test_run)
            for obs in observations:
                obs.test_run_id = test_run.id
                status_color = "green" if obs.status == "completed" else "red"
                console.print(
                    f"  [{status_color}]✓ Step {obs.step_index + 1}[/{status_color}] — "
                    f"{persona.name}: {obs.status} "
                    f"(friction: {obs.friction_score}, delight: {obs.delight_score})"
                )
                if verbose:
                    console.print(f"    [dim]{obs.narration}[/dim]")

            test_run.completed_at = datetime.utcnow()
            all_test_runs.append(test_run)
            all_observations.extend(observations)

            # Fresh browser session for the next test run.
            await browser_agent.close()

    await _compile_and_print_report(all_test_runs, all_observations, output_dir)


def _select_items(items: list, max_count: int, interactive: bool, label: str, formatter) -> list:
    if not items:
        console.print(f"[red]No {label}s available to run.[/red]")
        raise typer.Exit(code=1)

    if not interactive:
        return items[:max_count]

    preselected_ids = {item.id for item in items[:max_count]}
    choices = [
        questionary.Choice(title=formatter(item), value=item, checked=item.id in preselected_ids)
        for item in items
    ]
    selected = questionary.checkbox(
        f"Select {label}s (↑↓ move · space toggle · enter confirm):",
        choices=choices,
    ).ask()

    if selected is None:  # Ctrl-C
        raise typer.Exit(code=130)
    if not selected:
        console.print(f"[red]No {label}s selected.[/red]")
        raise typer.Exit(code=1)
    return selected


async def _compile_and_print_report(
    test_runs: list[TestRun], observations: list, output_dir: str
) -> Report:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"report_{timestamp}.html")

    compile_use_case = CompileReport(
        llm_client=OpenRouterClient(
            api_key=settings.openrouter_api_key, model=settings.pehloo_default_model
        ),
        renderer=HTMLReportRenderer(),
    )
    report = await compile_use_case.execute(test_runs, observations, report_path)

    console.rule("[bold green]Report Complete")
    console.print(f"[green]Report saved:[/green] {report_path}")

    table = Table(title="Summary")
    table.add_column("Persona")
    table.add_column("Findings")
    for run in report.test_runs:
        table.add_row(run.persona.name, report.per_persona_findings.get(run.persona.id, "—"))
    console.print(table)

    if report.prioritized_issues:
        console.print("\n[red bold]Fix This First:[/red bold]")
        for issue in report.prioritized_issues:
            console.print(f"  • [bold]{issue.title}[/bold] (severity {issue.severity})")
            if issue.suggested_fix:
                console.print(f"    [green]→[/green] {issue.suggested_fix}")
    return report


@app.command("plan")
def plan_cmd(
    url: str = typer.Option(..., help="Target web app URL"),
    personas: Path = typer.Option(..., help="Path to personas JSON file"),
    output: Path = typer.Option(Path(settings.pehloo_output_dir), help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Stream agent narration live"),
) -> None:
    """Interactive flow: pick a persona, generate + refine 3 journeys, run one, report out."""
    setup_logging(verbose)
    asyncio.run(_plan(url, str(personas), str(output), verbose))


async def _plan(url: str, personas_path: str, output_dir: str, verbose: bool) -> None:
    console.rule("[bold blue]Pehloo — Plan & Test")

    # 1) Personas in.
    all_personas = JSONPersonaParser().parse(personas_path)
    if not all_personas:
        console.print("[red]No personas found in file.[/red]")
        raise typer.Exit(code=1)
    persona = _pick_persona(all_personas)
    console.print(f"\n[green]Selected:[/green] {persona.name} — {persona.description}\n")

    # 2) Generate 3 journeys, allow one round of refinement.
    llm = OpenRouterClient(
        api_key=settings.openrouter_api_key, model=settings.pehloo_default_model
    )
    generate_use_case = GenerateJourneys(generator=LLMJourneyGenerator(llm_client=llm))

    console.print("[dim]Generating 3 candidate journeys…[/dim]")
    journeys = await generate_use_case.execute(persona, url, count=3)
    _print_journeys(journeys)

    feedback = Prompt.ask(
        "\n[bold]Feedback to revise[/bold] (press Enter to accept as-is)", default=""
    ).strip()
    if feedback:
        console.print("[dim]Revising journeys based on your feedback…[/dim]")
        journeys = await generate_use_case.execute(
            persona, url, count=3, previous=journeys, feedback=feedback
        )
        _print_journeys(journeys)

    # 3) Persist to YAML — also proves we can round-trip into `pehloo run`.
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    yaml_path = os.path.join(output_dir, f"journeys_{timestamp}.yaml")
    dump_journeys(journeys, yaml_path)
    console.print(f"\n[green]Journeys saved:[/green] {yaml_path}")

    # 4) Pick one to execute.
    chosen = _pick_journey(journeys)
    console.print(f"\n[green]Running:[/green] {chosen.name} ({len(chosen.steps)} steps)\n")

    # 5) Browser-agent run — mirrors the loop inside `_run`.
    browser_agent = BrowserUseAgent(
        api_key=settings.openrouter_api_key,
        model=settings.pehloo_default_model,
        max_steps=settings.pehloo_max_steps_per_task,
        headless=settings.pehloo_headless,
        login_email=settings.pehloo_login_email,
        login_password=settings.pehloo_login_password,
    )
    execute_use_case = ExecutePersonaRun(browser_agent=browser_agent)

    test_run = TestRun(
        id=str(uuid.uuid4()),
        persona=persona,
        journey=chosen,
        target_url=url,
        started_at=datetime.utcnow(),
    )
    observations = await execute_use_case.execute(test_run)
    for obs in observations:
        obs.test_run_id = test_run.id
        status_color = "green" if obs.status == "completed" else "red"
        console.print(
            f"  [{status_color}]✓ Step {obs.step_index + 1}[/{status_color}] — "
            f"{persona.name}: {obs.status} "
            f"(friction: {obs.friction_score}, delight: {obs.delight_score})"
        )
        if verbose:
            console.print(f"    [dim]{obs.narration}[/dim]")
    test_run.completed_at = datetime.utcnow()

    # 6) Report.
    await _compile_and_print_report([test_run], observations, output_dir)


def _pick_persona(personas: list[Persona]) -> Persona:
    table = Table(title="Personas")
    table.add_column("#", style="bold")
    table.add_column("Name")
    table.add_column("Description")
    for i, p in enumerate(personas, start=1):
        table.add_row(str(i), p.name, p.description)
    console.print(table)

    choices = [str(i) for i in range(1, len(personas) + 1)]
    idx = IntPrompt.ask("Pick a persona", choices=choices, default=1)
    return personas[idx - 1]


def _pick_journey(journeys: list[Journey]) -> Journey:
    choices = [str(i) for i in range(1, len(journeys) + 1)]
    idx = IntPrompt.ask("\nPick a journey to execute", choices=choices, default=1)
    return journeys[idx - 1]


def _print_journeys(journeys: list[Journey]) -> None:
    for i, j in enumerate(journeys, start=1):
        body_lines = [
            f"  {k}. {s.instruction}\n     [dim]→ {s.success_criteria}[/dim]"
            for k, s in enumerate(j.steps, start=1)
        ]
        console.print(
            Panel("\n".join(body_lines), title=f"[bold]Journey {i}: {j.name}[/bold]")
        )
