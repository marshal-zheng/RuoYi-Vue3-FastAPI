"""Deployment-owned OpenAI-compatible protocol. This module is imported only after admission."""

import logging
from collections.abc import AsyncIterator

import httpx2
from openai import APIError, APITimeoutError, AsyncOpenAI, DefaultAsyncHttpxClient, omit
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, suppress_instrumentation

from common.ai_context import AIError
from config.env import TextFieldAISettings
from modules.system.application.services.ai_providers.base import ProviderChunk


class _PrivateTransportLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return is_instrumentation_enabled()


_PRIVATE_LOG_FILTER = _PrivateTransportLogs()


def _protect_transport_logs():
    # Logger filters run before any handler (including application log bridges).
    # SDK/HTTP transports are already imported; suppression is context-local, so
    # concurrent ordinary HTTP requests keep their normal diagnostics.
    for name in tuple(logging.Logger.manager.loggerDict):
        if name.split('.')[0] in {'openai', 'httpx2', 'httpcore2'}:
            logging.getLogger(name).addFilter(_PRIVATE_LOG_FILTER)


class OpenAICompatibleProvider:
    def __init__(self, settings: TextFieldAISettings, *, client_factory=AsyncOpenAI, transport=None):
        self.settings = settings
        self.client_factory = client_factory
        self.transport = transport

    async def stream(self, messages: list[dict]) -> AsyncIterator[ProviderChunk]:
        settings = self.settings
        if not settings.is_configured:
            raise AIError('provider-unavailable')
        # Request-owned client: SDK stream, transport and pool all close in the same task.
        timeout = httpx2.Timeout(45, connect=10, write=10, pool=10)
        # Disable automatic model/HTTP content capture for this private payload.
        with suppress_instrumentation():
            async with DefaultAsyncHttpxClient(
                timeout=timeout, follow_redirects=False, trust_env=False, transport=self.transport
            ) as http:
                _protect_transport_logs()
                try:
                    async with self.client_factory(
                        api_key=settings.ai_api_key.get_secret_value()
                        if settings.ai_auth_mode == 'bearer'
                        else 'no-auth',
                        base_url=settings.ai_base_url.rstrip('/') + '/',
                        organization='',
                        project='',
                        admin_api_key='',
                        webhook_secret='',
                        max_retries=0,
                        timeout=timeout,
                        http_client=http,
                    ) as client:
                        stream = await client.chat.completions.create(
                            model=settings.ai_model,
                            messages=messages,
                            stream=True,
                            n=1,
                            response_format={'type': 'json_object'},
                            max_tokens=settings.ai_text_field_max_tokens,
                            # SDK auth omission is a per-request public option.
                            extra_headers={
                                **({'Authorization': omit} if settings.ai_auth_mode == 'none' else {}),
                                'OpenAI-Organization': omit,
                                'OpenAI-Project': omit,
                            },
                        )
                        async with stream:
                            async for chunk in stream:
                                if not chunk.choices:
                                    continue
                                if len(chunk.choices) != 1 or chunk.choices[0].index != 0:
                                    raise AIError('invalid-output')
                                choice = chunk.choices[0]
                                yield ProviderChunk(text=choice.delta.content or '', finish=choice.finish_reason)
                except (APITimeoutError, httpx2.TimeoutException):
                    raise AIError('timeout') from None
                except (APIError, httpx2.HTTPError):
                    raise AIError('provider-unavailable') from None
                except (ValueError, TypeError, AttributeError):
                    raise AIError('invalid-output') from None
