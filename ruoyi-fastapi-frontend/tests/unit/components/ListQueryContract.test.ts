import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, type App } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import type { ZxGridListInstance } from '@zxio/zxui';
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
  updateState: ZxGridListInstance['updateState'],
  refresh: ZxGridListInstance['refresh']
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
          return () => h('div', slots.form?.({ query: {}, loading: false, updateState, refresh }));
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
    'updates query.$field before refreshing a filter',
    async ({ component, field, value }) => {
      const updateState = vi.fn<ZxGridListInstance['updateState']>();
      const refresh = vi.fn<ZxGridListInstance['refresh']>().mockResolvedValue();
      const wrapper = mount(component, {
        global: globalOptions(updateState, refresh),
      });
      wrapper.findComponent({ name: 'FilterSelect' }).vm.$emit('change', value);
      await flushPromises();
      expect(updateState).toHaveBeenCalledWith(`query.${field}`, value);
      expect(refresh).toHaveBeenCalledOnce();
      expect(updateState.mock.invocationCallOrder[0]).toBeLessThan(
        refresh.mock.invocationCallOrder[0]
      );
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
      global: globalOptions(vi.fn(), vi.fn()),
    });
    await wrapper.findComponent({ name: 'ZxGridList' }).props('loadData')({
      query: { configName: 'database', configType: 'N' },
      pager: { page: 3, size: 20, total: 0 },
    });
    expect(listConfig).toHaveBeenCalledWith({
      configName: 'database',
      configType: 'N',
      page: 3,
      pageSize: 20,
    });
    wrapper.unmount();
  });
});
