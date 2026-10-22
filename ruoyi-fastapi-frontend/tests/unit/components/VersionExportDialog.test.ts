import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { ElForm, ElFormItem } from 'element-plus';
import VersionExportDialog from '@/views/project/components/VersionExportDialog.vue';

const api = vi.hoisted(() => ({ word: vi.fn(), excel: vi.fn(), xml: vi.fn() }));
vi.mock('@/api/project/version', () => ({
  exportProjectVersion: api.word,
  exportProjectVersionExcel: api.excel,
  exportProjectVersionXml: api.xml,
}));
vi.mock('@/views/project/composables/topoExportUtils', () => ({
  exportTopologyAsImage: vi.fn(),
}));
const dialog = defineComponent({
  props: ['modelValue', 'formRef', 'formModel', 'confirm'],
  template: '<section v-if="modelValue"><slot /><button @click="save">export</button></section>',
  setup(props) {
    return {
      async save() {
        if ((await props.formRef.validate()) !== false) await props.confirm(props.formModel);
      },
    };
  },
});
let wrapper: ReturnType<typeof mount>;
afterEach(() => {
  wrapper?.unmount();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
describe('version export form validation', () => {
  it('passes native ElForm validation and downloads the selected version', async () => {
    api.xml.mockResolvedValue(new Blob(['<version />']));
    vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:qa'), revokeObjectURL: vi.fn() });
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    wrapper = mount(VersionExportDialog, {
      global: {
        components: { ElForm, ElFormItem },
        stubs: { ZxDialog: dialog, FileTypeSelector: true, ElIcon: true },
      },
    });
    await (wrapper.vm as unknown as { open: (row: object, format: string) => void }).open(
      { projectId: 14, versionId: 15, versionName: 'QA clone' },
      'xml'
    );
    await wrapper.get('button').trigger('click');
    await flushPromises();
    expect(api.xml).toHaveBeenCalledWith(15);
    expect(click).toHaveBeenCalledOnce();
  });
});
