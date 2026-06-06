import json
from typing import Any

from openai import AsyncOpenAI

from pehloo.domain.ports.i_llm_client import ILLMClient

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient(ILLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=_OPENROUTER_BASE_URL)
        self._model = model

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
