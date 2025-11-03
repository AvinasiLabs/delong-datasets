"""
Policy enforcement for data export.

Note: Backend controls data visibility via runtime_key cipher.
Client-side policy only enforces export limits.
"""
from typing import Optional

from . import config
from .errors import PolicyViolationError


def enforce_visibility_policy(*, is_full: bool) -> None:
    """
    DEPRECATED: Visibility is controlled by backend via runtime_key.

    This function is kept for backwards compatibility but does nothing.
    Backend automatically returns sample or real data based on cipher verification.

    Args:
        is_full: Whether requesting full dataset access (ignored)
    """
    pass  # Backend controls visibility


def enforce_export_policy(*, rows: Optional[int] = None) -> None:
    """
    Enforce data export policy.

    Checks row limits for export operations.

    Args:
        rows: Number of rows being exported (if known)

    Raises:
        PolicyViolationError: If export exceeds configured limits
    """
    # Check row limits
    if rows is not None and rows > config.MAX_LOCAL_EXPORT_ROWS:
        raise PolicyViolationError(
            f"Export exceeds limit: {rows} rows > {config.MAX_LOCAL_EXPORT_ROWS} allowed. "
            f"Set DS_MAX_LOCAL_EXPORT_ROWS environment variable to increase limit."
        )


__all__ = ["enforce_visibility_policy", "enforce_export_policy"]
