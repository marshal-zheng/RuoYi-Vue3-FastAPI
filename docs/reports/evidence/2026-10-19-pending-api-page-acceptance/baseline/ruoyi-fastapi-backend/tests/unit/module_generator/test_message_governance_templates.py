from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / 'module_generator' / 'templates'


def _read(relative_path: str) -> str:
    return (TEMPLATES / relative_path).read_text(encoding='utf-8')


def test_python_controller_template_uses_resource_contract():
    content = _read('python/controller.py.jinja2')

    assert 'ResponseUtil.success(' not in content
    assert 'ResponseUtil.ok_list(' not in content
    assert 'ResponseUtil.ok_page(' in content
    assert 'ResponseUtil.ok_collection(' in content
    assert 'ResponseUtil.created_resource(' in content
    assert 'ResponseUtil.no_content()' in content
    assert '.page_num' not in content
    assert '.rows' not in content


def test_js_api_template_declares_feedback():
    content = _read('js/api.js.jinja2')

    assert "feedback: { mode: 'auto', key: '{{ moduleName }}.{{ businessName }}.create' }" in content
    assert "feedback: { mode: 'auto', key: '{{ moduleName }}.{{ businessName }}.update' }" in content
    assert "feedback: { mode: 'auto', key: '{{ moduleName }}.{{ businessName }}.delete' }" in content


def test_vue_templates_consume_items_and_do_not_emit_crud_success_messages():
    for relative_path in [
        'vue/v3/index.vue.jinja2',
        'vue/index.vue.jinja2',
        'vue/v3/index-tree.vue.jinja2',
        'vue/index-tree.vue.jinja2',
    ]:
        content = _read(relative_path)

        assert 'response.rows' not in content
        assert 'pageNum' not in content
        assert '.msgSuccess(' not in content


def test_python_vo_template_uses_page_and_page_size():
    content = _read('python/vo.py.jinja2')

    assert 'page_num:' not in content
    assert 'page: int = Field(default=1' in content
