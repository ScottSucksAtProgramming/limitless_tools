"""Shared exception hierarchy for the Limitless Tools CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LimitlessError(Exception):
    """Base class for all domain-specific errors."""

    message: str
    cause: Exception | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cause is not None and not isinstance(self.cause, BaseException):
            raise TypeError("cause must be an exception instance")

    def __str__(self) -> str:  # pragma: no cover - trivial method
        return self.message


@dataclass(slots=True)
class ConfigurationError(LimitlessError):
    """Raised when configuration or environment setup is invalid."""


@dataclass(slots=True)
class ValidationError(LimitlessError):
    """Raised when user input fails validation (e.g., invalid CLI args)."""


@dataclass(slots=True)
class ApiError(LimitlessError):
    """Raised when the remote API responds with an error or network failure."""

    status_code: int | None = None


@dataclass(slots=True)
class StorageError(LimitlessError):
    """Raised when local storage operations fail."""


@dataclass(slots=True)
class StateError(LimitlessError):
    """Raised for sync state read/write issues."""


@dataclass(slots=True)
class OutputError(LimitlessError):
    """Raised when export/write targets cannot be written."""


@dataclass(slots=True)
class ServiceError(LimitlessError):
    """Raised by services when orchestration fails."""

