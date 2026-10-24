"""Public job input boundaries use the actual registered body models."""

import pytest
from pydantic import ValidationError

from modules.scheduler.api.job_controller import jobController


def model(path, method='PUT'):
    return next(r.body_field.type_ for r in jobController.routes if r.path == path and method in r.methods)


def payload(path, method):
    if path.endswith('/run'):
        return {'jobId': 42}
    if path.endswith('/changeStatus'):
        return {'jobId': 42, 'status': '1'}
    return {
        'jobName': 'test',
        'invokeTarget': 'module_task.scheduler_test.job',
        'cronExpression': '0 0 0 * * ?',
        **({'jobId': 42} if method == 'PUT' else {}),
    }


OPERATIONS = [
    ('/monitor/job', 'POST'),
    ('/monitor/job', 'PUT'),
    ('/monitor/job/changeStatus', 'PUT'),
    ('/monitor/job/run', 'PUT'),
]


@pytest.mark.parametrize('path,method', OPERATIONS)
@pytest.mark.parametrize(
    'field,value',
    [
        ('type', 'status'),
        ('createBy', 'forged'),
        ('createTime', '2020-01-01T00:00:00'),
        ('updateBy', 'forged'),
        ('updateTime', '2020-01-01T00:00:00'),
    ],
)
def test_rejects_operation_switch_and_audit_fields(path, method, field, value):
    with pytest.raises(ValidationError):
        model(path, method)(**payload(path, method), **{field: value})


@pytest.mark.parametrize('path', ['/monitor/job', '/monitor/job/changeStatus', '/monitor/job/run'])
@pytest.mark.parametrize('identity', ['missing', None, 0, -1])
def test_positive_identity_required(path, identity):
    data = payload(path, 'PUT')
    if identity == 'missing':
        data.pop('jobId')
    else:
        data['jobId'] = identity
    with pytest.raises(ValidationError):
        model(path)(**data)


@pytest.mark.parametrize('path', ['/monitor/job/changeStatus', '/monitor/job/run'])
def test_narrow_operations_reject_edit_fields(path):
    with pytest.raises(ValidationError):
        model(path)(**payload(path, 'PUT'), invokeTarget='unregistered')


def test_create_rejects_identity():
    with pytest.raises(ValidationError):
        model('/monitor/job', 'POST')(**payload('/monitor/job', 'POST'), jobId=42)


@pytest.mark.parametrize('field', ['jobName', 'invokeTarget', 'cronExpression'])
def test_create_requires_configuration(field):
    data = payload('/monitor/job', 'POST')
    data.pop(field)
    with pytest.raises(ValidationError):
        model('/monitor/job', 'POST')(**data)


def test_edit_preserves_omission_and_allows_clearing_args():
    result = model('/monitor/job')(jobId=42, jobArgs=None, jobKwargs='', remark=None)
    assert result.model_dump(exclude_unset=True) == {'job_id': 42, 'job_args': None, 'job_kwargs': '', 'remark': None}
