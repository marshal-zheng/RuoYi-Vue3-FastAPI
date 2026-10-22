import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { mockRemark } from '@/mocks/data/remark';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { defineComponent, h, nextTick } from 'vue';
import { ElTree, ElMessageBox } from 'element-plus';
import RoleFormDrawer from '@/views/system/role/components/RoleFormDrawer.vue';
import { getRole } from '@/api/system/role';
import { roleMenuTreeselect, treeselect } from '@/api/system/menu';
import type { MenuTreeNode } from '@/api/system/menu';
import type { HttpCollection } from '@/types/http-contract';

vi.mock('@/api/system/role', () => ({
  addRole: vi.fn(),
  getRole: vi.fn(),
  updateRole: vi.fn(),
}));
vi.mock('@/api/system/menu', () => ({
  roleMenuTreeselect: vi.fn(),
  treeselect: vi.fn(),
}));

const slotStub = { inheritAttrs: false, template: '<div><slot /></div>' };
const menuItems: MenuTreeNode[] = [
  { id: 1, label: '系统管理', children: [{ id: 2, label: '用户管理' }] },
];

function mountDrawer() {
  return mount(RoleFormDrawer, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      components: { ElTree },
      stubs: {
        DictStatus: true,
        ZxDrawer: defineComponent({
          name: 'ZxDrawer',
          inheritAttrs: false,
          props: ['modelValue', 'formModel', 'loading', 'okDisabled'],
          emits: ['update:modelValue', 'close'],
          setup(_, { emit, expose, slots }) {
            expose({
              close: () => {
                emit('update:modelValue', false);
                emit('close');
              },
            });
            return () => h('div', slots.default?.());
          },
        }),
        ElAlert: slotStub,
        ElButton: slotStub,
        ElForm: slotStub,
        ElFormItem: slotStub,
        ElTree: false,
        ElCheckbox: true,
        ElIcon: true,
        ElInputNumber: true,
        ElRadio: true,
        ElRadioGroup: true,
        ElTooltip: true,
        QuestionFilled: true,
        ZxInput: true,
      },
    },
  });
}

type DrawerWrapper = ReturnType<typeof mountDrawer>;
const wrappers: DrawerWrapper[] = [];

function createDrawer() {
  const wrapper = mountDrawer();
  wrappers.push(wrapper);
  const open = (roleId?: number) =>
    (wrapper.vm as unknown as { open: (roleId?: number) => Promise<void> }).open(roleId);
  const tree = () => wrapper.findComponent({ name: 'ElTree' });
  const drawer = () => wrapper.findComponent({ name: 'ZxDrawer' });
  return { open, tree, drawer };
}

beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  setQuerySession(1, [], []);
});

afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

describe('RoleFormDrawer menu loading', () => {
  it('uses collection items as the menu tree when adding a role', async () => {
    vi.mocked(treeselect).mockResolvedValue({ items: menuItems });
    const { open, tree } = createDrawer();

    await open();

    expect(tree().props('data')).toEqual(menuItems);
    expect(tree().text()).toContain('系统管理');
  });

  it('shows loading only while the menu request is pending', async () => {
    let resolveMenus!: (result: HttpCollection<MenuTreeNode>) => void;
    vi.mocked(treeselect).mockReturnValue(
      new Promise((resolve) => {
        resolveMenus = resolve;
      })
    );
    const { open, tree, drawer } = createDrawer();

    const opening = open();
    await nextTick();
    expect(drawer().props('loading')).toBe(true);
    expect(drawer().props('okDisabled')).toBe(true);
    expect(tree().props('emptyText')).toBe('加载中，请稍候');

    resolveMenus({ items: menuItems });
    await opening;
    await nextTick();
    expect(drawer().props('loading')).toBe(false);
    expect(drawer().props('okDisabled')).toBe(false);
    expect(tree().props('data')).toEqual(menuItems);
  });

  it('shows an empty state after loading an empty menu collection', async () => {
    vi.mocked(treeselect).mockResolvedValue({ items: [] });
    const { open, tree, drawer } = createDrawer();

    await open();

    expect(drawer().props('loading')).toBe(false);
    expect(tree().props('data')).toEqual([]);
    expect(tree().props('emptyText')).toBe('暂无菜单数据');
    expect(tree().text()).toBe('暂无菜单数据');
  });

  it('shows a failure state and allows reopening to retry', async () => {
    vi.mocked(treeselect).mockRejectedValueOnce(new Error('菜单请求失败'));
    const { open, tree, drawer } = createDrawer();

    await expect(open()).rejects.toThrow('菜单请求失败');
    await nextTick();
    expect(drawer().props('loading')).toBe(false);
    expect(drawer().props('okDisabled')).toBe(true);
    expect(tree().props('emptyText')).toBe('菜单加载失败，请关闭后重试');
    expect(tree().text()).toBe('菜单加载失败，请关闭后重试');

    vi.mocked(treeselect).mockResolvedValueOnce({ items: menuItems });
    await open();
    expect(drawer().props('okDisabled')).toBe(false);
    expect(tree().props('data')).toEqual(menuItems);
    expect(tree().props('emptyText')).toBe('暂无菜单数据');
  });

  it('preserves the role-specific menu response when editing a role', async () => {
    vi.mocked(getRole).mockResolvedValue({
      remarkText: '',
      roleId: 2,
      roleName: '测试角色',
      roleKey: 'test',
      roleSort: 1,
      status: '0',
      menuCheckStrictly: true,
    });
    vi.mocked(roleMenuTreeselect).mockResolvedValue({
      menus: menuItems,
      checkedKeys: [2],
    });
    const { open, tree, drawer } = createDrawer();

    await open(2);
    await nextTick();
    await nextTick();

    expect(tree().props('data')).toEqual(menuItems);
    expect((tree().vm as InstanceType<typeof ElTree>).getCheckedKeys()).toEqual([1, 2]);
    expect(drawer().props('loading')).toBe(false);
    expect(treeselect).not.toHaveBeenCalled();
  });
});

it('keeps a format-only role remark when close or another record is declined', async () => {
  const confirm = vi.spyOn(ElMessageBox, 'confirm').mockRejectedValue(new Error('继续编辑'));
  try {
    const original = mockRemark('same text', 'roleguard')!;
    vi.mocked(getRole).mockResolvedValue({
      roleId: 2,
      roleName: 'Role',
      roleKey: 'role',
      roleSort: 1,
      status: '0',
      remark: original,
      remarkText: 'same text',
    });
    vi.mocked(roleMenuTreeselect).mockResolvedValue({
      menus: [],
      checkedKeys: [],
    });
    const wrapper = mountDrawer();
    wrappers.push(wrapper);
    const api = wrapper.vm as unknown as {
      open: (id?: number) => Promise<void>;
      close: () => Promise<void>;
    };
    await api.open(2);
    const formatted = structuredClone(original);
    const text = formatted.body.content.content[0].content![0];
    if (text.type !== 'text') throw new Error('Expected text fixture');
    text.marks = [{ type: 'italic' }];
    wrapper.findComponent(RemarkEditor).vm.$emit('update:modelValue', formatted);
    await nextTick();
    await api.close();
    expect(wrapper.findComponent(RemarkEditor).props('modelValue')).toEqual(formatted);
    await api.open(3);
    expect(vi.mocked(getRole)).toHaveBeenCalledTimes(1);
    expect(confirm).toHaveBeenCalledTimes(2);
    confirm.mockResolvedValue(
      Object.assign('confirm' as const, { value: '', action: 'confirm' as const })
    );
    await api.close();
    expect(wrapper.findComponent(RemarkEditor).exists()).toBe(false);
  } finally {
    confirm.mockRestore();
  }
});
