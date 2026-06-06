from abc import ABC, abstractmethod

from pehloo.domain.entities.report import Report


class IReportRenderer(ABC):
    @abstractmethod
    def render(self, report: Report, output_path: str) -> None: ...
