import json

import pytest
from sqlalchemy import JSON, String
from sqlalchemy.exc import StatementError

from scripts.data_migrations import remark_document_v2
from scripts.data_migrations.remark_document_v2 import classify_columns


def test_physical_states_are_not_inferred_from_report_files():
    def cols(**values):
        return [{'name': key, 'type': value} for key, value in values.items()]

    assert classify_columns([]) == 'missing'
    assert classify_columns(cols(remark=String(500))) == 'legacy'
    assert classify_columns(cols(remark=String(500), remark__json_v2=JSON())) == 'backfilling'
    assert classify_columns(cols(remark=JSON(), remark__text_v1=String(500))) == 'switched'
    assert classify_columns(cols(remark=JSON())) == 'complete'
    with pytest.raises(ValueError):
        classify_columns(cols(remark=String(500), remark__text_v1=String(500)))


def test_database_exception_reports_never_expose_document_parameters(monkeypatch, tmp_path):
    private = 'PRIVATE_REMARK_CONTENT'

    def failing_migration(*_args, **_kwargs):
        raise StatementError(
            'failed database write', 'UPDATE sys_user', {'remark': private}, ValueError('driver failure')
        )

    monkeypatch.setattr(remark_document_v2, '_migrate', failing_migration)
    report = tmp_path / 'failure.json'
    with pytest.raises(ValueError, match='database operation failed') as caught:
        remark_document_v2.migrate(object(), report_path=report)
    assert private not in str(caught.value)
    assert private not in report.read_text()
    assert json.loads(report.read_text())['failedPhase'] == 'preflight'
