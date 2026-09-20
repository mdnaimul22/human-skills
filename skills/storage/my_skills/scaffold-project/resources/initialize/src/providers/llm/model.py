import json
from collections.abc import Iterable
from typing import Optional
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from openai.types.chat import ChatCompletionMessageParam
from src.config import Settings, ClientConfig
from src.helpers.exceptions import ExternalServiceError
from .config import ClientRotator


def _create_async_client(config: ClientConfig) -> AsyncOpenAI:
    transport = DefaultAsyncHttpxClient(proxy=config.proxy, timeout=30.0) if config.proxy else None
    return AsyncOpenAI(base_url=config.base_url, api_key=config.api_key, http_client=transport, timeout=30.0)


class LLMProvider:
    def __init__(self):
        self.rotator = ClientRotator()

    async def process(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        model: Optional[str] = None,
    ) -> str:
        last_error = None
        attempts = max(1, min(Settings.LLM_RETRIES, len(self.rotator.client_configs)))

        for _ in range(attempts):
            config = self.rotator.get_next_client_config(model=model)
            client = _create_async_client(config)
            try:
                response = await client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    temperature=Settings.LLM_TEMPERATURE,
                    max_tokens=Settings.LLM_MAX_TOKENS,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
            finally:
                await client.close()

        raise ExternalServiceError("LLM", f"All retry attempts failed: {last_error}")

    async def generate_json(self, messages: Iterable[ChatCompletionMessageParam], model: Optional[str] = None) -> dict:
        raw = await self.process(messages=messages, model=model)
        return json.loads(raw)