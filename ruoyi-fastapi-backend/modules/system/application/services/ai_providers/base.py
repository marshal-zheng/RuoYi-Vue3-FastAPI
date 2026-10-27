"""Small protocol boundary for the configured provider adapter."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderChunk:
    text: str = ''
    finish: str | None = None


class TextFieldProvider(Protocol):
    def stream(self, messages: list[dict]) -> AsyncIterator[ProviderChunk]: ...
