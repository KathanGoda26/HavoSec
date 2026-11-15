"""Small provider abstraction; provider-specific transport stays outside the agent."""
from abc import ABC, abstractmethod
from typing import Any
import httpx


class ProviderUnavailable(RuntimeError):
    pass


class AnalysisProvider(ABC):
    @abstractmethod
    async def structured_analysis(self, system: str, payload: str, schema: dict) -> tuple[dict, dict]:
        """Return decoded structured content and non-sensitive usage metadata."""


class OpenAIAnalysisProvider(AnalysisProvider):
    endpoint = 'https://api.openai.com/v1/chat/completions'
    max_response_bytes = 65_536

    def __init__(self, api_key: str, model: str, timeout: int, client_factory=httpx.AsyncClient):
        self.api_key, self.model, self.timeout = api_key, model, timeout
        self.client_factory = client_factory

    async def structured_analysis(self, system, payload, schema):
        request = {
            'model': self.model,
            'temperature': 0,
            'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': payload}],
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'finding_analysis', 'strict': True, 'schema': schema}},
        }
        try:
            async with self.client_factory(timeout=self.timeout, follow_redirects=False) as client:
                async with client.stream('POST', self.endpoint, json=request,
                        headers={'Authorization': f'Bearer {self.api_key}',
                                 'Content-Type': 'application/json'}) as response:
                    response.raise_for_status()
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > self.max_response_bytes:
                            raise ProviderUnavailable('Analysis provider response exceeded its limit')
                        chunks.append(chunk)
                import json
                body = json.loads(b''.join(chunks))
                content = body['choices'][0]['message']['content']
                decoded = json.loads(content)
                usage = body.get('usage') or {}
                safe_usage = {key: int(usage[key]) for key in
                              ('prompt_tokens', 'completion_tokens', 'total_tokens')
                              if isinstance(usage.get(key), int) and usage[key] >= 0}
                return decoded, safe_usage
        except ProviderUnavailable:
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ProviderUnavailable('Analysis provider request failed') from exc
