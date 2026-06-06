import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pehloo.domain.entities.report import Report
from pehloo.domain.ports.i_report_renderer import IReportRenderer

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class HTMLReportRenderer(IReportRenderer):
    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, report: Report, output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        template = self._env.get_template("report.html.j2")
        persona_names = {run.persona.id: run.persona.name for run in report.test_runs}
        html = template.render(report=report, persona_names=persona_names)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
