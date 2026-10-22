"""Generated controllers publish the actual document read models in OpenAPI."""

import importlib
import json
import sys
from contextlib import contextmanager

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import TypeAdapter, ValidationError

from common.remark_document_v1 import plain_to_remark
from module_generator.entity.vo.gen_vo import GenTableColumnModel, GenTableModel
from utils.template_util import TemplateInitializer, TemplateUtils


def column(name, python_field, python_type='str', html_type='input', *, primary=False):
    return GenTableColumnModel(
        columnName=name,
        columnComment=name,
        columnType='bigint' if primary else 'json' if html_type == 'remark' else 'varchar(64)',
        pythonField=python_field,
        pythonType=python_type,
        htmlType=html_type,
        isPk='1' if primary else '0',
        isInsert='1',
        isEdit='1',
        isList='1',
        isQuery='0',
        isRequired='0',
    )


@contextmanager
def generated_api(tmp_path, monkeypatch, category, child_only):
    package_name = f'generated_remark_api_{category}_{int(child_only)}'
    primary = column('id', 'id', 'int', primary=True)
    notes = column('review_notes', 'reviewNotes', 'dict', 'remark')
    child = GenTableModel(
        className='ArticleLine',
        businessName='articleline',
        tableName='article_line',
        pkColumn=primary,
        columns=[
            primary,
            column('article_id', 'articleId', 'int'),
            column('line_notes', 'lineNotes', 'dict', 'remark'),
        ],
    )
    table = GenTableModel(
        tableName='article',
        className='Article',
        moduleName='content',
        businessName='article',
        packageName=package_name,
        functionName='文章',
        tplCategory=category,
        tplWebType='element-plus',
        pkColumn=primary,
        columns=[primary, *([] if child_only else [notes])],
        subTable=child if category == 'sub' else None,
        subTableName='article_line',
        subTableFkName='article_id',
        options=json.dumps({'treeCode': 'id', 'treeParentCode': 'parent_id', 'treeName': 'name'}),
    )
    context = TemplateUtils.prepare_context(table)
    env = TemplateInitializer.init_jinja2()
    package = tmp_path / package_name
    for directory in [package, package / 'service', package / 'entity', package / 'entity/vo']:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / '__init__.py').write_text('')
    (package / 'entity/vo/article_vo.py').write_text(env.get_template('python/vo.py.jinja2').render(**context))
    (package / 'article_controller.py').write_text(env.get_template('python/controller.py.jinja2').render(**context))
    # Schema construction needs the service symbol; the real generated DTO and
    # controller modules remain intact. No request or persistence is simulated.
    (package / 'service/article_service.py').write_text('class ArticleService:\n    pass\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        controller = importlib.import_module(f'{package_name}.article_controller')
        vo = importlib.import_module(f'{package_name}.entity.vo.article_vo')
        app = FastAPI()
        app.include_router(controller.articleController)
        yield app, vo
    finally:
        for name in list(sys.modules):
            if name == package_name or name.startswith(f'{package_name}.'):
                sys.modules.pop(name, None)


def resolve_schema(schema, fragment):
    return schema['components']['schemas'][fragment['$ref'].rsplit('/', 1)[1]]


@pytest.mark.parametrize(('category', 'child_only'), [('crud', False), ('tree', False), ('sub', False), ('sub', True)])
def test_generated_openapi_uses_read_dtos_for_all_public_document_responses(
    tmp_path, monkeypatch, category, child_only
):
    with generated_api(tmp_path, monkeypatch, category, child_only) as (app, _vo):
        schema = app.openapi()
        paths = schema['paths']
        for path, method, status in [
            ('/content/article/{id}', 'get', '200'),
            ('/content/article', 'post', '201'),
            ('/content/article', 'put', '200'),
        ]:
            response = paths[path][method]['responses'][status]['content']['application/json']['schema']
            read = resolve_schema(schema, response)
            assert response['$ref'].endswith('/ArticleReadModel')
            if not child_only:
                assert read['properties']['reviewNotesText']['readOnly'] is True
            if category == 'sub':
                child = next(
                    item for item in read['properties']['articlelineList']['anyOf'] if item.get('type') == 'array'
                )
                child_read = resolve_schema(schema, child['items'])
                assert child_read['properties']['lineNotesText']['readOnly'] is True
        response = paths['/content/article/list']['get']['responses']['200']['content']['application/json']['schema']
        collection = resolve_schema(schema, response)
        assert collection['properties']['items']['items']['$ref'].endswith('/ArticleReadModel')
        if category != 'tree':
            assert {'total', 'page', 'pageSize'} <= collection['properties'].keys()
        write = resolve_schema(
            schema, paths['/content/article']['post']['requestBody']['content']['application/json']['schema']
        )
        assert 'reviewNotesText' not in write['properties']


@pytest.mark.parametrize(('category', 'child_only'), [('crud', False), ('tree', False), ('sub', False), ('sub', True)])
def test_generated_response_adapters_keep_authoritative_main_and_child_projection(
    tmp_path, monkeypatch, category, child_only
):
    with generated_api(tmp_path, monkeypatch, category, child_only) as (app, vo):
        doc = plain_to_remark('generated 中文😀', identity_key='article:1:review_notes')
        values = {'id': 1}
        if not child_only:
            values['reviewNotes'] = doc
        if category == 'sub':
            values['articlelineList'] = [{'id': 2, 'articleId': 1, 'lineNotes': doc}]
        read = vo.ArticleReadModel.model_validate(values).model_dump(by_alias=True)
        for route in app.routes:
            if not isinstance(route, APIRoute) or route.path not in {
                '/content/article',
                '/content/article/{id}',
                '/content/article/list',
            }:
                continue
            payload = read
            if route.path.endswith('/list'):
                payload = {'items': [read], **({} if category == 'tree' else {'total': 1, 'page': 1, 'pageSize': 10})}
            parsed = TypeAdapter(route.response_model).validate_python(payload).model_dump(by_alias=True)
            record = parsed['items'][0] if 'items' in parsed else parsed
            if not child_only:
                assert record['reviewNotes'] == doc
                assert record['reviewNotesText'] == 'generated 中文😀'
            if category == 'sub':
                assert record['articlelineList'][0]['lineNotesText'] == 'generated 中文😀'
        forged = {**values, 'reviewNotesText': 'forged'}
        with pytest.raises(ValidationError, match='extra_forbidden'):
            vo.ArticleModel.model_validate(forged)
