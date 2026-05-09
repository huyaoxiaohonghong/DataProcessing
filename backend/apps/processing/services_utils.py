"""
Shared utilities for the processing service.

This module hosts small, dependency-light helpers that are reused by the
multi-sheet execution pipeline (Data_Processing_Service) and its callers.

Currently exposed helpers:

* :func:`append_task_error` — append a diagnostic line to
  ``ProcessingTask.error_message`` while keeping existing content intact.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from apps.processing.models import ProcessingTask


def append_task_error(task: "ProcessingTask", text: str) -> None:
    """Append ``text`` to ``task.error_message`` using newline separation.

    Rules (see Requirements 5.2 and 8.5):

    * Existing content is preserved; the new ``text`` is joined with ``\\n``.
    * ``None`` and empty ``error_message`` are tolerated — after joining the
      result is ``lstrip()``-ed so no leading whitespace/newline sneaks in.
    * The write is persisted via ``save(update_fields=['error_message'])`` so
      unrelated fields on the task remain untouched (safe to call from inside
      long-running execution paths that maintain their own state).

    Parameters
    ----------
    task:
        The :class:`ProcessingTask` instance whose ``error_message`` should be
        updated. The instance is mutated in place and saved.
    text:
        The diagnostic message to append. Empty strings and ``None`` are
        treated as no-ops to avoid writing blank lines.
    """
    if not text:
        # Nothing to append: skip DB round-trip. Keeps call sites terse
        # (they can pass conditional strings without guarding themselves).
        return

    existing = task.error_message or ""
    combined = f"{existing}\n{text}".lstrip()
    task.error_message = combined
    task.save(update_fields=["error_message"])
