import json
from collections.abc import Iterable
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from openai.types.chat import ChatCompletionMessageParam
from pydantic import JsonValue
from src.config import Settings, setup_logger
from src.helpers.exceptions import ExternalServiceError
from .config import ClientConfig, ClientRotator

logger = setup_logger(boss_name="providers.main.txt", his_name="providers.llm.txt")


def _clean_json_text(raw: str) -> str:
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return clean


class LLMProvider:
    def __init__(self, rotator: ClientRotator | None = None):
        self.rotator = rotator or ClientRotator()
        self._clients: dict[tuple[str, str, str | None], AsyncOpenAI] = {}

    def _get_client(self, config: ClientConfig) -> AsyncOpenAI:
        key = (config.base_url, config.api_key, config.proxy)
        client = self._clients.get(key)
        if client is None:
            transport = DefaultAsyncHttpxClient(proxy=config.proxy, timeout=30.0) if config.proxy else None
            client = AsyncOpenAI(base_url=config.base_url, api_key=config.api_key, http_client=transport, timeout=30.0)
            self._clients[key] = client
        return client

    async def process(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not self.rotator.client_configs:
            raise ExternalServiceError("LLM", "No client configurations available")

        last_error: Exception | None = None
        attempts = max(1, min(Settings.LLM_RETRIES, len(self.rotator.client_configs)))
        temp = temperature if temperature is not None else Settings.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else Settings.LLM_MAX_TOKENS

        for attempt in range(1, attempts + 1):
            config = self.rotator.get_next_client_config(model=model)
            client = self._get_client(config)
            try:
                response = await client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt}/{attempts} failed on model='{config.model}': {e}")

        raise ExternalServiceError("LLM", f"All retry attempts failed: {last_error}")

    async def generate_json(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        model: str | None = None,
    ) -> dict[str, JsonValue]:
        raw = await self.process(messages=messages, model=model)
        clean = _clean_json_text(raw)
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            raise ExternalServiceError("LLM", f"Failed to parse LLM response as JSON: {e}")

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
