import json

import pytest

from module_generator.entity.vo.gen_vo import GenTableColumnModel, GenTableModel
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
