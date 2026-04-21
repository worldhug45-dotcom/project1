"""Application-wide error classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorType(StrEnum):
    """Operational error categories used in logs and control flow."""

    RETRYABLE = "retryable"
    NON_FATAL = "non_fatal"
    FATAL = "fatal"
    CONFIGURATION = "configuration"


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """Serializable error information for log events."""

    error_type: ErrorType
    message: str
    source: str | None = None


class Project1Error(Exception):
    """Base exception carrying an operational error type."""

    error_type = ErrorType.FATAL

    def __init__(self, message: str, *, source: str | None = None) -> None:
        super().__init__(message)
        self.source = source

    def to_error_info(self) -> ErrorInfo:
        return ErrorInfo(
            error_type=self.error_type,
            message=str(self),
            source=self.source,
        )


class RetryableError(Project1Error):
    """Temporary error that may recover after retry."""

    error_type = ErrorType.RETRYABLE


class NonFatalError(Project1Error):
    """Error that does not necessarily fail the whole run."""

    error_type = ErrorType.NON_FATAL


class FatalError(Project1Error):
    """Error that fails the whole run."""

    error_type = ErrorType.FATAL


class StorageWriteError(FatalError):
    """Persistence failure that makes the current run unsafe to continue."""


class ConfigurationAppError(Project1Error):
    """Configuration validation error raised before work begins."""

    error_type = ErrorType.CONFIGURATION


def classify_exception(exc: BaseException) -> ErrorInfo:
    """Convert arbitrary exceptions into the common error structure."""

    if isinstance(exc, Project1Error):
        return exc.to_error_info()
    return ErrorInfo(error_type=ErrorType.FATAL, message=str(exc))
