import { describe, expect, it, vi } from 'vitest';
import { shallowMount } from '@vue/test-utils';
import { ref, type App } from 'vue';
import MenuList from '@/views/system/menu/components/MenuList.vue';
import MenuDrawer from '@/views/system/menu/components/MenuDrawer.vue';
import { listMenu, treeselect } from '@/api/system/menu';
import { handleTree } from '@/utils/ruoyi';

vi.mock('@/api/system/menu', () => ({
  listMenu: vi.fn(),
  treeselect: vi.fn(),
  getMenu: vi.fn(),
  delMenu: vi.fn(),
  addMenu: vi.fn(),
  updateMenu: vi.fn(),
}));
vi.mock('@/components/ui', () => ({ IconSelect: { template: '<div />' } }));

const slotStub = { inheritAttrs: false, template: '<div><slot /></div>' };
const fieldStubs = Object.fromEntries(
  [
    'ZxButton',
    'ZxInput',
    'ElOption',
    'ElSelect',
    'ZxSearch',
    'ElTableColumn',
    'ZxIcon',
    'DictTag',
    'ZxMoreAction',
    'ElTable',
    'ElRadio',
    'ElRadioGroup',
    'SvgIcon',
    'ElIcon',
    'ElPopover',
    'ElInputNumber',
    'ElTooltip',
  ].map((name) => [name, slotStub])
);

describe('menu collection consumers', () => {
  it('builds the list tree from collection items', async () => {
    vi.mocked(listMenu).mockResolvedValue({
      items: [
        { menuId: 1, parentId: 0, menuName: '系统管理' },
        { menuId: 2, parentId: 1, menuName: '菜单管理' },
      ],
    });
    const wrapper = shallowMount(MenuList, {
      global: {
        plugins: [
          {
            install(app: App) {
              app.config.globalProperties.useDict = () => ({
                sys_normal_disable: ref([]),
                sys_show_hide: ref([]),
              });
              app.config.globalProperties.handleTree = handleTree;
            },
          },
        ],
        directives: { hasPermi: () => {}, loading: () => {} },
        stubs: {
          ...fieldStubs,
          ZxGridList: {
            name: 'ZxGridList',
            inheritAttrs: false,
            props: ['loadData'],
            template: '<div />',
          },
        },
      },
    });
    const result = await wrapper.findComponent({ name: 'ZxGridList' }).props('loadData')({
      query: {},
    });
    expect(result.data).toHaveLength(1);
    expect(result.data[0].children[0].menuName).toBe('菜单管理');
    wrapper.unmount();
  });

  it('opens the drawer with array children from the tree collection', async () => {
    vi.mocked(treeselect).mockResolvedValue({
      items: [{ id: 1, label: '系统管理', children: [] }],
    });
    const wrapper = shallowMount(MenuDrawer, {
      props: { sysShowHide: [], sysNormalDisable: [] },
      global: {
        stubs: {
          ...fieldStubs,
          ZxDrawer: slotStub,
          ElForm: slotStub,
          ElFormItem: slotStub,
          ElTreeSelect: {
            name: 'ElTreeSelect',
            inheritAttrs: false,
            props: ['data'],
            template: '<div />',
          },
        },
      },
    });
    await (wrapper.vm as unknown as { open: () => Promise<void> }).open();
    expect(wrapper.findComponent({ name: 'ElTreeSelect' }).props('data')).toEqual([
      { id: 0, label: '主类目', children: [{ id: 1, label: '系统管理', children: [] }] },
    ]);
    wrapper.unmount();
  });
});
