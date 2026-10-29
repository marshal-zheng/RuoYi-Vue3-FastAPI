"""Business integration on SQLite: notice HTML policy and bindings, user soft delete and avatar projection."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from exceptions.exception import ResourceNotFoundException, ValidationException
from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel
from modules.file_assets.application import composition
from modules.file_assets.domain.models import Actor, AssetState
from modules.file_assets.infrastructure.models import FileBindingDO
from modules.file_assets.tests.conftest import ADMIN, EDITOR, asset_row, upload
from modules.system.application.notice_content import NOTICE_CONTENT_MAX_BYTES, sanitize_notice_html
from modules.system.application.read_models.user_read_models import UserInfoReadModel
from modules.system.application.services.notice_service import NoticeService
from modules.system.application.user_avatars import attach_user_avatars, release_user_assets, replace_user_avatar
from modules.system.infrastructure.notice_repository import NoticeRepository

pytestmark = pytest.mark.usefixtures('seeded')


# --------------------------------------------------------------------- sanitizer ---


def _src(asset_id: str) -> str:
    return f'/file-assets/{asset_id}/content'


def test_supported_quill_formats_survive():
    html = (
        '<h2 class="ql-align-center">标题</h2><p class="ql-indent-2"><strong>粗</strong><em>斜</em><u>下</u><s>删</s>'
        '<span class="ql-size-large" style="color: rgb(230, 0, 0); background-color: #ffff00">色</span>'
        '<a href="https://example.com" target="_blank">链</a><a href="mailto:a@b.c">信</a></p>'
        '<blockquote>引用</blockquote><pre class="ql-syntax" spellcheck="false">x &lt; 1</pre>'
        '<ol><li class="ql-indent-1">一</li></ol><ul><li>二</li></ul><p><br></p>'
    )
    cleaned, ids = sanitize_notice_html(html)
    for fragment in (
        '<h2 class="ql-align-center">',
        '<p class="ql-indent-2">',
        'style="color:rgb(230, 0, 0);background-color:#ffff00"',
        'href="https://example.com" target="_blank" rel="noopener noreferrer"',
        'href="mailto:a@b.c"',
        '<blockquote>引用</blockquote>',
        '<pre class="ql-syntax" spellcheck="false">x &lt; 1</pre>',
        '<li class="ql-indent-1">一</li>',
    ):
        assert fragment in cleaned
    assert ids == []


@pytest.mark.parametrize(
    'payload',
    [
        '<p onclick="alert(1)">x</p>',
        '<p><a href="javascript:alert(1)">x</a></p>',
        '<p style="background-image:url(https://t.example/x)">x</p>',
        '<p style="color: expression(alert(1))">x</p>',
        '<script>alert(1)</script><p>x</p>',
        '<p class="evil ql-align-center">x</p>',
    ],
)
def test_xss_vectors_are_neutralized(payload):
    cleaned, _ = sanitize_notice_html(payload)
    lowered = cleaned.lower()
    assert 'onclick' not in lowered and 'javascript:' not in lowered and 'url(' not in lowered
    assert 'expression' not in lowered and '<script' not in lowered and 'evil' not in lowered


def test_images_are_deduplicated_in_first_occurrence_order():
    a, b = '0966aa3d-09c9-4581-8b20-812d4b959219', '1966aa3d-09c9-4581-8b20-812d4b959219'
    _, ids = sanitize_notice_html(f'<p><img src="{_src(b)}"><img src="{_src(a)}"><img src="{_src(b)}"></p>')
    assert ids == [b, a]


@pytest.mark.parametrize(
    'payload',
    [
        '<p><img src="data:image/png;base64,AAAA"></p>',
        '<p><img src="https://example.com/x.png"></p>',
        '<p><img src="/dev-api/profile/upload/x.png"></p>',
        '<p><img src="/file-assets/0966AA3D-09C9-4581-8B20-812D4B959219/content?x=1"></p>',
        '<p><img></p>',
        '<iframe src="https://www.youtube.com/embed/x"></iframe>',
        '<video src="/x.mp4"></video>',
    ],
)
def test_unsupported_images_and_embeds_are_rejected_not_dropped(payload):
    with pytest.raises(ValidationException):
        sanitize_notice_html(payload)


def test_one_mib_limit_counts_utf8_bytes_not_characters():
    within = '<p>' + '中' * ((NOTICE_CONTENT_MAX_BYTES - 7) // 3) + '</p>'
    assert len(within.encode()) <= NOTICE_CONTENT_MAX_BYTES < len(within) * 3 + 100
    sanitize_notice_html(within)
    with pytest.raises(ValidationException):
        sanitize_notice_html('<p>' + '中' * (NOTICE_CONTENT_MAX_BYTES // 3 + 1) + '</p>')


# ----------------------------------------------------------------- notice service ---


@pytest.fixture
def notice_service(session_factory, registry, runtime):
    composition.set_policy_loader(composition._policy_loader)

    def build(session):
        return NoticeService(notice_repo=NoticeRepository(session), query_db=session)

    return build


async def _bindings(session_factory, owner_id: str) -> list[str]:
    async with session_factory() as session:
        rows = await session.scalars(
            select(FileBindingDO.asset_id)
            .where(FileBindingDO.owner_type == 'system.notice', FileBindingDO.owner_id == owner_id)
            .order_by(FileBindingDO.position)
        )
        return list(rows.all())


async def test_notice_create_edit_delete_keep_html_and_bindings_in_one_transaction(
    assets, session_factory, notice_service
):
    first = await upload(assets, EDITOR)
    async with session_factory() as session:
        service = notice_service(session)
        result = await service.add_notice_services(
            NoticeModel(noticeTitle='t', noticeType='1', noticeContent=f'<p><img src="{_src(first.asset_id)}"></p>'),
            actor=EDITOR,
        )
        await session.commit()
    notice_id = str(result.result['noticeId'])
    assert await _bindings(session_factory, notice_id) == [first.asset_id]

    second = await upload(assets, EDITOR, owner_id=notice_id)
    async with session_factory() as session:
        await notice_service(session).edit_notice_services(
            NoticeModel(noticeId=int(notice_id), noticeContent=f'<p><img src="{_src(second.asset_id)}"></p>'),
            actor=EDITOR,
        )
        await session.commit()
    assert await _bindings(session_factory, notice_id) == [second.asset_id]
    assert (await asset_row(session_factory, first.asset_id)).state == AssetState.DELETING.value

    # Editing other fields only keeps the bindings untouched.
    async with session_factory() as session:
        await notice_service(session).edit_notice_services(
            NoticeModel(noticeId=int(notice_id), noticeTitle='renamed'), actor=EDITOR
        )
        await session.commit()
    assert await _bindings(session_factory, notice_id) == [second.asset_id]

    async with session_factory() as session:
        await notice_service(session).delete_notice_services(DeleteNoticeModel(noticeIds=notice_id))
        await session.commit()
    assert await _bindings(session_factory, notice_id) == []
    assert (await asset_row(session_factory, second.asset_id)).state == AssetState.DELETING.value


async def test_failed_notice_save_keeps_previous_content_and_bindings(assets, session_factory, notice_service):
    first = await upload(assets, EDITOR, owner_id='10')
    async with session_factory() as session:
        await notice_service(session).edit_notice_services(
            NoticeModel(noticeId=10, noticeContent=f'<p><img src="{_src(first.asset_id)}"></p>'), actor=EDITOR
        )
        await session.commit()
    foreign = await upload(assets, ADMIN, owner_id='10')
    async with session_factory() as session:
        with pytest.raises(Exception):  # noqa: B017 - someone else's draft is an invalid reference
            await notice_service(session).edit_notice_services(
                NoticeModel(noticeId=10, noticeContent=f'<p><img src="{_src(foreign.asset_id)}"></p>'), actor=EDITOR
            )
        await session.rollback()
    assert await _bindings(session_factory, '10') == [first.asset_id]
    assert (await asset_row(session_factory, first.asset_id)).state == AssetState.READY.value


# --------------------------------------------------------------------------- users ---


async def test_user_soft_delete_releases_avatar_and_projection(assets, session_factory):
    me = Actor(user_id=2, permissions=frozenset())
    avatar = await upload(assets, me, purpose='user.avatar', owner_id='2')
    async with session_factory() as session:
        await replace_user_avatar(session, me, 2, avatar.asset_id)
        await session.commit()
    async with session_factory() as session:
        users = [UserInfoReadModel(user_id=2), UserInfoReadModel(user_id=3)]
        await attach_user_avatars(session, users)
        assert users[0].avatar_asset_id == avatar.asset_id and users[0].avatar_url == avatar.content_url
        assert users[1].avatar_url is None
        assert users[0].model_dump(by_alias=True)['avatarUrl'] == avatar.content_url
    async with session_factory() as session:
        assert await release_user_assets(session, 2) == [avatar.asset_id]
        await session.commit()
    assert (await asset_row(session_factory, avatar.asset_id)).state == AssetState.DELETING.value


async def test_avatar_replacement_for_deleted_user_is_refused(assets, session_factory):
    me = Actor(user_id=4, permissions=frozenset())
    avatar = await upload(assets, me, purpose='user.avatar', owner_id='4')
    async with session_factory() as session:
        with pytest.raises(ResourceNotFoundException):
            await replace_user_avatar(session, me, 4, avatar.asset_id)
