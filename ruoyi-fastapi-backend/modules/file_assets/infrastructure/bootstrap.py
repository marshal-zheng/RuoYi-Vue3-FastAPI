"""Explicit storage initialization with separate admin credentials (never used by the web process)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from modules.file_assets.domain.models import INSTALLATION_MARKER_KEY, OBJECT_KEY_PREFIX, object_key_for


def app_policy(bucket: str) -> dict[str, Any]:
    """Least privilege for the application account: own bucket, `assets/` objects, read-only marker."""
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': ['s3:ListBucket', 's3:GetBucketLocation'],
                'Resource': [f'arn:aws:s3:::{bucket}'],
            },
            {
                'Effect': 'Allow',
                'Action': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject'],
                'Resource': [f'arn:aws:s3:::{bucket}/{OBJECT_KEY_PREFIX}*'],
            },
            {
                'Effect': 'Allow',
                'Action': ['s3:GetObject'],
                'Resource': [f'arn:aws:s3:::{bucket}/{INSTALLATION_MARKER_KEY}'],
            },
        ],
    }


@dataclass
class BootstrapReport:
    bucket: str
    created_bucket: bool = False
    marker: str = ''
    findings: list[str] = field(default_factory=list)
    ok: bool = True

    def fail(self, message: str) -> None:
        self.ok = False
        self.findings.append(message)


def _client(endpoint: str, region: str, addressing_style: str, access_key: str, secret_key: str):
    return boto3.session.Session().client(
        's3',
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': addressing_style},
            connect_timeout=3,
            read_timeout=10,
            retries={'mode': 'standard', 'total_max_attempts': 2},
            request_checksum_calculation='when_required',
            response_checksum_validation='when_required',
        ),
    )


def _code(exc: ClientError) -> str:
    return str(exc.response.get('Error', {}).get('Code') or 'ClientError')


def _check_bucket_settings(client, bucket: str, report: BootstrapReport) -> None:
    versioning = client.get_bucket_versioning(Bucket=bucket).get('Status')
    if versioning in {'Enabled', 'Suspended'}:
        report.fail(f'bucket versioning is {versioning}; deletes would leave versions/delete markers')
    try:
        lock = client.get_object_lock_configuration(Bucket=bucket)
        if lock.get('ObjectLockConfiguration', {}).get('ObjectLockEnabled') == 'Enabled':
            report.fail('object lock is enabled; physical deletion cannot be guaranteed')
    except ClientError as exc:
        if _code(exc) not in {'ObjectLockConfigurationNotFoundError', 'NoSuchObjectLockConfiguration'}:
            report.findings.append(f'object lock check: {_code(exc)}')
    try:
        policy = client.get_bucket_policy(Bucket=bucket).get('Policy')
        if policy and '"*"' in policy:
            report.fail('bucket policy grants a wildcard principal; the bucket must stay private')
    except ClientError as exc:
        if _code(exc) not in {'NoSuchBucketPolicy', 'NoSuchBucketPolicyError'}:
            report.findings.append(f'bucket policy check: {_code(exc)}')


def bootstrap_storage(
    *,
    endpoint: str,
    region: str,
    addressing_style: str,
    bucket: str,
    installation_id: str,
    admin_access_key: str,
    admin_secret_key: str,
    take_over: bool = False,
    confirm_installation: str | None = None,
) -> BootstrapReport:
    report = BootstrapReport(bucket=bucket)
    client = _client(endpoint, region, addressing_style, admin_access_key, admin_secret_key)
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if _code(exc) not in {'404', 'NoSuchBucket', 'NotFound'}:
            report.fail(f'head_bucket failed: {_code(exc)}')
            return report
        params: dict[str, Any] = {'Bucket': bucket}
        if region and region != 'us-east-1':
            params['CreateBucketConfiguration'] = {'LocationConstraint': region}
        client.create_bucket(**params)
        report.created_bucket = True

    _check_bucket_settings(client, bucket, report)

    existing = None
    try:
        raw = client.get_object(Bucket=bucket, Key=INSTALLATION_MARKER_KEY)['Body'].read(4096)
        existing = json.loads(raw.decode('utf-8')).get('installationId')
    except ClientError as exc:
        if _code(exc) not in {'NoSuchKey', '404', 'NotFound'}:
            report.fail(f'marker read failed: {_code(exc)}')
            return report
    if existing and existing != installation_id and not (take_over and confirm_installation == existing):
        report.fail(
            f'bucket belongs to installation {existing!r}; refusing to overwrite '
            '(use --take-over --confirm-installation <old id> after confirming the handover)'
        )
        return report
    if existing != installation_id:
        body = json.dumps(
            {'installationId': installation_id, 'createdAt': datetime.now(UTC).isoformat(), 'previous': existing},
            ensure_ascii=True,
        ).encode('ascii')
        client.put_object(Bucket=bucket, Key=INSTALLATION_MARKER_KEY, Body=body, ContentType='application/json')
    report.marker = installation_id
    return report


def check_app_access(
    *,
    endpoint: str,
    region: str,
    addressing_style: str,
    bucket: str,
    installation_id: str,
    access_key: str,
    secret_key: str,
    write_probe: bool = False,
) -> BootstrapReport:
    """Verify the application account: marker readable and matching; optional write/deny probes."""
    report = BootstrapReport(bucket=bucket)
    client = _client(endpoint, region, addressing_style, access_key, secret_key)
    try:
        client.head_bucket(Bucket=bucket)
        client.list_objects_v2(Bucket=bucket, Prefix=OBJECT_KEY_PREFIX, MaxKeys=1)
    except ClientError as exc:
        report.fail(f'bucket access failed: {_code(exc)}')
        return report
    try:
        raw = client.get_object(Bucket=bucket, Key=INSTALLATION_MARKER_KEY)['Body'].read(4096)
        marker = json.loads(raw.decode('utf-8')).get('installationId')
        report.marker = str(marker or '')
        if marker != installation_id:
            report.fail(f'installation marker mismatch: bucket={marker!r} config={installation_id!r}')
    except ClientError as exc:
        report.fail(f'installation marker unreadable: {_code(exc)}')
    if not write_probe:
        return report
    key = object_key_for(str(uuid.uuid4()), datetime.now(UTC))
    try:
        client.put_object(Bucket=bucket, Key=key, Body=b'probe', ContentType='text/plain')
        if client.get_object(Bucket=bucket, Key=key)['Body'].read() != b'probe':
            report.fail('write probe read back different bytes')
        client.delete_object(Bucket=bucket, Key=key)
        client.delete_object(Bucket=bucket, Key=key)  # idempotent delete of a missing key
    except ClientError as exc:
        report.fail(f'write probe failed: {_code(exc)} (a leftover probe key is reported, never auto-deleted)')
    for operation, call in (
        (
            'overwrite installation marker',
            lambda: client.put_object(Bucket=bucket, Key=INSTALLATION_MARKER_KEY, Body=b'x'),
        ),
        ('write outside assets/', lambda: client.put_object(Bucket=bucket, Key='outside/probe', Body=b'x')),
    ):
        try:
            call()
            report.fail(f'application account can {operation}; policy is broader than least privilege')
        except ClientError as exc:
            if _code(exc) != 'AccessDenied':
                report.findings.append(f'{operation}: unexpected {_code(exc)}')
    return report
