import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, reactive, type App } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import type { ZxGridListRequestInstance } from '@zxio/zxui';
import ConfigList from '@/views/system/config/components/ConfigList.vue';
import { listConfig } from '@/api/system/config';
import { handleTree } from '@/utils/ruoyi';

vi.mock('@/api/system/config', () => ({
  listConfig: vi.fn(),
  getConfig: vi.fn(),
  delConfig: vi.fn(),
  refreshCache: vi.fn(),
}));

const slotStub = { template: '<div><slot /><slot name="filters" /></div>' };
const selectStub = { name: 'FilterSelect', template: '<button />' };

function globalOptions(
  draft: Record<string, unknown>,
  search: ZxGridListRequestInstance['search']
) {
  return {
    plugins: [
      {
        install(app: App) {
          app.config.globalProperties.useDict = () => ({});
          app.config.globalProperties.handleTree = handleTree;
        },
      },
    ],
    directives: { hasPermi: () => {}, loading: () => {} },
    stubs: {
      ZxGridList: defineComponent({
        name: 'ZxGridList',
        props: ['loadData'],
        setup(_props, { slots }) {
          return () => h('div', slots.form?.({ mode: 'request', draft, loading: false, search }));
        },
      }),
      ZxListToolbar: slotStub,
      DictStatus: true,
      DictSelect: selectStub,
      ElSelect: selectStub,
      ElDatePicker: selectStub,
      ZxButton: true,
      ZxInput: true,
      ZxSearch: true,
      ConfigDlg: true,
      DeptDlg: true,
      ElOption: true,
      ElTable: true,
      ElTableColumn: true,
      DictTag: true,
      ElButton: true,
      ZxMoreAction: true,
    },
  };
}

describe('GridList public query contract', () => {
  it.each([{ component: ConfigList, field: 'configType', value: 'N' }])(
    'writes draft.$field before applying a filter',
    async ({ component, field, value }) => {
      const draft = reactive<Record<string, unknown>>({});
      const search = vi.fn<ZxGridListRequestInstance['search']>(() => {
        expect(draft[field]).toBe(value);
        return Promise.resolve({ kind: 'not-started', reason: 'test' });
      });
      const wrapper = mount(component, {
        global: globalOptions(draft, search),
      });
      wrapper.findComponent({ name: 'FilterSelect' }).vm.$emit('update:modelValue', value);
      wrapper.findComponent({ name: 'FilterSelect' }).vm.$emit('change', value);
      await flushPromises();
      expect(search).toHaveBeenCalledOnce();
      wrapper.unmount();
    }
  );

  it('maps the public grid query and pager to flat HTTP parameters', async () => {
    vi.mocked(listConfig).mockResolvedValue({
      items: [],
      total: 0,
      page: 3,
      pageSize: 20,
    });
    const wrapper = mount(ConfigList, {
      global: globalOptions({}, vi.fn()),
    });
    await wrapper.findComponent({ name: 'ZxGridList' }).props('loadData')({
      query: { configName: 'database', configType: 'N' },
      pager: { page: 3, size: 20 },
      sort: [{ field: 'createTime', order: 'desc' }],
    });
    expect(listConfig).toHaveBeenCalledWith({
      configName: 'database',
      configType: 'N',
      page: 3,
      pageSize: 20,
      sort: [{ field: 'createTime', order: 'desc' }],
    });
    wrapper.unmount();
  });
});
