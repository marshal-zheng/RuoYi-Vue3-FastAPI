"""Generated asset fields: explicit declaration, four page templates and an actually generated CRUD fixture.

The runtime part installs the rendered DO/VO/repository/service/controller/policy into a temporary package
and drives them against the real file asset services (SQLite + fake storage; no real S3 semantics claimed).
"""

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.database import Base
from container.file_asset_policies import build_file_asset_policies
from exceptions.exception import ServiceException
from module_generator.asset_fields import asset_template_context, validate_asset_fields
from module_generator.entity.vo.gen_vo import GenTableColumnModel, GenTableModel
from modules.file_assets.application import composition
from modules.file_assets.application.asset_service import AssetService
from modules.file_assets.application.runtime import FileAssetRuntime, OwnershipState
from modules.file_assets.domain.errors import (
    AssetConflictError,
    AssetInvalidError,
    AssetNotFoundError,
    AssetPermissionDeniedError,
    AssetTooLargeError,
    FileAssetError,
)
from modules.file_assets.domain.models import Actor
from modules.file_assets.infrastructure.models import FileAssetDO, FileBindingDO
from modules.file_assets.tests.conftest import make_settings, upload
from modules.file_assets.tests.fakes import FakeStorage
from utils.gen_util import GenUtils
from utils.template_util import TemplateInitializer, TemplateUtils

MIB = 1024 * 1024
BACKEND = Path(__file__).resolve().parents[3]
DOCX = (BACKEND / 'modules/file_assets/tests/fixtures/office/msodde_harmless-clean.docx').read_bytes()
PDF = b'%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 1\ntrailer<<>>\nstartxref\n9\n%%EOF\n'
PACKAGE = 'generated_gallery_demo'
EDITOR = Actor(
    user_id=2,
    permissions=frozenset({f'demo:gallery:{op}' for op in ('add', 'edit', 'query', 'list', 'remove')}),
)
OTHER_EDITOR = Actor(user_id=5, permissions=EDITOR.permissions)
VIEWER = Actor(user_id=3, permissions=frozenset({'demo:gallery:query'}))
OUTSIDER = Actor(user_id=4, permissions=frozenset())


def column(name, field, python_type='str', html='input', *, pk=False, **flags):
    values = {
        'columnName': name,
        'columnComment': name,
        'columnType': 'int' if pk else 'varchar(255)',  # SQLite only auto-assigns INTEGER keys
        'pythonField': field,
        'pythonType': python_type,
        'htmlType': html,
        'isPk': '1' if pk else '0',
        'isIncrement': '1' if pk else '0',
        'isInsert': '1',
        'isEdit': '1',
        'isList': '1',
        'isQuery': '0',
        'isRequired': '0',
    }
    values.update(flags)
    return GenTableColumnModel(**values)


def asset_field(name, kind, types, size_mib, count, **extra):
    return {
        'fieldName': name,
        'label': name,
        'assetKind': kind,
        'allowedTypeIds': types,
        'maxBytes': int(size_mib * MIB),
        'maxCount': count,
        **extra,
    }


DEFAULT_FIELDS = [
    asset_field('coverImages', 'image', ['png', 'jpeg'], 2, 3, required=True, showInList=True),
    asset_field('attachments', 'file', ['pdf'], 10, 5, showInList=True),
    asset_field('documents', 'file', ['docx', 'xlsx'], 20, 5),
]


def gallery_table(category='crud', web='element-plus', *, fields=None, columns=None, sub_fields=None):
    pk = column('gallery_id', 'galleryId', 'int', pk=True)
    child_pk = column('line_id', 'lineId', 'int', pk=True)
    child = GenTableModel(
        className='GalleryLine',
        tableName='gen_gallery_line',
        businessName='line',
        functionName='明细',
        columns=[child_pk, column('gallery_id', 'galleryId', 'int')],
        pkColumn=child_pk,
        assetFields=sub_fields,
    )
    return GenTableModel(
        tableName='gen_gallery_demo',
        tableComment='图库',
        className='GenGalleryDemo',
        moduleName='demo',
        businessName='gallery',
        packageName=PACKAGE,
        functionName='图库',
        functionAuthor='qa',
        tplCategory=category,
        tplWebType=web,
        pkColumn=pk,
        columns=columns
        or [
            pk,
            column('title', 'title'),
            column('parent_id', 'parentId', 'int'),
        ],
        subTable=child if category == 'sub' else None,
        subTableName='gen_gallery_line',
        subTableFkName='gallery_id',
        options=json.dumps({'treeCode': 'gallery_id', 'treeParentCode': 'parent_id', 'treeName': 'title'}),
        assetFields=DEFAULT_FIELDS if fields is None else fields,
    )


def render(table):
    validate_asset_fields(table)
    context = TemplateUtils.prepare_context(table)
    env = TemplateInitializer.init_jinja2()
    templates = TemplateUtils.get_template_list(
        table.tpl_category, table.tpl_web_type, has_assets=bool(table.asset_fields)
    )
    return {name: env.get_template(name).render(**context) for name in templates}


# ---------------------------------------------------------------- declaration ---


@pytest.mark.parametrize(
    ('change', 'message'),
    [
        ({'fields': [asset_field('files', 'file', [], 1, 1)]}, '类型声明无效'),
        ({'fields': [asset_field('photos', 'image', ['pdf'], 1, 1)]}, '类型声明无效'),
        ({'fields': [asset_field('photos', 'image', ['png'], 6, 1)]}, '单个大小上限'),
        ({'fields': [asset_field('files', 'file', ['pdf'], 20, 11)]}, '超过用户草稿配额'),
        ({'fields': [asset_field('files', 'file', ['pdf'], 1, 51)]}, '数量需在'),
        ({'fields': [asset_field('title', 'file', ['pdf'], 1, 1)]}, '冲突'),
        ({'fields': [asset_field('Files', 'file', ['pdf'], 1, 1)]}, 'camelCase'),
        ({'fields': [asset_field('files', 'file', ['pdf'], 1, 1) | {'label': "附件'); import os #"}]}, '标签不能包含'),
        ({'category': 'sub', 'sub_fields': [asset_field('files', 'file', ['pdf'], 1, 1)]}, '子表行不能拥有文件字段'),
        (
            {
                'columns': [
                    column('gallery_id', 'galleryId', 'int', pk=True),
                    column('cover', 'cover', html='imageUpload'),
                ]
            },
            '物理列，不能直接作为文件字段',
        ),
    ],
)
def test_declaration_errors_fail_generation(change, message):
    table = gallery_table(change.pop('category', 'crud'), **change)
    with pytest.raises(ServiceException) as info:
        render(table)
    assert message in info.value.message


def test_purpose_must_fit_the_asset_columns():
    table = gallery_table(fields=[asset_field('attachments', 'file', ['pdf'], 1, 1)])
    table.business_name = 'x' * 50  # demo.<50>.attachments = 67 characters > VARCHAR(64)
    with pytest.raises(ServiceException, match='超过 64 字符'):
        validate_asset_fields(table)


def test_size_hint_never_rounds_below_the_server_limit():
    table = gallery_table(fields=[asset_field('attachments', 'file', ['pdf'], 1, 1) | {'maxBytes': 1500}])
    [field] = asset_template_context(table, 'demo:gallery')['assetFields']
    assert field['sizeMb'] == 0.01 and field['sizeMb'] * MIB >= 1500


def test_semantics_are_never_guessed_from_column_names():
    table = GenTableModel(tableName='t', tableId=1, createBy='qa', updateBy='qa')
    for name in ('cover_image', 'contract_file'):
        guessed = GenTableColumnModel(columnName=name, columnType='varchar(255)')
        GenUtils.init_column_field(guessed, table)
        assert guessed.html_type == 'input'


def test_policy_and_note_are_generated_only_for_declared_fields():
    without = TemplateUtils.get_template_list('crud', 'element-plus')
    assert not any('file_asset' in name for name in without)
    generated = render(gallery_table())
    assert TemplateUtils.get_file_name('python/file_asset_policy.py.jinja2', gallery_table()).endswith(
        f'{PACKAGE}/policy/gallery_file_asset_policy.py'
    )
    note = generated['md/file_assets.md.jinja2']
    assert 'GalleryAssetPolicy()' in note and 'demo:gallery:query' in note


# ------------------------------------------------------------------ templates ---


def _compile_vue(sources: dict[str, str]) -> subprocess.CompletedProcess:
    script = """import {createRequire} from 'node:module';
const require = createRequire(process.argv[1] + '/package.json');
const {parse,compileScript,compileTemplate}=require('@vue/compiler-sfc');
let input='';for await(const part of process.stdin) input+=part;
for(const [filename,source] of Object.entries(JSON.parse(input))) {
 const {descriptor,errors}=parse(source,{filename});if(errors.length)throw errors[0];
 const compiled=compileScript(descriptor,{id:filename});
 const template=compileTemplate({source:descriptor.template.content,filename,id:filename,compilerOptions:{bindingMetadata:compiled.bindings}});
 if(template.errors.length)throw template.errors[0];
}"""
    return subprocess.run(
        ['node', '--input-type=module', '-e', script, str(BACKEND.parent / 'ruoyi-fastapi-frontend')],
        input=json.dumps(sources),
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize('web', ['element-plus', 'element-ui'])
@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
def test_all_four_templates_render_the_same_declaration(category, web):
    generated = render(gallery_table(category, web))
    for name, source in generated.items():
        if name.endswith('.py.jinja2'):
            ast.parse(source, filename=name)
    pages = {name: source for name, source in generated.items() if name.endswith('.vue.jinja2')}
    assert len(pages) == 1
    page = next(iter(pages.values()))
    assert 'purpose="demo.gallery.coverImages"' in page
    assert ":type-ids=\"['png', 'jpeg']\"" in page and ':type-ids="[\'pdf\']"' in page
    assert ':owner-id="form.galleryId"' in page and ':file-size="2.0"' in page and ':limit="3"' in page
    assert '"assetField_coverImages", "assetField_attachments", "assetField_documents"' in page
    assert 'coverImages: [{ type: "array", required: true' in page
    assert 'coverImages: [],' in page
    assert '/common/upload' not in page
    if web == 'element-plus':
        result = _compile_vue(pages)
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('web', ['element-plus', 'element-ui'])
def test_pages_without_asset_fields_render_no_asset_wiring(web):
    generated = render(gallery_table('crud', web, fields=[]))
    page = next(source for name, source in generated.items() if name.endswith('.vue.jinja2'))
    assert 'assetField_' not in page and 'image-upload' not in page and 'file-upload' not in page
    assert not any('file_asset' in name for name in generated)


# --------------------------------------------------------- generated runtime ---


@pytest.fixture(scope='module')
def generated(tmp_path_factory):
    sources = render(gallery_table())
    root = tmp_path_factory.mktemp('generated')
    targets = {
        'python/do.py.jinja2': 'entity/do/gallery_do.py',
        'python/vo.py.jinja2': 'entity/vo/gallery_vo.py',
        'python/repository.py.jinja2': 'repository/gallery_repository.py',
        'python/service.py.jinja2': 'service/gallery_service.py',
        'python/controller.py.jinja2': 'controller/gallery_controller.py',
        'python/file_asset_policy.py.jinja2': 'policy/gallery_file_asset_policy.py',
    }
    for template, target in targets.items():
        path = root / PACKAGE / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sources[template], encoding='utf-8')
        for current in [path.parent, *path.parents]:
            if current == root:
                break
            (current / '__init__.py').touch()
    sys.path.insert(0, str(root))
    try:
        yield SimpleNamespace(
            do=importlib.import_module(f'{PACKAGE}.entity.do.gallery_do'),
            vo=importlib.import_module(f'{PACKAGE}.entity.vo.gallery_vo'),
            service=importlib.import_module(f'{PACKAGE}.service.gallery_service').GalleryService,
            controller=importlib.import_module(f'{PACKAGE}.controller.gallery_controller'),
            policy=importlib.import_module(f'{PACKAGE}.policy.gallery_file_asset_policy'),
        )
    finally:
        sys.path.remove(str(root))
        for name in list(sys.modules):
            if name == PACKAGE or name.startswith(f'{PACKAGE}.'):
                sys.modules.pop(name, None)
        Base.metadata.remove(Base.metadata.tables['gen_gallery_demo'])


@pytest.fixture
async def stack(generated, monkeypatch):
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:', poolclass=StaticPool, connect_args={'check_same_thread': False}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    # The generated policy is registered exactly like the integration note asks (composition root list).
    policy = generated.policy.GalleryAssetPolicy()
    monkeypatch.setattr(composition, '_policy_loader', lambda: [*build_file_asset_policies(), policy])
    monkeypatch.setattr(composition, '_registry', None)
    runtime = FileAssetRuntime(make_settings(), FakeStorage())
    runtime.ownership.state = OwnershipState.CONFIRMED
    assets = AssetService(runtime, composition.get_policy_registry(), factory)
    try:
        yield SimpleNamespace(factory=factory, assets=assets, **vars(generated))
    finally:
        await runtime.stop()
        await engine.dispose()


async def _bindings(stack, owner_id=None):
    async with stack.factory() as session:
        stmt = select(FileBindingDO.field_key, FileBindingDO.asset_id).where(FileBindingDO.owner_type == 'demo.gallery')
        if owner_id is not None:
            stmt = stmt.where(FileBindingDO.owner_id == str(owner_id))
        return sorted((await session.execute(stmt.order_by(FileBindingDO.position))).all())


async def _create(stack, actor=EDITOR, **values):
    async with stack.factory() as session:
        return await stack.service.add_gallery_services(session, stack.vo.GalleryModel(**values), actor)


async def _edit(stack, actor=EDITOR, **values):
    async with stack.factory() as session:
        return await stack.service.edit_gallery_services(session, stack.vo.GalleryModel(**values), actor)


def test_generated_relations_are_not_business_columns(generated):
    assert {c.name for c in inspect(generated.do.GenGalleryDemo).columns} == {
        'gallery_id',
        'title',
        'parent_id',
    }
    app = FastAPI()
    app.include_router(generated.controller.galleryController)
    schemas = app.openapi()['components']['schemas']
    read = schemas['GalleryReadModel']['properties']
    assert read['coverImages']['type'] == 'array' and read['coverImages']['items']['type'] == 'string'
    assert 'coverImages' in schemas['GalleryReadModel'].get('required', []) or 'default' not in read['coverImages']


async def test_generated_crud_binds_projects_replaces_clears_and_releases(stack):
    cover = await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages')
    pdf = await upload(
        stack.assets,
        EDITOR,
        purpose='demo.gallery.attachments',
        data=PDF,
        filename='a.pdf',
        content_type='application/pdf',
    )
    created = await _create(stack, title='first', coverImages=[cover.asset_id], attachments=[pdf.asset_id])
    gallery_id = created.gallery_id
    assert created.cover_images == [cover.asset_id] and created.attachments == [pdf.asset_id]
    async with stack.factory() as session:
        page = await stack.service.get_gallery_list_services(
            session, stack.vo.GalleryPageQueryModel(page=1, pageSize=10), is_page=True
        )
        assert page.items[0]['coverImages'] == [cover.asset_id] and page.items[0]['documents'] == []
        # Readers follow the business read permission; outsiders cannot see the bound content.
        plan = await stack.assets.authorize_content(session, VIEWER, pdf.asset_id)
        assert not plan.inline  # file purposes are always served as attachments
        with pytest.raises(AssetNotFoundError):
            await stack.assets.authorize_content(session, OUTSIDER, pdf.asset_id)

    replacement = await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages', owner_id=str(gallery_id))
    edited = await _edit(stack, galleryId=gallery_id, title='second', coverImages=[replacement.asset_id])
    assert edited.cover_images == [replacement.asset_id] and edited.attachments == [pdf.asset_id]  # absent = unchanged
    cleared = await _edit(stack, galleryId=gallery_id, attachments=[])
    assert cleared.attachments == [] and cleared.cover_images == [replacement.asset_id]
    assert await _bindings(stack, gallery_id) == [('coverImages', replacement.asset_id)]
    async with stack.factory() as session:
        released = await session.get(FileAssetDO, cover.asset_id)
        assert released.first_bound_at is not None and released.delete_after is not None

    async with stack.factory() as session:
        await stack.service.delete_gallery_services(session, stack.vo.DeleteGalleryModel(galleryIds=str(gallery_id)))
    assert await _bindings(stack, gallery_id) == []
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(stack.do.GenGalleryDemo)) == 0
        assert (await session.get(FileAssetDO, replacement.asset_id)).delete_after is not None


async def test_generated_edit_never_binds_to_an_owner_deleted_concurrently(stack, monkeypatch):
    created = await _create(
        stack,
        title='first',
        coverImages=[(await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages')).asset_id],
    )
    draft = await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages', owner_id=str(created.gallery_id))
    repository = importlib.import_module(f'{PACKAGE}.repository.gallery_repository').GalleryRepository

    async def deleted_meanwhile(self, gallery_id):
        return None  # the row vanished between the edit's read and its owner lock

    monkeypatch.setattr(repository, 'lock_gallery', deleted_meanwhile)
    with pytest.raises(ServiceException, match='不存在'):
        await _edit(stack, galleryId=created.gallery_id, coverImages=[draft.asset_id])
    async with stack.factory() as session:
        assert (await session.get(FileAssetDO, draft.asset_id)).first_bound_at is None


async def test_generated_writes_follow_menu_permissions_and_roll_back_as_one(stack):
    with pytest.raises(AssetPermissionDeniedError):
        await upload(stack.assets, OUTSIDER, purpose='demo.gallery.coverImages')
    cover = await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages')
    with pytest.raises(AssetPermissionDeniedError):
        await _create(stack, actor=VIEWER, title='denied', coverImages=[cover.asset_id])
    foreign = await upload(stack.assets, OTHER_EDITOR, purpose='demo.gallery.coverImages')
    with pytest.raises(FileAssetError):
        await _create(stack, title='mixed', coverImages=[cover.asset_id, foreign.asset_id])
    with pytest.raises(ServiceException, match='coverImages不能为空'):
        await _create(stack, title='missing required', coverImages=[])
    # Nothing of the failed business transactions survived: no rows, no bindings, the draft is still unbound.
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(stack.do.GenGalleryDemo)) == 0
        assert (await session.get(FileAssetDO, cover.asset_id)).first_bound_at is None
    assert await _bindings(stack) == []
    created = await _create(stack, title='ok', coverImages=[cover.asset_id])
    with pytest.raises(AssetConflictError):
        await _create(stack, title='steal', coverImages=[cover.asset_id])
    assert await _bindings(stack, created.gallery_id) == [('coverImages', cover.asset_id)]


async def test_generated_type_and_size_limits_are_enforced_by_the_server(stack):
    # The PDF-only field refuses Office even when the browser restriction is bypassed (name or MIME forged).
    for filename, content_type in [
        ('report.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('report.pdf', 'application/pdf'),
    ]:
        with pytest.raises(FileAssetError) as info:
            await upload(
                stack.assets,
                EDITOR,
                purpose='demo.gallery.attachments',
                data=DOCX,
                filename=filename,
                content_type=content_type,
            )
        assert info.value.http_status_code in {415, 422}
    with pytest.raises(AssetTooLargeError):
        await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages', data=b'\x89PNG' + b'0' * (2 * MIB + 1))
    document = await upload(
        stack.assets,
        EDITOR,
        purpose='demo.gallery.documents',
        data=DOCX,
        filename='report.docx',
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    cover = await upload(stack.assets, EDITOR, purpose='demo.gallery.coverImages')
    created = await _create(stack, title='docs', coverImages=[cover.asset_id], documents=[document.asset_id])
    assert created.documents == [document.asset_id]
    async with stack.factory() as session:
        plan = await stack.assets.authorize_content(session, VIEWER, document.asset_id)
    assert not plan.inline and plan.display_name == 'report.docx'
    # A purpose the generated module did not register is rejected outright (no open default).
    with pytest.raises(AssetInvalidError):
        await upload(stack.assets, EDITOR, purpose='demo.gallery.unknown')
