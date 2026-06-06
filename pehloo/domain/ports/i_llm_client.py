from abc import ABC, abstractmethod
from typing import Any


class ILLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str: ...

    @abstractmethod
    async def complete_json(self, system: str, user: str) -> dict[str, Any]: ...
