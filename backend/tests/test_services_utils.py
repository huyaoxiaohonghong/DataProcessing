"""
Unit tests for apps.processing.services_utils.

Validates:
- Requirement 5.2 (cycle-detection writes to task.error_message)
- Requirement 8.5 (per-sheet failure appends to task.error_message)
"""
import pytest

from apps.processing.models import ProcessingTask
from apps.processing.services_utils import append_task_error


def _reload(task: ProcessingTask) -> ProcessingTask:
    return ProcessingTask.objects.get(pk=task.pk)


def test_append_to_none_error_message_strips_leading_newline(test_task):
    """When error_message is None, the appended text should not be prefixed with \\n."""
    test_task.error_message = None
    test_task.save(update_fields=["error_message"])

    append_task_error(test_task, "first error")

    assert test_task.error_message == "first error"
    assert _reload(test_task).error_message == "first error"


def test_append_to_empty_string_error_message(test_task):
    """Empty string is treated the same as None: no leading newline."""
    test_task.error_message = ""
    test_task.save(update_fields=["error_message"])

    append_task_error(test_task, "boom")

    assert test_task.error_message == "boom"
    assert _reload(test_task).error_message == "boom"


def test_append_newline_separates_multiple_entries(test_task):
    """Sequential calls produce newline-separated entries in order."""
    test_task.error_message = None
    test_task.save(update_fields=["error_message"])

    append_task_error(test_task, "line one")
    append_task_error(test_task, "line two")
    append_task_error(test_task, "line three")

    persisted = _reload(test_task).error_message
    assert persisted == "line one\nline two\nline three"


def test_append_empty_text_is_noop(test_task):
    """Passing empty/None text leaves the existing message untouched."""
    test_task.error_message = "existing"
    test_task.save(update_fields=["error_message"])

    append_task_error(test_task, "")
    append_task_error(test_task, None)  # type: ignore[arg-type]

    assert _reload(test_task).error_message == "existing"


def test_append_only_updates_error_message_field(test_task):
    """Concurrent writes on other fields must not be clobbered by append."""
    test_task.error_message = None
    test_task.save(update_fields=["error_message"])

    # Simulate a concurrent writer changing `success_rows` in DB after our
    # in-memory instance was loaded. Because append_task_error uses
    # update_fields=['error_message'], the concurrent write should survive.
    ProcessingTask.objects.filter(pk=test_task.pk).update(success_rows=42)

    append_task_error(test_task, "late error")

    fresh = _reload(test_task)
    assert fresh.error_message == "late error"
    assert fresh.success_rows == 42
