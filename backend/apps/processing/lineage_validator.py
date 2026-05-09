"""
Lineage validator for DataMapping submissions.

This module operates on plain dicts from serializer ``validated_data``
(no ORM instances), making it reusable across serializer ``validate()``
and unit tests without database setup.

Split of responsibilities:
- :func:`validate_structural`: hard errors that should raise
  :class:`rest_framework.exceptions.ValidationError` before any DB write.
- :func:`collect_unknown_refs`: non-fatal warnings describing entries
  that will be silently ignored during ``_rebuild_children``.

All functions are pure with respect to their inputs and do not touch
the database or any ORM model. See
``design.md`` §2.2 ("新增模块：lineage_validator.py") for the
specification this module implements.
"""
from typing import Any, Dict, List, Tuple

from rest_framework.exceptions import ValidationError


# --- Warning type constants (stable identifiers for API consumers) --------
WARNING_SHEET_LINEAGE_IGNORED = 'sheet_lineage_ignored'
WARNING_FIELD_LINEAGE_IGNORED = 'field_lineage_ignored'
WARNING_CROSS_SHEET_REF_UNRESOLVED = 'cross_sheet_ref_unresolved'

# Default relation_type when the payload omits it. Must match
# ``SheetLineage.RelationType.DERIVED``. Duplicated here to avoid a model
# import cycle; the serializer ChoiceField enforces the real set.
_DEFAULT_RELATION_TYPE = 'derived'

# FieldType.CROSS_SHEET_REF raw value. Duplicated to keep this module
# ORM-free; the serializer ChoiceField guards the real choice set.
_FIELD_TYPE_CROSS_SHEET_REF = 'cross_sheet_ref'


def validate_structural(
    target_sheets_data: List[Dict[str, Any]],
    sheet_lineages_data: List[Dict[str, Any]],
    field_lineages_data: List[Dict[str, Any]],
) -> None:
    """Perform pre-write structural validation on the submitted payload.

    Any violation aborts the whole submission: the caller is expected to
    run this before touching the database.

    Raises:
        rest_framework.exceptions.ValidationError: when any of:

        - **Req 1.3** — two ``target_sheets`` entries share the same
          ``sheet_name`` within the same mapping.
        - **Req 3.3** — a ``sheet_lineages`` entry has
          ``upstream == downstream`` (self-loop).
        - **Req 3.5** — two ``sheet_lineages`` entries form an
          identical ``(upstream, downstream, relation_type)`` triple.

    Args:
        target_sheets_data: list of target sheet dicts (as produced by
            ``_MappingTargetSheetWriteSerializer``).
        sheet_lineages_data: list of sheet lineage dicts.
        field_lineages_data: list of field lineage dicts. Currently not
            inspected structurally but accepted for API symmetry and
            future expansion.
    """
    target_sheets_data = target_sheets_data or []
    sheet_lineages_data = sheet_lineages_data or []
    # field_lineages_data is accepted for forward-compat; not used today.
    _ = field_lineages_data

    errors: Dict[str, List[Dict[str, Any]]] = {}

    # ---- Req 1.3: duplicate sheet_name within the same mapping -----------
    duplicate_name_errors = _find_duplicate_sheet_names(target_sheets_data)
    if duplicate_name_errors:
        errors['target_sheets'] = [
            {
                'index': d['index'],
                'sheet_name': (
                    f"sheet_name 在同一 mapping 下重复：{d['sheet_name']}"
                    f"（首次出现位置 index={d['first_index']}）"
                ),
            }
            for d in duplicate_name_errors
        ]

    # ---- Req 3.3 & Req 3.5: self-loop and duplicate triple ---------------
    sheet_lineage_errors = _find_sheet_lineage_errors(sheet_lineages_data)
    if sheet_lineage_errors:
        errors['sheet_lineages'] = sheet_lineage_errors

    if errors:
        raise ValidationError(errors)


def collect_unknown_refs(
    target_sheets_data: List[Dict[str, Any]],
    sheet_lineages_data: List[Dict[str, Any]],
    field_lineages_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Collect non-fatal warnings about entries that will be silently
    skipped during ``_rebuild_children``.

    Returns:
        A list of warning dicts. Every item carries a stable ``type``
        identifier so API consumers can branch on it.

        - ``sheet_lineage_ignored`` — **Req 3.2**: a ``sheet_lineages``
          entry references a ``sheet_name`` absent from
          ``target_sheets``. Shape::

              {"type": "sheet_lineage_ignored", "index": i,
               "upstream": "...", "downstream": "...",
               "missing": ["upstream" | "downstream", ...],
               "reason": "sheet_not_found"}

        - ``field_lineage_ignored`` — **Req 4.2**: a ``field_lineages``
          entry references a ``sheet_name`` absent from
          ``target_sheets``. Shape::

              {"type": "field_lineage_ignored", "index": i,
               "upstream_sheet": "...", "downstream_sheet": "...",
               "upstream_field": "...", "downstream_field": "...",
               "missing": ["upstream_sheet" | "downstream_sheet", ...],
               "reason": "sheet_not_found"}

        - ``cross_sheet_ref_unresolved`` — **Req 6.3**: a
          ``cross_sheet_ref`` field whose ``source_target_sheet_name``
          does not match any submitted target sheet. Shape::

              {"type": "cross_sheet_ref_unresolved",
               "sheet_index": i, "sheet": "<parent sheet_name>",
               "field_index": j, "field": "<target_field>",
               "reference": "<source_target_sheet_name>",
               "reason": "source_target_sheet_not_found"}

    Args:
        target_sheets_data: list of target sheet dicts.
        sheet_lineages_data: list of sheet lineage dicts.
        field_lineages_data: list of field lineage dicts.
    """
    target_sheets_data = target_sheets_data or []
    sheet_lineages_data = sheet_lineages_data or []
    field_lineages_data = field_lineages_data or []

    known_sheet_names = {
        ts.get('sheet_name', '')
        for ts in target_sheets_data
        if ts.get('sheet_name', '')
    }

    warnings: List[Dict[str, Any]] = []
    warnings.extend(_collect_sheet_lineage_warnings(
        sheet_lineages_data, known_sheet_names,
    ))
    warnings.extend(_collect_field_lineage_warnings(
        field_lineages_data, known_sheet_names,
    ))
    warnings.extend(_collect_cross_sheet_ref_warnings(
        target_sheets_data, known_sheet_names,
    ))
    return warnings


# --- Internal helpers ------------------------------------------------------

def _find_duplicate_sheet_names(
    target_sheets_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return per-index records for every duplicate ``sheet_name`` (Req 1.3)."""
    seen: Dict[str, int] = {}
    duplicates: List[Dict[str, Any]] = []
    for idx, ts in enumerate(target_sheets_data):
        name = ts.get('sheet_name', '')
        if not name:
            # Empty sheet_name is rejected by ``CharField`` at the serializer
            # layer; keep this branch defensive and skip rather than mask
            # the real DRF message.
            continue
        if name in seen:
            duplicates.append({
                'index': idx,
                'sheet_name': name,
                'first_index': seen[name],
            })
        else:
            seen[name] = idx
    return duplicates


def _find_sheet_lineage_errors(
    sheet_lineages_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return DRF-shaped error records for Req 3.3 and Req 3.5."""
    errors: List[Dict[str, Any]] = []
    seen_triples: Dict[Tuple[str, str, str], int] = {}
    for idx, sl in enumerate(sheet_lineages_data):
        upstream = sl.get('upstream', '')
        downstream = sl.get('downstream', '')
        relation_type = sl.get('relation_type', _DEFAULT_RELATION_TYPE)

        # Req 3.3: self-loop is always rejected, and we do not record its
        # triple so users get a single clear error per row.
        if upstream and downstream and upstream == downstream:
            errors.append({
                'index': idx,
                'detail': (
                    f"不允许自环：upstream 与 downstream 均为 '{upstream}'"
                ),
            })
            continue

        # Req 3.5: duplicate (upstream, downstream, relation_type) triple
        triple = (upstream, downstream, relation_type)
        if triple in seen_triples:
            errors.append({
                'index': idx,
                'detail': (
                    "(upstream, downstream, relation_type) 三元组重复："
                    f"({upstream}, {downstream}, {relation_type})"
                    f"（首次出现位置 index={seen_triples[triple]}）"
                ),
            })
        else:
            seen_triples[triple] = idx
    return errors


def _collect_sheet_lineage_warnings(
    sheet_lineages_data: List[Dict[str, Any]],
    known_sheet_names: set,
) -> List[Dict[str, Any]]:
    """Build Req 3.2 warnings for sheet lineages referencing unknown sheets."""
    warnings: List[Dict[str, Any]] = []
    for idx, sl in enumerate(sheet_lineages_data):
        up = sl.get('upstream', '')
        down = sl.get('downstream', '')
        missing: List[str] = []
        if up and up not in known_sheet_names:
            missing.append('upstream')
        if down and down not in known_sheet_names:
            missing.append('downstream')
        if not missing:
            continue
        warnings.append({
            'type': WARNING_SHEET_LINEAGE_IGNORED,
            'index': idx,
            'upstream': up,
            'downstream': down,
            'missing': missing,
            'reason': 'sheet_not_found',
        })
    return warnings


def _collect_field_lineage_warnings(
    field_lineages_data: List[Dict[str, Any]],
    known_sheet_names: set,
) -> List[Dict[str, Any]]:
    """Build Req 4.2 warnings for field lineages referencing unknown sheets."""
    warnings: List[Dict[str, Any]] = []
    for idx, fl in enumerate(field_lineages_data):
        up = fl.get('upstream_sheet', '')
        down = fl.get('downstream_sheet', '')
        missing: List[str] = []
        if up and up not in known_sheet_names:
            missing.append('upstream_sheet')
        if down and down not in known_sheet_names:
            missing.append('downstream_sheet')
        if not missing:
            continue
        warnings.append({
            'type': WARNING_FIELD_LINEAGE_IGNORED,
            'index': idx,
            'upstream_sheet': up,
            'downstream_sheet': down,
            'upstream_field': fl.get('upstream_field', ''),
            'downstream_field': fl.get('downstream_field', ''),
            'missing': missing,
            'reason': 'sheet_not_found',
        })
    return warnings


def _collect_cross_sheet_ref_warnings(
    target_sheets_data: List[Dict[str, Any]],
    known_sheet_names: set,
) -> List[Dict[str, Any]]:
    """Build Req 6.3 warnings for unresolved cross_sheet_ref fields."""
    warnings: List[Dict[str, Any]] = []
    for ts_idx, ts in enumerate(target_sheets_data):
        fields = ts.get('fields', []) or []
        for fd_idx, fd in enumerate(fields):
            if fd.get('field_type') != _FIELD_TYPE_CROSS_SHEET_REF:
                continue
            ref_name = fd.get('source_target_sheet_name', '')
            if not ref_name:
                # Empty reference is a runtime no-op (resolver returns
                # None, per Req 6.6); not a configuration warning.
                continue
            if ref_name in known_sheet_names:
                continue
            warnings.append({
                'type': WARNING_CROSS_SHEET_REF_UNRESOLVED,
                'sheet_index': ts_idx,
                'sheet': ts.get('sheet_name', ''),
                'field_index': fd_idx,
                'field': fd.get('target_field', ''),
                'reference': ref_name,
                'reason': 'source_target_sheet_not_found',
            })
    return warnings
