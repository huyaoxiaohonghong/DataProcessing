"""
Migration 0006 — Strengthen SheetLineage uniqueness.

Req 3.5 mandates that `(upstream, downstream, relation_type)` be unique **within
the same DataMapping**. The initial 0005 migration locked the triple without
``mapping`` in the unique_together tuple — technically redundant because
``upstream``/``downstream`` FKs already carry the mapping, but the DB-level
constraint should reflect the business intent explicitly so any future cross-
mapping ORM shortcut cannot slip past the constraint.

This migration re-declares ``unique_together`` to include the ``mapping``
column as an explicit guard.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processing', '0005_multi_sheet_lineage'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='sheetlineage',
            unique_together={('mapping', 'upstream', 'downstream', 'relation_type')},
        ),
    ]
