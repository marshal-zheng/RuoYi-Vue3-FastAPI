"""File asset HTTP API: upload, metadata, same-origin content streaming and own-draft discard.

There is deliberately no generic bind/unbind endpoint and no pre-signed URL: business saves bind in
their own transactions, and every content use is authorized here and streamed from private storage.
"""

import asyncio
import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.file_assets.api.http import (
    content_headers,
    etag_matches,
    not_modified_headers,
    read_upload_form,
    release_request_transaction,
)
from modules.file_assets.api.schemas import (
    CONTENT_RESPONSES,
    UPLOAD_REQUEST_BODY,
    AssetDescriptorModel,
    AssetMetadataBatchRequest,
    AssetMetadataBatchResponse,
    descriptor_model,
)
from modules.file_assets.application.asset_service import normalize_upload_owner
from modules.file_assets.application.cleanup_service import alert
from modules.file_assets.application.composition import get_file_asset_services
from modules.file_assets.domain.errors import AssetInvalidError, FileAssetsUnavailableError
from modules.file_assets.domain.models import Actor, UploadEntry
from modules.file_assets.infrastructure.s3_storage import ObjectMissingError, StorageError
from modules.identity.ports import get_current_user
from utils.log_util import logger
from utils.response_util import ResponseUtil

if TYPE_CHECKING:  # FastAPI resolves endpoint annotations at runtime; only helper types live here.
    from modules.file_assets.application.asset_service import ContentPlan
    from modules.file_assets.application.runtime import FileAssetRuntime, Slot
    from modules.file_assets.infrastructure.s3_storage import ObjectStream

fileAssetController = APIRouter(prefix='/file-assets')  # noqa: N816


@fileAssetController.post(
    '/uploads',
    response_model=AssetDescriptorModel,
    openapi_extra=UPLOAD_REQUEST_BODY,
    summary='上传文件并创建 READY 草稿资产',
)
async def upload_file_asset(
    request: Request,
    current_user: CurrentUserModel = Depends(get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    # Authentication (any 401) has completed before a single asset row or object exists.
    await release_request_transaction(query_db)
    services = get_file_asset_services()
    services.runtime.require_available()
    slot = await services.runtime.upload_slots.acquire()
    handed_over = False
    try:
        parsed = await read_upload_form(request, 'file')
        try:
            unknown = set(parsed.fields) - {'purpose', 'ownerId'}
            if unknown:
                raise AssetInvalidError('UNKNOWN_FIELD', '上传参数不受支持', field=sorted(unknown)[0])
            spec = services.assets.resolve_purpose(parsed.fields.get('purpose', ''), entry=UploadEntry.GENERIC)
            owner_id = normalize_upload_owner(parsed.fields.get('ownerId'))
        except Exception:
            await parsed.incoming.close()
            raise
        handed_over = True
        descriptor = await services.assets.upload(
            actor=Actor.from_current_user(current_user),
            spec=spec,
            owner_id=owner_id,
            incoming=parsed.incoming,
            slot=slot,
        )
    finally:
        if not handed_over:
            slot.release()
    return ResponseUtil.ok_resource(descriptor_model(descriptor))


@fileAssetController.post(
    '/metadata:batch',
    response_model=AssetMetadataBatchResponse,
    summary='批量读取当前可见资产的元数据',
)
async def batch_file_asset_metadata(
    payload: AssetMetadataBatchRequest,
    current_user: CurrentUserModel = Depends(get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    services = get_file_asset_services()
    services.runtime.require_available()
    items, unavailable = await services.assets.get_metadata(
        query_db, Actor.from_current_user(current_user), payload.asset_ids
    )
    return ResponseUtil.ok_document(
        AssetMetadataBatchResponse(items=[descriptor_model(item) for item in items], unavailable_ids=unavailable)
    )


@fileAssetController.get('/{asset_id}', response_model=AssetDescriptorModel, summary='读取单个资产元数据')
async def get_file_asset(
    asset_id: str,
    current_user: CurrentUserModel = Depends(get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    services = get_file_asset_services()
    services.runtime.require_available()
    descriptor = await services.assets.describe(query_db, Actor.from_current_user(current_user), asset_id)
    return ResponseUtil.ok_resource(descriptor_model(descriptor))


@fileAssetController.get(
    '/{asset_id}/content',
    response_class=StreamingResponse,
    responses=CONTENT_RESPONSES,
    summary='鉴权后从私有存储流式读取内容',
)
async def get_file_asset_content(
    request: Request,
    asset_id: str,
    download: bool = Query(default=False, description='true 时强制 attachment（只能收紧）'),
    current_user: CurrentUserModel = Depends(get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    services = get_file_asset_services()
    runtime = services.runtime
    storage = runtime.require_available()
    plan = await services.assets.authorize_content(query_db, Actor.from_current_user(current_user), asset_id)
    await release_request_transaction(query_db)
    if etag_matches(request.headers.get('if-none-match'), plan.sha256):
        # Authorized revalidation never touches storage.
        runtime.metrics.inc('content_not_modified_total')
        return Response(status_code=304, headers=not_modified_headers(plan.sha256))
    slot = await runtime.download_slots.acquire()
    try:
        stream = await runtime.run_download(storage.open, plan.object_key)
    except ObjectMissingError:
        slot.release()
        runtime.metrics.inc('missing_object_total')
        alert('missing_object', 'authorized READY asset has no stored object', asset=plan.asset_id)
        raise FileAssetsUnavailableError('OBJECT_MISSING') from None
    except StorageError as exc:
        slot.release()
        runtime.metrics.inc('storage_error_total', operation='get')
        logger.warning('file_assets.content storage_error asset={} code={}', plan.asset_id, exc.code)
        raise FileAssetsUnavailableError('STORAGE_UNAVAILABLE') from None
    except BaseException:
        slot.release()
        raise
    runtime.metrics.inc('content_served_total')
    return StreamingResponse(
        _stream_body(runtime, stream, slot, plan),
        status_code=200,
        headers=content_headers(
            media_type=plan.media_type,
            size=plan.size,
            sha256=plan.sha256,
            name=plan.display_name,
            inline=plan.inline and not download,
        ),
    )


async def _stream_body(runtime: 'FileAssetRuntime', stream: 'ObjectStream', slot: 'Slot', plan: 'ContentPlan'):
    """64 KiB chunks read in the bounded download pool; the slot frees only after the last read ends."""
    loop = asyncio.get_running_loop()
    deadline = time.monotonic() + runtime.settings.file_asset_download_response_timeout_seconds
    pending = None

    def finish() -> None:
        stream.close()
        slot.release()

    try:
        while time.monotonic() < deadline:
            pending = runtime.submit_download(stream.read_chunk)
            chunk = await asyncio.wrap_future(pending)
            pending = None
            if not chunk:
                return
            yield chunk
        logger.warning('file_assets.content response_timeout asset={}', plan.asset_id)
    except StorageError as exc:
        logger.warning('file_assets.content stream_error asset={} code={}', plan.asset_id, exc.code)
    finally:
        if pending is not None and not pending.done():
            pending.add_done_callback(lambda _future: loop.call_soon_threadsafe(finish))
        else:
            finish()


@fileAssetController.delete('/{asset_id}', status_code=204, summary='丢弃本人尚未绑定的草稿（可重复执行）')
async def discard_file_asset(
    asset_id: str,
    current_user: CurrentUserModel = Depends(get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    services = get_file_asset_services()
    await services.assets.discard(query_db, Actor.from_current_user(current_user), asset_id)
    await query_db.commit()
    return ResponseUtil.no_content()
