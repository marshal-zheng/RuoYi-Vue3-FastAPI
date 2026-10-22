import ast
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

from common.remark_document_v1 import plain_to_remark, remark_to_storage
from config import database
from exceptions.exception import ServiceException
from module_generator.entity.vo.gen_vo import GenTableColumnModel, GenTableModel
from module_generator.remark_policy import validate_remark_generation
from utils.template_util import TemplateInitializer, TemplateUtils

EDITOR_IMPORT = 'import Editor from "@/components/ui/Editor/index.vue";'


def _column(**overrides) -> GenTableColumnModel:
    return GenTableColumnModel.model_validate(
        {
            'columnName': 'body',
            'columnComment': '正文',
            'columnType': 'text',
            'pythonField': 'body',
            'pythonType': 'str',
            'htmlType': 'editor',
            'isPk': '0',
            'isInsert': '1',
            'isEdit': '1',
            'isList': '0',
            'isQuery': '0',
            'dictType': '',
            **overrides,
        }
    )


def _render(category: str, column: GenTableColumnModel, *, tree_parent: str = 'parent_id') -> str:
    primary = _column(columnName='id', pythonField='id', pythonType='int', isPk='1', htmlType='input')
    child = GenTableModel.model_validate(
        {'className': 'ArticleLine', 'tableName': 'article_line', 'columns': [primary]}
    )
    table = GenTableModel.model_validate(
        {
            'tableName': 'article',
            'className': 'Article',
            'moduleName': 'content',
            'businessName': 'article',
            'packageName': 'module_content',
            'functionName': '文章',
            'tplCategory': category,
            'tplWebType': 'element-plus',
            'pkColumn': primary,
            'columns': [primary, column],
            'subTable': child,
            'subTableName': 'article_line',
            'subTableFkName': 'article_id',
            'options': json.dumps({'treeCode': 'id', 'treeParentCode': tree_parent, 'treeName': 'body'}),
        }
    )
    templates = TemplateUtils.get_template_list(table.tpl_category, table.tpl_web_type)
    pages = [template for template in templates if template.endswith('.vue.jinja2')]
    expected = 'index-tree.vue.jinja2' if category == 'tree' else 'index.vue.jinja2'
    assert pages == [f'vue/v3/{expected}']
    context = TemplateUtils.prepare_context(table)
    return TemplateInitializer.init_jinja2().get_template(pages[0]).render(**context)


@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
@pytest.mark.parametrize('mode', ['insert', 'edit'])
def test_rendered_editor_has_a_local_component_import(category: str, mode: str):
    source = _render(
        category, _column(isInsert='1' if mode == 'insert' else '0', isEdit='1' if mode == 'edit' else '0')
    )

    assert '<editor v-model="form.body" :min-height="192"/>' in source
    assert source.count(EDITOR_IMPORT) == 1


@pytest.mark.parametrize('category', ['crud', 'tree'])
@pytest.mark.parametrize(
    'overrides',
    [
        {'htmlType': 'input'},
        {'isInsert': '0', 'isEdit': '0'},
        {'isPk': '1'},
        {'columnName': 'create_by'},
        {'columnName': 'update_time'},
        {'pythonField': 'createTime'},
    ],
)
def test_pages_without_a_rendered_editor_do_not_import_it(category: str, overrides: dict):
    source = _render(category, _column(**overrides))

    assert '<editor ' not in source
    assert EDITOR_IMPORT not in source


def test_tree_parent_control_takes_precedence_without_loading_editor():
    source = _render('tree', _column(), tree_parent='body')

    assert '<el-tree-select' in source
    assert '<editor ' not in source
    assert EDITOR_IMPORT not in source


@pytest.mark.parametrize('category', ['crud', 'tree'])
def test_usable_super_column_keeps_its_rendered_editor(category: str):
    source = _render(category, _column(columnName='remark', pythonField='remark'))

    assert '<editor v-model="form.remark" :min-height="192"/>' in source
    assert source.count(EDITOR_IMPORT) == 1


@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
def test_explicit_remark_uses_shared_document_field(category):
    source = _render(
        category, _column(columnName='memo', pythonField='memo', columnType='json', htmlType='remark', isList='1')
    )
    assert '<RemarkEditor' in source
    assert 'form.memo' in source
    assert '<editor v-model="form.memo"' not in source
    assert 'readRemark(' in source


def test_vue2_and_non_nullable_remark_are_refused():
    table = GenTableModel(tplWebType='element-ui', columns=[_column(columnType='json', htmlType='remark')])
    with pytest.raises(ServiceException):
        validate_remark_generation(table)
    table.tpl_web_type = 'element-plus'
    table.columns[0].is_required = '1'
    with pytest.raises(ServiceException):
        validate_remark_generation(table)


def _remark_table(category='crud', *, child_remark=True):
    primary = _column(
        columnName='id', pythonField='id', columnType='bigint', pythonType='int', isPk='1', htmlType='input'
    )
    memo = _column(
        columnName='review_notes',
        pythonField='reviewNotes',
        columnType='json',
        pythonType='dict',
        htmlType='remark',
        isList='1',
    )
    child = GenTableModel.model_validate(
        {
            'className': 'ArticleLine',
            'businessName': 'articleline',
            'tableName': 'article_line',
            'pkColumn': primary,
            'columns': [
                primary,
                _column(
                    columnName='article_id',
                    pythonField='articleId',
                    columnType='bigint',
                    pythonType='int',
                    htmlType='input',
                ),
                *(
                    [
                        _column(
                            columnName='line_notes',
                            pythonField='lineNotes',
                            columnType='json',
                            pythonType='dict',
                            htmlType='remark',
                            isList='1',
                        )
                    ]
                    if child_remark
                    else []
                ),
            ],
        }
    )
    return GenTableModel.model_validate(
        {
            'tableName': 'article',
            'className': 'Article',
            'moduleName': 'content',
            'businessName': 'article',
            'packageName': 'module_content',
            'functionName': '文章',
            'tplCategory': category,
            'tplWebType': 'element-plus',
            'pkColumn': primary,
            'columns': [primary, memo],
            'subTable': child if category == 'sub' else None,
            'subTableName': 'article_line',
            'subTableFkName': 'article_id',
            'options': json.dumps({'treeCode': 'id', 'treeParentCode': 'parent_id', 'treeName': 'name'}),
        }
    )


def _generated(table):
    context = TemplateUtils.prepare_context(table)
    env = TemplateInitializer.init_jinja2()
    return {
        name: env.get_template(name).render(**context)
        for name in TemplateUtils.get_template_list(table.tpl_category, table.tpl_web_type)
    }


@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
def test_actual_generated_python_parses_and_vue_sfc_compiles(category):
    generated = _generated(_remark_table(category))
    for name, source in generated.items():
        if name.endswith('.py.jinja2'):
            ast.parse(source, filename=name)
    frontend = Path.cwd().parent / 'ruoyi-fastapi-frontend'
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
    result = subprocess.run(
        ['node', '--input-type=module', '-e', script, str(frontend)],
        input=json.dumps({n: s for n, s in generated.items() if n.endswith('.vue.jinja2')}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
def test_generated_dto_roundtrip_and_readonly_projection(tmp_path, category):
    source = _generated(_remark_table(category))['python/vo.py.jinja2']
    module_path = tmp_path / 'generated_vo.py'
    module_path.write_text(source)
    module_name = f'generated_remark_{category}'
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        document = plain_to_remark('主表\n中文 👩‍💻', identity_key='article:1:review_notes')
        payload = {'id': 1, 'reviewNotes': document}
        if category == 'sub':
            payload['articlelineList'] = [
                {'id': 2, 'lineNotes': plain_to_remark('子表', identity_key='article_line:2:line_notes')}
            ]
        dto = module.ArticleModel.model_validate(payload)
        stored = dto.model_dump(exclude_unset=True)
        assert remark_to_storage(dto.review_notes) == document
        assert module.ArticleModel.model_validate({'id': 1}).model_dump(exclude_unset=True) == {'id': 1}
        assert (
            module.ArticleModel.model_validate({'id': 1, 'reviewNotes': None}).model_dump(exclude_unset=True)[
                'review_notes'
            ]
            is None
        )
        read = module.ArticleReadModel.model_validate(stored).model_dump(by_alias=True)
        assert read['reviewNotesText'] == '主表\n中文 👩‍💻'
        if category == 'sub':
            assert read['articlelineList'][0]['lineNotesText'] == '子表'
            with pytest.raises(ValidationError):
                module.ArticleModel.model_validate({**payload, 'articlelineList': [{'lineNotesText': '伪造'}]})
        with pytest.raises(ValidationError):
            module.ArticleModel.model_validate({**payload, 'reviewNotesText': '伪造'})
        with pytest.raises(ValidationError):
            module.ArticleModel.model_validate({**payload, 'reviewNotes': '旧字符串'})
    finally:
        sys.modules.pop(module_name, None)


def test_generated_submit_excludes_server_text_for_master_and_children():
    source = _generated(_remark_table('sub'))['vue/v3/index.vue.jinja2']
    assert 'delete submitData.reviewNotesText' in source
    assert 'child.lineNotes = row.lineNotes' in source
    assert 'row.index =' not in source


@pytest.mark.parametrize('flag', ['isRequired', 'isPk', 'isQuery', 'isUnique'])
def test_remark_policy_rejects_flags_from_the_actual_saved_fields(flag):
    table = _remark_table()
    table.columns[1] = _column(columnType='json', htmlType='remark', **{flag: '1'})
    with pytest.raises(ServiceException):
        validate_remark_generation(table)


@pytest.mark.parametrize(
    'source',
    [
        None,
        {'column_type': 'longtext', 'is_required': '0'},
        {'column_type': 'json', 'is_required': '1'},
        {'column_type': 'json', 'is_required': '0', 'is_pk': '1'},
    ],
)
def test_remark_policy_requires_actual_nullable_native_json(source):
    table = _remark_table()
    with pytest.raises(ServiceException):
        validate_remark_generation(table, {'article': {'review_notes': source}})
    validate_remark_generation(table, {'article': {'review_notes': {'column_type': 'json', 'is_required': '0'}}})


@pytest.mark.parametrize('child', [False, True])
@pytest.mark.parametrize('collision', ['storage', 'client'])
def test_remark_policy_refuses_derived_text_names_that_collide_with_real_columns(child, collision):
    table = _remark_table('sub')
    owner = table.sub_table if child else table
    remark = next(column for column in owner.columns if column.html_type == 'remark')
    owner.columns.append(
        _column(
            columnName=f'{remark.column_name}_text' if collision == 'storage' else 'business_text',
            pythonField=f'{remark.python_field}Text' if collision == 'client' else 'businessText',
            htmlType='input',
        )
    )
    with pytest.raises(ServiceException, match='派生字段'):
        validate_remark_generation(table)


@pytest.mark.parametrize('category', ['crud', 'tree', 'sub'])
@pytest.mark.parametrize('insert,edit,list_', [('1', '0', '0'), ('0', '1', '0'), ('0', '0', '1'), ('0', '0', '0')])
def test_explicit_remark_rendering_respects_insert_edit_and_list_flags(category, insert, edit, list_):
    table = _remark_table(category, child_remark=False)
    table.columns[1] = _column(
        columnName='review_notes',
        pythonField='reviewNotes',
        columnType='json',
        pythonType='dict',
        htmlType='remark',
        isInsert=insert,
        isEdit=edit,
        isList=list_,
    )
    source = next(value for name, value in _generated(table).items() if name.endswith('.vue.jinja2'))
    assert ('v-model="form.reviewNotes"' in source) == (insert == '1' or edit == '1')
    assert ('prop="reviewNotesText"' in source) == (list_ == '1')


def test_non_remark_json_does_not_enable_the_remark_contract():
    table = _remark_table()
    table.columns[1].html_type = 'textarea'
    generated = _generated(table)
    assert 'RemarkValue' not in generated['python/vo.py.jinja2']
    assert 'RemarkEditor' not in generated['vue/v3/index.vue.jinja2']


@pytest.mark.parametrize('category', ['crud', 'sub'])
def test_actual_generated_mapping_saves_and_reads_complete_documents(tmp_path, monkeypatch, category):
    class GeneratedBase(DeclarativeBase):
        pass

    monkeypatch.setattr(database, 'Base', GeneratedBase)
    generated = _generated(_remark_table(category))
    modules = []
    try:
        for facet in ['vo', 'do']:
            path = tmp_path / f'{facet}.py'
            path.write_text(generated[f'python/{facet}.py.jinja2'])
            name = f'generated_mapping_{category}_{facet}'
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            modules.append(module)
            spec.loader.exec_module(module)
        vo, do = modules
        engine = create_engine('sqlite://')
        GeneratedBase.metadata.create_all(engine)
        document = plain_to_remark('完整 JSON 👩‍💻', identity_key='article:1:review_notes')
        child_document = plain_to_remark('子行\n步骤', identity_key='article_line:2:line_notes')
        with Session(engine) as session:
            row = do.Article(id=1, review_notes=document)
            if category == 'sub':
                row.articleline_list = [do.ArticleLine(id=2, article_id=1, line_notes=child_document)]
            session.add(row)
            session.commit()
            session.expire_all()
            restored = session.get(do.Article, 1)
            read = vo.ArticleReadModel.model_validate(restored).model_dump(by_alias=True)
            assert read['reviewNotes'] == document
            assert read['reviewNotesText'] == '完整 JSON 👩‍💻'
            if category == 'sub':
                assert read['articlelineList'][0]['lineNotes'] == child_document
                assert read['articlelineList'][0]['lineNotesText'] == '子行\n步骤'
            restored.review_notes = None
            session.commit()
            assert session.execute(text('SELECT review_notes IS NULL FROM article')).scalar() == 1
            assert do.Article.__table__.c.review_notes.type.none_as_null is True
            assert do.Article.__table__.c.review_notes.nullable is True
        engine.dispose()
    finally:
        for module in modules:
            sys.modules.pop(module.__name__, None)


@pytest.mark.asyncio
async def test_actual_generated_sub_service_saves_parent_identity_and_document_roundtrip(tmp_path, monkeypatch):
    class GeneratedBase(DeclarativeBase):
        pass

    class AwaitableSession:
        def __init__(self, session):
            self.session = session

        def add(self, row):
            self.session.add(row)

        async def execute(self, *args, **kwargs):
            return self.session.execute(*args, **kwargs)

        async def flush(self):
            self.session.flush()

        async def commit(self):
            self.session.commit()

        async def rollback(self):
            self.session.rollback()

    monkeypatch.setattr(database, 'Base', GeneratedBase)
    generated = _generated(_remark_table('sub'))
    package = tmp_path / 'module_content'
    for facet, target in [
        ('vo', 'entity/vo'),
        ('do', 'entity/do'),
        ('repository', 'repository'),
        ('service', 'service'),
    ]:
        directory = package / target
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f'article_{facet}.py').write_text(generated[f'python/{facet}.py.jinja2'])
        for current in [directory, *directory.parents]:
            if current == tmp_path:
                break
            (current / '__init__.py').touch()
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        service = importlib.import_module('module_content.service.article_service').ArticleService
        vo = importlib.import_module('module_content.entity.vo.article_vo')
        engine = create_engine('sqlite://')
        GeneratedBase.metadata.create_all(engine)
        document = plain_to_remark('主记录', identity_key='article:9:review_notes')
        child_document = plain_to_remark('新子行😀', identity_key='article_line:2:line_notes')
        with Session(engine) as session:
            dto = vo.ArticleModel.model_validate(
                {'id': 9, 'reviewNotes': document, 'articlelineList': [{'id': 2, 'lineNotes': child_document}]}
            )
            result = await service.add_article_services(AwaitableSession(session), dto)
            response = result.model_dump(by_alias=True)
            assert response['reviewNotes'] == document
            assert len(response['articlelineList']) == 1
            assert response['articlelineList'][0]['articleId'] == 9
            assert response['articlelineList'][0]['lineNotes'] == child_document
            assert response['articlelineList'][0]['lineNotesText'] == '新子行😀'
        engine.dispose()
    finally:
        for name in list(sys.modules):
            if name == 'module_content' or name.startswith('module_content.'):
                sys.modules.pop(name, None)


def test_actual_generated_page_submit_serializes_only_declared_child_fields(tmp_path):
    generated = _generated(_remark_table('sub'))
    frontend = Path.cwd().parent / 'ruoyi-fastapi-frontend'
    document = plain_to_remark('主表', identity_key='article:1:review_notes')
    child_document = plain_to_remark('子表', identity_key='article_line:2:line_notes')
    script = """import {createRequire} from 'node:module';
const require=createRequire(process.argv[1]+'/package.json');
const Vue=require('vue'),ts=require('typescript'),{parse,compileScript}=require('@vue/compiler-sfc');
let input='';for await(const chunk of process.stdin)input+=chunk;
const {source,main,children}=JSON.parse(input);
let submitted;
const api={listArticle:async()=>({items:[],total:0}),getArticle:async()=>main,
 updateArticle:async value=>{submitted=JSON.parse(JSON.stringify(value))},addArticle:async value=>{submitted=JSON.parse(JSON.stringify(value))}};
const modules={vue:Vue,'@/utils/operation':{useOperation:action=>({run:action,pending:Vue.ref(false)})},
 '@/components/ui/Remark/RemarkEditor.vue':{},'@/components/ui/Remark/RemarkDisplay.vue':{},
 '@/components/ui/Remark/contract':{readRemark:value=>value??null},'@/api/content/article':api};
const globals={...Vue,getCurrentInstance:()=>({proxy:{$refs:{articleRef:{validate:async()=>true}},$modal:{},resetForm(){}}})};
const compiled=compileScript(parse(source).descriptor,{id:'generated-submit'});
const js=ts.transpileModule(compiled.content,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const exports={};new Function(...Object.keys(globals),'require','exports',js)(...Object.values(globals),id=>modules[id],exports);
const state=exports.default.setup({}, {expose(){}});
await Promise.resolve();state.form.value=main;state.articlelineList.value=children;
await state.submitForm();process.stdout.write(JSON.stringify(submitted));"""
    payload = {
        'source': generated['vue/v3/index.vue.jinja2'],
        'main': {'id': 1, 'reviewNotes': document, 'reviewNotesText': 'server'},
        'children': [{'id': 2, 'articleId': 1, 'lineNotes': child_document, 'lineNotesText': 'server', 'index': 99}],
    }
    result = subprocess.run(
        ['node', '--input-type=module', '-e', script, str(frontend)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    request = json.loads(result.stdout)
    path = tmp_path / 'submit_vo.py'
    path.write_text(generated['python/vo.py.jinja2'])
    spec = importlib.util.spec_from_file_location('generated_submit_vo', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        dto = module.ArticleModel.model_validate(request)
        assert remark_to_storage(dto.articleline_list[0].line_notes) == child_document
        assert 'index' not in request['articlelineList'][0]
    finally:
        sys.modules.pop(spec.name, None)
