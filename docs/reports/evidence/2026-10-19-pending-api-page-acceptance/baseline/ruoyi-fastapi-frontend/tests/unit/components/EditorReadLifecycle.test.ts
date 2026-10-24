import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { queryClient } from '@/queries/client';
import { roleKeys } from '@/queries/system/role';
import { endQuerySession, setQuerySession } from '@/queries/context';
import {
  defineComponent,
  h,
  nextTick,
  watch,
  type Component,
  type ComponentCustomProperties,
} from 'vue';
import { handleTree } from '@/utils/ruoyi';
import ConfigDlg from '@/views/system/config/components/ConfigDlg.vue';
import DictDlg from '@/views/system/dict/components/DictDlg.vue';
import RoleFormDrawer from '@/views/system/role/components/RoleFormDrawer.vue';
import RoleDataScopeDrawer from '@/views/system/role/components/RoleDataScopeDrawer.vue';

const api = vi.hoisted(() => ({
  config: vi.fn(),
  dict: vi.fn(),
  dept: vi.fn(),
  role: vi.fn(),
  deptList: vi.fn(),
  deptExclude: vi.fn(),
  menu: vi.fn(),
  roleMenu: vi.fn(),
  roleDept: vi.fn(),
  write: vi.fn(),
  feedback: vi.fn(),
  httpFeedback: vi.fn(),
}));
vi.mock('@/api/system/config', () => ({
  getConfig: api.config,
  addConfig: api.write,
  updateConfig: api.write,
}));
vi.mock('@/api/system/dict/type', () => ({
  getType: api.dict,
  addType: api.write,
  updateType: api.write,
}));
vi.mock('@/api/system/dept', () => ({
  getDept: api.dept,
  listDept: api.deptList,
  listDeptExcludeChild: api.deptExclude,
  addDept: api.write,
  updateDept: api.write,
}));
vi.mock('@/api/system/role', () => ({
  getRole: api.role,
  deptTreeSelect: api.roleDept,
  addRole: api.write,
  updateRole: api.write,
  dataScope: api.write,
}));
vi.mock('@/api/system/menu', () => ({
  treeselect: api.menu,
  roleMenuTreeselect: api.roleMenu,
}));
vi.mock('@/utils/http', () => ({ presentRequestError: api.httpFeedback }));
vi.mock('@/utils/dict', () => ({
  useDict: () => ({ sys_yes_no: [], sys_normal_disable: [] }),
}));
vi.mock('element-plus', () => ({ ElMessage: { error: api.feedback } }));
vi.mock('@/utils/feedback/presenter', () => ({
  presentProblemFeedback: api.feedback,
  resolveFeedbackOptions: (value: unknown) => value,
}));

const shell = defineComponent({
  name: 'EditorShell',
  inheritAttrs: false,
  props: ['modelValue', 'formModel', 'confirm', 'okDisabled', 'loading'],
  emits: ['update:modelValue', 'close'],
  setup(_, { emit, expose, slots }) {
    expose({
      close: async () => {
        emit('update:modelValue', false);
        emit('close');
      },
    });
    return () => h('section', slots.default?.());
  },
});
let onTreeData: ((items: { id: number }[]) => void) | undefined;
const tree = defineComponent({
  name: 'EditorTree',
  props: ['data'],
  setup(props, { expose }) {
    let checked: number[] = [];
    const methods = {
      getCheckedKeys: () => checked,
      getHalfCheckedKeys: () => [],
      setCheckedKeys: (keys: number[]) => {
        checked = [...keys];
      },
      setChecked: (id: number) => {
        checked.push(id);
      },
    };
    watch(
      () => props.data,
      (items) => onTreeData?.(items),
      { flush: 'sync' }
    );
    expose(methods);
    return methods;
  },
  render: () => h('div'),
});
const slot = { inheritAttrs: false, template: '<div><slot /></div>' };
const detail = (id: number) => ({
  configId: id,
  configName: `Config ${id}`,
  dictId: id,
  dictName: `Dict ${id}`,
  deptId: id,
  deptName: `Dept ${id}`,
  parentId: 1,
  roleId: id,
  roleName: `Role ${id}`,
  roleKey: `role_${id}`,
  roleSort: id,
  status: '0',
  configType: 'N',
  configKey: `key_${id}`,
  configValue: `value_${id}`,
  dictType: `dict_${id}`,
  dataScope: '2',
  menuCheckStrictly: true,
  deptCheckStrictly: true,
});
function deferred() {
  let resolve!: (value: ReturnType<typeof detail>) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<ReturnType<typeof detail>>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}
const cases = [
  {
    name: 'config',
    component: ConfigDlg,
    read: api.config,
    id: 'configId',
    field: 'configName',
    arg: (id?: number) => id,
  },
  {
    name: 'dict',
    component: DictDlg,
    read: api.dict,
    id: 'dictId',
    field: 'dictName',
    arg: (id?: number) => id,
  },
  {
    name: 'role',
    component: RoleFormDrawer,
    read: api.role,
    id: 'roleId',
    field: 'roleName',
    arg: (id?: number) => id,
  },
  {
    name: 'scope',
    component: RoleDataScopeDrawer,
    read: api.role,
    id: 'roleId',
    field: 'roleName',
    arg: (id?: number) => id,
  },
];
const mounted: ReturnType<typeof mount>[] = [];

function editor(component: Component) {
  const wrapper = mount(component, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      config: { globalProperties: { handleTree } as ComponentCustomProperties },
      stubs: {
        DictStatus: true,
        DictSelect: true,
        ZxDialog: shell,
        ZxDrawer: shell,
        ElForm: slot,
        ElFormItem: slot,
        FormGrid: slot,
        ElTree: tree,
        ElAlert: { props: ['title'], template: '<aside><slot /></aside>' },
        ElButton: { template: '<button><slot /></button>' },
        ZxInput: true,
        ElSelect: slot,
        ElOption: true,
        ElTreeSelect: true,
        ElRadioGroup: slot,
        ElRadio: true,
        ElCheckbox: true,
        ElInputNumber: true,
        ElTooltip: slot,
        ElIcon: slot,
        QuestionFilled: true,
      },
    },
  });
  mounted.push(wrapper);
  const exposed = wrapper.vm as unknown as {
    open: (id?: unknown) => Promise<void>;
    close: () => Promise<void>;
  };
  const modal = () => wrapper.findComponent(shell);
  return {
    wrapper,
    exposed,
    modal,
    model: () => modal().props('formModel') as Record<string, unknown>,
  };
}
const outcome = <T>(task: Promise<T>) =>
  task.then(
    (value) => ({ value }),
    (error) => ({ error })
  );
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  setQuerySession(1, [], []);
  vi.resetAllMocks();
  onTreeData = undefined;
  [api.config, api.dict, api.dept, api.role].forEach((read) =>
    read.mockImplementation(async (id) => detail(id))
  );
  api.deptList.mockResolvedValue({ items: [{ deptId: 1, deptName: 'Root' }] });
  api.deptExclude.mockImplementation(async (id) => ({
    items: [{ deptId: id + 100, deptName: 'Parent' }],
  }));
  api.menu.mockResolvedValue({ items: [{ id: 100, label: 'Menu' }] });
  api.roleMenu.mockImplementation(async (id) => ({
    menus: [{ id, label: 'Menu' }],
    checkedKeys: [id],
  }));
  api.roleDept.mockImplementation(async (id) => ({
    depts: [{ id, label: 'Dept' }],
    checkedKeys: [id],
  }));
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  queryClient.clear();
  endQuerySession();
});

it('closes an open dictionary editor when its authorization scope changes', async () => {
  setQuerySession(1, ['admin'], ['dict:write']);
  const e = editor(DictDlg);
  await e.exposed.open(11);
  expect(e.modal().props('modelValue')).toBe(true);

  setQuerySession(2, ['admin'], ['dict:write']);
  await nextTick();
  expect(e.modal().props('modelValue')).toBe(false);
});

it('rejects an old dictionary confirm callback after switching authorization scope', async () => {
  setQuerySession(1, ['admin'], ['dict:write']);
  const e = editor(DictDlg);
  await e.exposed.open(11);
  const confirm = e.modal().props('confirm');

  setQuerySession(2, ['admin'], ['dict:write']);
  await nextTick();
  expect(await confirm({})).toBe(false);
  expect(api.write).not.toHaveBeenCalled();
});

for (const item of cases)
  describe(`${item.name} editor read lifecycle`, () => {
    it('keeps the last selected record when older success arrives last', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item.component),
        first = e.exposed.open(item.arg(11));
      await nextTick();
      expect(e.modal().props('modelValue')).toBe(true);
      expect(e.modal().props('loading')).toBe(true);
      expect(await e.modal().props('confirm')({})).toBe(false);
      expect(api.write).not.toHaveBeenCalled();
      const second = e.exposed.open(item.arg(22));
      // Native observers release the previous key on the Vue update.
      await nextTick();
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      b.resolve(detail(22));
      await second;
      a.resolve(detail(11));
      await first;
      await nextTick();
      expect(e.model()[item.id]).toBe(22);
      expect(e.model()[item.field]).toBe(detail(22)[item.field as keyof ReturnType<typeof detail>]);
      expect(e.modal().props('loading')).toBe(false);
      expect(e.modal().props('okDisabled')).toBe(false);
      if (item.name === 'role' || item.name === 'scope')
        expect(
          (
            e.wrapper.findComponent(tree).vm as unknown as {
              getCheckedKeys: () => number[];
            }
          ).getCheckedKeys()
        ).toEqual([22]);
    });
    it('ignores an old failure and its finally while the next read is pending', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item.component),
        old = outcome(e.exposed.open(item.arg(11))),
        current = e.exposed.open(item.arg(22));
      a.reject(new Error('old failure'));
      await old;
      await nextTick();
      expect(e.modal().props('loading')).toBe(true);
      expect(e.modal().props('okDisabled')).toBe(true);
      expect(api.feedback).not.toHaveBeenCalled();
      b.resolve(detail(22));
      await current;
    });
    it('cancels on UI close and keeps a reopened read busy after old success', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item.component),
        old = e.exposed.open(item.arg(11));
      await nextTick();
      e.modal().vm.$emit('update:modelValue', false);
      await nextTick();
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      const current = e.exposed.open(item.arg(11));
      a.resolve(detail(11));
      await old;
      await nextTick();
      expect(e.modal().props('loading')).toBe(true);
      expect(e.model()[item.field]).toBeFalsy();
      b.resolve({ ...detail(11), [item.field]: 'Reopened' });
      await current;
      expect(e.model()[item.field]).toBe('Reopened');
    });
    if (item.name !== 'scope')
      it('keeps a new draft when a previous edit finishes', async () => {
        const a = deferred();
        item.read.mockReturnValueOnce(a.promise);
        const e = editor(item.component),
          old = e.exposed.open(item.arg(11));
        await e.exposed.open(item.arg());
        a.resolve(detail(11));
        await old;
        expect(e.model()[item.id]).toBeUndefined();
        expect(e.model()[item.field]).toBeFalsy();
        expect(e.modal().props('okDisabled')).toBe(false);
      });
    it('retains the current failure, blocks writes and permits retry', async () => {
      const error = new Error('current read failed');
      item.read.mockRejectedValueOnce(error);
      const e = editor(item.component);
      expect(await outcome(e.exposed.open(item.arg(11)))).toEqual({ error });
      await nextTick();
      expect(e.modal().props('modelValue')).toBe(true);
      expect(e.modal().props('loading')).toBe(false);
      expect(e.modal().props('okDisabled')).toBe(true);
      expect(await e.modal().props('confirm')({})).toBe(false);
      expect(api.write).not.toHaveBeenCalled();
      expect(api.feedback).not.toHaveBeenCalled();
      const retry = e.wrapper.findAll('button').find((button) => button.text() === '重试');
      expect(retry).toBeDefined();
      await retry!.trigger('click');
      await flushPromises();
      expect(e.model()[item.id]).toBe(11);
      expect(e.modal().props('okDisabled')).toBe(false);
    });
    it('aborts on unmount and ignores a non-cooperating response', async () => {
      const a = deferred();
      item.read.mockReturnValueOnce(a.promise);
      const e = editor(item.component),
        old = e.exposed.open(item.arg(11));
      await nextTick();
      e.wrapper.unmount();
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      a.resolve(detail(11));
      await old;
      expect(api.feedback).not.toHaveBeenCalled();
    });
  });

for (const item of cases.filter((item) => item.name === 'role' || item.name === 'scope')) {
  it(`${item.name} ignores old tree work when reopened during nextTick`, async () => {
    const a = deferred(),
      b = deferred();
    item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
    const e = editor(item.component);
    let second: Promise<void> | undefined;
    onTreeData = (items) => {
      if (items[0]?.id === 11) {
        onTreeData = undefined;
        second = e.exposed.open(item.arg(22));
      }
    };
    const first = e.exposed.open(item.arg(11));
    a.resolve(detail(11));
    await first;
    await nextTick();
    expect(second).toBeDefined();
    const treeApi = e.wrapper.findComponent(tree).vm as unknown as {
      getCheckedKeys: () => number[];
    };
    expect(treeApi.getCheckedKeys()).toEqual([]);
    expect(e.modal().props('loading')).toBe(true);
    b.resolve(detail(22));
    await second;
    expect(treeApi.getCheckedKeys()).toEqual([22]);
  });
}

it('presents the current 401 through the existing HTTP recovery policy and keeps a stale 401 silent', async () => {
  const old = deferred(),
    current = deferred();
  api.config.mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise);
  const e = editor(ConfigDlg);
  const first = outcome(e.exposed.open(11)),
    second = outcome(e.exposed.open(22));
  const expired = Object.assign(new Error('session expired'), {
    problem: { status: 401 },
    meta: { status: 401 },
    config: { silentError: true },
  });
  old.reject(expired);
  await first;
  expect(api.httpFeedback).not.toHaveBeenCalled();
  current.reject(expired);
  await second;
  expect(api.httpFeedback).toHaveBeenCalledExactlyOnceWith(
    expired,
    expect.objectContaining({ silentError: false, feedback: { mode: 'auto' } })
  );
  expect(expired.config.silentError).toBe(true);
});

for (const item of cases.filter((item) => item.name === 'role' || item.name === 'scope')) {
  it(`${item.name} sends operation fields without response-only metadata`, async () => {
    const e = editor(item.component);
    await e.exposed.open(item.arg(11));
    Object.assign(e.model(), {
      createBy: 'response-only',
      delFlag: '2',
      type: 'status',
      admin: true,
    });
    await e.modal().props('confirm')(e.model());
    const payload = api.write.mock.calls[0][0];
    expect(payload.roleId).toBe(11);
    for (const field of ['createBy', 'delFlag', 'type', 'admin'])
      expect(payload).not.toHaveProperty(field);
    if (item.name === 'scope') {
      expect(Object.keys(payload).sort()).toEqual([
        'dataScope',
        'deptCheckStrictly',
        'deptIds',
        'roleId',
      ]);
      expect(payload.deptIds).toEqual([11]);
    } else {
      expect(payload.roleName).toBe('Role 11');
      expect(payload.menuIds).toEqual([11]);
    }
  });
}

for (const item of cases.filter((item) => item.name === 'role' || item.name === 'scope')) {
  it(`${item.name} closes and refuses an old confirm after the authorization scope changes`, async () => {
    const e = editor(item.component);
    await e.exposed.open(11);
    const confirm = e.modal().props('confirm');
    setQuerySession(2, [], []);
    await nextTick();
    expect(e.modal().props('modelValue')).toBe(false);
    expect(await confirm(e.model())).toBe(false);
    expect(api.write).not.toHaveBeenCalled();
  });

  it(`${item.name} refreshes its query resources without replacing draft fields or tree selection`, async () => {
    const scope = setQuerySession(1, [], []);
    const e = editor(item.component);
    await e.exposed.open(11);
    e.model().roleName = 'Unsaved draft';
    const selected = e.wrapper.findComponent(tree).vm as unknown as {
      setCheckedKeys: (keys: number[]) => void;
      getCheckedKeys: () => number[];
    };
    selected.setCheckedKeys([99]);
    api.role.mockResolvedValue({ ...detail(11), roleName: 'Refreshed role' });
    await queryClient.invalidateQueries({ queryKey: roleKeys.all(scope) });
    await flushPromises();
    expect(api.role).toHaveBeenCalledTimes(2);
    expect(e.model().roleName).toBe('Unsaved draft');
    expect(selected.getCheckedKeys()).toEqual([99]);
  });

  it(`${item.name} keeps a reopened editor when the previous write finishes`, async () => {
    const e = editor(item.component);
    await e.exposed.open(11);
    let complete!: () => void;
    api.write.mockReturnValue(
      new Promise<void>((resolve) => {
        complete = resolve;
      })
    );
    const saving = e.modal().props('confirm')(e.model());
    await e.exposed.open(22);
    complete();
    expect(await saving).toBe(false);
    expect(e.modal().props('modelValue')).toBe(true);
    expect(e.model().roleId).toBe(22);
    expect(e.wrapper.emitted('success')).toBeUndefined();
  });
}
