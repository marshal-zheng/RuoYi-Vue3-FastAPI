/**
 * Unit tests for UserFormDialog component
 */
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { isAbortError } from '@zxio/http';
import type { SchemaFormInstance } from '@zxio/schema-form/formily';
import { ZxSelect } from '@zxio/zxui/select';
import { useAIContextScope, type AIContextScopeRuntime } from '@zxio/zxui/ai-context';
import { createFieldThemeTestHost } from '../../helpers/theme-field-public';
import type { UserValues } from '@/views/system/user/components/user-form';
import { ElOption, ElSelect, ElTreeSelect, ElMessageBox } from 'element-plus';
import { defineComponent, h, nextTick, ref, proxyRefs } from 'vue';
import { addUser, deptTreeSelect, getUser, updateUser, listUser } from '@/api/system/user';
import { updateDept } from '@/api/system/dept';
import UserFormDialog from '@/views/system/user/components/UserFormDialog.vue';
import { mockRemark } from '@/mocks/data/remark';
import { readRemark } from '@/components/ui/Remark/contract';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import {
  captureUserCommand,
  userCommands,
  userDetailOptions,
  userListOptions,
} from '@/queries/system/user';
import {
  captureDeptCommand,
  deptCommands,
  deptKeys,
  userDeptTreeOptions,
} from '@/queries/system/dept';

vi.mock('@/api/system/user', () => ({
  getUser: vi.fn(),
  addUser: vi.fn(),
  updateUser: vi.fn(),
  deptTreeSelect: vi.fn(),
  listUser: vi.fn(),
}));
vi.mock('@/api/system/dept', () => ({
  listDept: vi.fn(),
  listDeptExcludeChild: vi.fn(),
  getDept: vi.fn(),
  addDept: vi.fn(),
  updateDept: vi.fn(),
  delDept: vi.fn(),
}));
vi.mock('@/utils/dict', () => ({
  useDict: () => ({ sys_normal_disable: ref([]) }),
}));

const feedback = vi.hoisted(() => ({
  error: vi.fn(),
  problem: vi.fn(),
  recovery: vi.fn(),
}));
vi.mock('@/utils/http', () => ({ presentRequestError: feedback.recovery }));
vi.mock('element-plus', async (importOriginal) => ({
  ...(await importOriginal<typeof import('element-plus')>()),
  ElMessage: { error: feedback.error },
}));
vi.mock('@/utils/feedback/presenter', () => ({
  presentProblemFeedback: feedback.problem,
  resolveFeedbackOptions: (options: unknown) => options,
}));

const dialogStub = defineComponent({
  name: 'ZxDialog',
  inheritAttrs: false,
  props: ['confirm', 'okLoading', 'okDisabled', 'loading', 'modelValue', 'handleBeforeCancel'],
  emits: ['update:modelValue', 'close'],
  setup(_, { slots, emit, expose }) {
    expose({
      close: () => {
        emit('update:modelValue', false);
        emit('close');
      },
    });
    return () => h('div', slots.default?.());
  },
});

type DialogApi = {
  open: (id?: number) => Promise<void>;
  close: () => Promise<void>;
};
type UserDetail = Awaited<ReturnType<typeof getUser>>;
function deferred() {
  let resolve!: (value: UserDetail) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<UserDetail>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}
const detail = (id: number) =>
  ({
    data: {
      remarkText: '',
      userId: id,
      userName: `user_${id}`,
      nickName: `User ${id}`,
      status: '0',
    },
    postIds: [id],
    roleIds: [id],
    posts: [],
    roles: [],
  }) satisfies UserDetail;
const outcome = <T>(promise: Promise<T>) =>
  promise.then(
    (value) => ({ value }),
    (error) => ({ error })
  );
function contextValue(scope: AIContextScopeRuntime, id: string) {
  const value = scope.binding(id)?.value;
  return typeof value === 'function' ? value() : value;
}
function formOf(wrapper: ReturnType<typeof mount>) {
  return proxyRefs(
    wrapper.getComponent({ name: 'ZxSchemaForm' }).vm.$.exposed!
  ) as unknown as SchemaFormInstance<UserValues>;
}
/** Test conveniences only; every edit passes through the owner's public setValues. */
function draftOf(wrapper: ReturnType<typeof mount>): UserValues {
  const form = formOf(wrapper);
  return new Proxy({} as UserValues, {
    get: (_, key) => Reflect.get(form.read(), key),
    set: (_, key, value) => {
      form.setValues({ ...form.read(), [key]: value });
      return true;
    },
    ownKeys: () => Reflect.ownKeys(form.read()),
    getOwnPropertyDescriptor: () => ({ configurable: true, enumerable: true }),
  });
}
let fieldTheme: Awaited<ReturnType<typeof createFieldThemeTestHost>>;
const aiScopes: AIContextScopeRuntime[] = [];
const mounted: ReturnType<typeof mount>[] = [];
const editorHosts: ReturnType<typeof createRemarkFieldTestHost>[] = [];

const renderSlotStub = {
  inheritAttrs: false,
  template: '<div><slot /></div>',
};

const formStub = {
  name: 'ElForm',
  inheritAttrs: false,
  template: '<form><slot /></form>',
};

function mountDialog(nativeTree = false) {
  const editorHost = createRemarkFieldTestHost('user-form-dialog-test');
  editorHost.attach();
  editorHosts.push(editorHost);
  const editorGlobal = editorHost.global;
  const wrapper = mount(UserFormDialog, {
    attachTo: fieldTheme.root,
    global: {
      ...editorGlobal,
      provide: { ...editorGlobal.provide, ...fieldTheme.provide },
      plugins: [...editorGlobal.plugins, [VueQueryPlugin, { queryClient }]],
      components: { ElTreeSelect, ElSelect, ElOption, ZxSelect },
      stubs: {
        DictStatus: defineComponent({
          setup() {
            aiScopes.push(useAIContextScope()!);
            return () => h('div');
          },
        }),
        DictSelect: true,
        ZxDialog: dialogStub,
        ElForm: formStub,
        ElFormItem: renderSlotStub,
        ElRow: renderSlotStub,
        ElCol: renderSlotStub,
        ElTreeSelect: nativeTree
          ? false
          : {
              name: 'ElTreeSelect',
              props: ['data', 'modelValue', 'cacheData'],
              inheritAttrs: false,
              template: '<select />',
            },
        ElSelect: nativeTree ? false : renderSlotStub,
        ElOption: nativeTree ? false : true,
        ElRadioGroup: renderSlotStub,
        ElRadio: renderSlotStub,
        ElAlert: {
          props: ['title'],
          template: '<aside>{{ title }}<slot /></aside>',
        },
        ElButton: { template: '<button><slot /></button>' },
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}

beforeEach(async () => {
  fieldTheme = await createFieldThemeTestHost();
  aiScopes.length = 0;
  queryClient.clear();
  setQuerySession(1, [], []);
  onlineManager.setOnline(true);
  vi.mocked(getUser)
    .mockReset()
    .mockImplementation(async (id) =>
      id === undefined ? { posts: [], roles: [] } : detail(Number(id))
    );
  vi.mocked(listUser)
    .mockReset()
    .mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 100 });
  vi.mocked(updateUser)
    .mockReset()
    .mockImplementation(async (input) => ({
      ...detail(input.userId!),
      data: {
        ...detail(input.userId!).data,
        nickName: input.nickName ?? '',
        status: input.status ?? '0',
        remark: input.remark ?? null,
      },
    }));
  vi.mocked(addUser)
    .mockReset()
    .mockImplementation(async (input) => ({
      ...detail(99),
      data: {
        ...detail(99).data,
        nickName: input.nickName,
        userName: input.userName,
        status: input.status ?? '0',
        remark: input.remark ?? null,
      },
    }));
  vi.mocked(deptTreeSelect).mockResolvedValue({
    items: [{ id: 1, label: '研发部' }],
  });
});
afterEach(async () => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  editorHosts.splice(0).forEach((host) => host.dispose());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
  vi.clearAllMocks();
  await fieldTheme.dispose();
});

describe('UserFormDialog', () => {
  it('starts the native department selector without a null cache node', () => {
    expect(() => mountDialog(true)).not.toThrow();
  });

  it('updates the native collapsed department label after an asynchronous edit and keeps keyboard selection', async () => {
    const scope = setQuerySession(1, [], []);
    const response = deferred();
    vi.mocked(getUser).mockReturnValueOnce(response.promise);
    vi.mocked(deptTreeSelect).mockResolvedValueOnce({
      items: [{ id: 1, label: 'Root', children: [{ id: 9, label: '原部门' }] }],
    });
    const wrapper = mountDialog(true);
    const opening = (wrapper.vm as unknown as DialogApi).open(42);
    await flushPromises();
    expect(wrapper.findComponent({ name: 'ZxSchemaForm' }).exists()).toBe(false);
    expect(document.querySelector('.el-tree-node[data-key="9"]')).toBeNull();
    response.resolve({
      ...detail(42),
      data: {
        ...detail(42).data,
        deptId: 9,
        dept: { deptId: 9, deptName: '原部门' },
      },
    });
    await opening;
    await flushPromises();
    const tree = wrapper.getComponent(ElTreeSelect);
    const element = tree.element;
    const selectedLabel = () => tree.get('.el-select__selected-item.el-select__placeholder').text();
    expect(selectedLabel()).toBe('原部门');
    const model = draftOf(wrapper);
    model.nickName = '尚未保存的输入';
    vi.mocked(deptTreeSelect).mockResolvedValueOnce({
      items: [{ id: 1, label: 'Root', children: [{ id: 9, label: '新部门' }] }],
    });
    await queryClient.invalidateQueries({ queryKey: deptKeys.userTree(scope) });
    await flushPromises();
    expect(tree.props('data')).toEqual([
      { id: 1, label: 'Root', children: [{ id: 9, label: '新部门' }] },
    ]);
    expect(tree.props('cacheData')).toEqual([{ id: 9, label: '新部门' }]);
    expect(tree.element).toBe(element);
    expect(selectedLabel()).toBe('新部门');
    expect(model.nickName).toBe('尚未保存的输入');
    vi.mocked(deptTreeSelect).mockRejectedValueOnce(new Error('部门刷新失败'));
    await queryClient.invalidateQueries({ queryKey: deptKeys.userTree(scope) });
    await flushPromises();
    expect(wrapper.text()).toContain('部门列表刷新失败');
    expect(selectedLabel()).toBe('新部门');
    expect(model.deptId).toBe(9);
    expect(model.nickName).toBe('尚未保存的输入');

    const input = tree.get('input');
    input.element.focus();
    await input.trigger('keydown', { key: 'Enter', code: 'Enter' });
    await flushPromises();
    expect(input.attributes('aria-expanded')).toBe('true');
    const popupId = input.attributes('aria-controls');
    expect(popupId).toBeDefined();
    const popup = document.getElementById(popupId!)!;
    const root = popup.querySelector('.el-tree-node[data-key="1"]')!;
    root
      .querySelector('.el-tree-node__expand-icon')!
      .dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await flushPromises();
    expect(popup.querySelector('.el-tree-node[data-key="9"] .is-selected')).not.toBeNull();
    await input.trigger('keydown', { key: 'ArrowDown', code: 'ArrowDown' });
    await new Promise((resolve) => setTimeout(resolve, 30));
    await input.trigger('keydown', { key: 'Enter', code: 'Enter' });
    await flushPromises();
    expect(model.deptId).toBe(1);
    expect(selectedLabel()).toBe('Root');
  });

  it('shows the current disabled department label from detail when choices omit the value', async () => {
    vi.mocked(deptTreeSelect).mockResolvedValue({ items: [] });
    vi.mocked(getUser)
      .mockResolvedValueOnce({
        ...detail(42),
        data: {
          ...detail(42).data,
          deptId: 9,
          dept: { deptId: 9, deptName: '停用部门旧名' },
        },
      })
      .mockResolvedValueOnce({
        ...detail(43),
        data: {
          ...detail(43).data,
          deptId: 9,
          dept: { deptId: 9, deptName: '停用部门新名' },
        },
      });
    const wrapper = mountDialog(true);
    const api = wrapper.vm as unknown as DialogApi;
    await api.open(42);
    await flushPromises();
    let tree = wrapper.getComponent(ElTreeSelect);
    const selectedLabel = () => tree.get('.el-select__selected-item.el-select__placeholder').text();
    expect(selectedLabel()).toBe('停用部门旧名');
    await api.close();
    await api.open(43);
    await flushPromises();
    tree = wrapper.getComponent(ElTreeSelect);
    expect(tree.props('data')).toEqual([]);
    expect(tree.props('modelValue')).toBe(9);
    expect(tree.props('cacheData')).toEqual([{ id: 9, label: '停用部门新名' }]);
    expect(selectedLabel()).toBe('停用部门新名');
  });

  it('shares department reads and follows department writes without replacing the user draft', async () => {
    const scope = setQuerySession(1, [], []);
    vi.mocked(deptTreeSelect).mockResolvedValue({
      items: [{ id: 9, label: '原部门' }],
    });
    vi.mocked(getUser).mockResolvedValue({
      ...detail(42),
      data: {
        ...detail(42).data,
        deptId: 9,
        dept: { deptId: 9, deptName: '原部门' },
      },
    });
    const shared = mount(
      defineComponent({
        setup() {
          useQuery(() => userDeptTreeOptions(scope));
          return () => h('div');
        },
      }),
      { global: { plugins: [[VueQueryPlugin, { queryClient }]] } }
    );
    mounted.push(shared);
    const wrapper = mountDialog();
    await (wrapper.vm as unknown as DialogApi).open(42);
    await flushPromises();
    const tree = wrapper.findComponent({ name: 'ElTreeSelect' });
    expect(deptTreeSelect).toHaveBeenCalledTimes(1);
    expect(tree.props('data')).toEqual([{ id: 9, label: '原部门' }]);
    const model = draftOf(wrapper);
    model.nickName = '尚未保存的输入';
    vi.mocked(updateDept).mockResolvedValue({ deptId: 9, deptName: '新部门' });
    vi.mocked(deptTreeSelect).mockResolvedValue({
      items: [{ id: 9, label: '新部门' }],
    });
    await deptCommands.updateDept(captureDeptCommand({ deptId: 9, deptName: '新部门' }));
    await flushPromises();
    expect(deptTreeSelect).toHaveBeenCalledTimes(2);
    expect(tree.props('data')).toEqual([{ id: 9, label: '新部门' }]);
    expect(model.nickName).toBe('尚未保存的输入');
    expect(model.deptId).toBe(9);
    vi.mocked(deptTreeSelect).mockRejectedValueOnce(new Error('部门网络不可用'));
    await queryClient.invalidateQueries({ queryKey: deptKeys.all(scope) });
    await flushPromises();
    expect(wrapper.text()).toContain('部门列表刷新失败');
    expect(tree.props('data')).toEqual([{ id: 9, label: '新部门' }]);
    expect(model.nickName).toBe('尚未保存的输入');
  });

  it('retains the selected department label when the normal-department choices omit it', async () => {
    vi.mocked(deptTreeSelect).mockResolvedValue({ items: [] });
    vi.mocked(getUser).mockResolvedValue({
      ...detail(42),
      data: {
        ...detail(42).data,
        deptId: 9,
        dept: { deptId: 9, deptName: '停用部门' },
      },
    });
    const wrapper = mountDialog();
    await (wrapper.vm as unknown as DialogApi).open(42);
    await flushPromises();
    const tree = wrapper.findComponent({ name: 'ElTreeSelect' });
    expect(tree.props('data')).toEqual([]);
    expect(tree.props('modelValue')).toBe(9);
    expect(tree.props('cacheData')).toEqual([{ id: 9, label: '停用部门' }]);
  });

  it('ends a closed opening wait while another observer keeps the shared read', async () => {
    const scope = setQuerySession(1, [], []);
    const response = deferred();
    vi.mocked(getUser).mockReturnValueOnce(response.promise);
    const SharedReader = defineComponent({
      setup() {
        const query = useQuery(() => userDetailOptions(scope, 42));
        return () => h('span', query.data.value?.data?.userId ?? '');
      },
    });
    const shared = mount(SharedReader, {
      global: { plugins: [[VueQueryPlugin, { queryClient }]] },
    });
    try {
      const wrapper = mountDialog();
      const api = wrapper.vm as unknown as DialogApi;
      const opening = outcome(api.open(42));
      await nextTick();
      await api.close();
      const result = await opening;
      expect('error' in result && isAbortError(result.error)).toBe(true);
      expect(vi.mocked(getUser).mock.calls[0][1]?.signal?.aborted).toBe(false);
      response.resolve(detail(42));
      await flushPromises();
      expect(shared.text()).toBe('42');
      expect(getUser).toHaveBeenCalledTimes(1);
      expect(feedback.error).not.toHaveBeenCalled();
    } finally {
      shared.unmount();
    }
  });
  it('joins the replacement read when a sibling write cancels the opening snapshot', async () => {
    const first = deferred(),
      replacement = deferred();
    vi.mocked(getUser).mockReturnValueOnce(first.promise).mockReturnValueOnce(replacement.promise);
    vi.mocked(updateUser).mockResolvedValueOnce(detail(43));
    const wrapper = mountDialog();
    const opening = outcome((wrapper.vm as unknown as DialogApi).open(42));
    await nextTick();
    await userCommands.updateUser(captureUserCommand({ userId: 43, nickName: 'Sibling' }));
    await flushPromises();
    expect(feedback.error).not.toHaveBeenCalled();
    expect(getUser).toHaveBeenCalledTimes(2);
    replacement.resolve({
      ...detail(42),
      data: { ...detail(42).data, nickName: 'Replacement' },
    });
    expect(await opening).toEqual({ value: undefined });
    const dialog = wrapper.findComponent(dialogStub);
    expect(draftOf(wrapper).nickName).toBe('Replacement');
    expect(dialog.props('loading')).toBe(false);
    expect(dialog.props('okDisabled')).toBe(false);
    first.resolve(detail(42));
  });
  it('closes an old authorization scope and rejects its retained confirm callback', async () => {
    vi.mocked(getUser).mockResolvedValue(detail(42));
    const wrapper = mountDialog();
    await (wrapper.vm as unknown as DialogApi).open(42);
    const dialog = wrapper.findComponent(dialogStub);
    const confirm = dialog.props('confirm');
    setQuerySession(2, [], []);
    await nextTick();
    expect(dialog.props('modelValue')).toBe(false);
    expect(await confirm({})).toBe(false);
    expect(updateUser).not.toHaveBeenCalled();
  });

  it('takes an editable snapshot once without modifying or following cached detail', async () => {
    const scope = setQuerySession(1, [], []);
    vi.mocked(getUser).mockResolvedValue(detail(42));
    const wrapper = mountDialog();
    await (wrapper.vm as unknown as DialogApi).open(42);
    const model = draftOf(wrapper);
    const cached = queryClient.getQueryData(userDetailOptions(scope, 42).queryKey);
    expect(cached?.roleIds).toEqual([42]);
    model.roleIds = [...model.roleIds, 9];
    model.nickName = 'typing';
    expect(cached?.roleIds).toEqual([42]);
    queryClient.setQueryData(userDetailOptions(scope, 42).queryKey, {
      ...detail(42),
      data: { ...detail(42).data, nickName: 'background' },
    });
    await flushPromises();
    expect(model.nickName).toBe('typing');
    expect(model.roleIds).toEqual([42, 9]);
  });

  it('presents a paused detail read and resumes without reporting a successful empty form', async () => {
    onlineManager.setOnline(false);
    vi.mocked(getUser).mockResolvedValue(detail(42));
    const wrapper = mountDialog();
    const pending = outcome((wrapper.vm as unknown as DialogApi).open(42));
    await flushPromises();
    expect(wrapper.text()).toContain('等待网络连接');
    expect(wrapper.findComponent(dialogStub).props('okDisabled')).toBe(true);
    onlineManager.setOnline(true);
    await pending;
    expect(getUser).toHaveBeenCalledTimes(1);
  });

  it('renders the schema owner only after its opening authority is available', async () => {
    vi.mocked(getUser).mockResolvedValue({ posts: [], roles: [] });
    const wrapper = mountDialog();
    expect(wrapper.findComponent({ name: 'ZxSchemaForm' }).exists()).toBe(false);
    await (wrapper.vm as unknown as DialogApi).open();
    await flushPromises();
    expect(wrapper.find('form').exists()).toBe(true);
    expect(wrapper.findAll('input').length).toBeGreaterThan(0);
    expect(wrapper.find('select').exists()).toBe(true);
    wrapper.unmount();
  });

  it.each(['0', '1'] as const)(
    'omits the create-only password when editing status %s',
    async (status) => {
      vi.mocked(getUser).mockResolvedValue({
        data: {
          remarkText: '',
          userId: 42,
          userName: 'edited_user',
          nickName: 'Before',
          status,
        },
        postIds: [3],
        roleIds: [2],
        posts: [],
        roles: [],
      });
      const wrapper = mountDialog();
      await (wrapper.vm as unknown as { open: (id: number) => Promise<void> }).open(42);
      await nextTick();
      const dialog = wrapper.findComponent({ name: 'ZxDialog' });
      const model = draftOf(wrapper);
      expect(model.password).toBe('');
      await dialog.props('confirm')({});

      const sent = vi.mocked(updateUser).mock.calls[0][0];
      expect(sent).not.toHaveProperty('password');
      expect(sent).toMatchObject({
        userId: 42,
        status,
        roleIds: [2],
        postIds: [3],
      });
      expect(wrapper.emitted('success')).toHaveLength(1);
      expect(dialog.props('okLoading')).toBe(false);
      wrapper.unmount();
    }
  );

  it('keeps the password when creating a user', async () => {
    vi.mocked(getUser).mockResolvedValue({ posts: [], roles: [] });
    const wrapper = mountDialog();
    await (wrapper.vm as unknown as { open: () => Promise<void> }).open();
    await nextTick();
    const dialog = wrapper.findComponent({ name: 'ZxDialog' });
    Object.assign(draftOf(wrapper), {
      userName: 'created_user',
      nickName: 'Created User',
      password: 'Create123',
    });
    await dialog.props('confirm')({});

    expect(addUser).toHaveBeenCalledWith(
      expect.objectContaining({ password: 'Create123' }),
      expect.objectContaining({ context: expect.any(Object) }),
      { silentError: true }
    );
    expect(updateUser).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it('opens in loading state and ignores A when B is selected and returned first', async () => {
    const a = deferred(),
      b = deferred();
    vi.mocked(getUser).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const first = outcome(api.open(11));
    await nextTick();
    const dialog = wrapper.findComponent(dialogStub);
    expect(dialog.props('modelValue')).toBe(true);
    expect(dialog.props('loading')).toBe(true);
    expect(dialog.props('okDisabled')).toBe(true);
    const second = api.open(12);
    await nextTick();
    expect(vi.mocked(getUser).mock.calls[0][1]?.signal).toBeInstanceOf(AbortSignal);
    b.resolve(detail(12));
    await second;
    a.resolve(detail(11));
    await first;
    await nextTick();
    expect(draftOf(wrapper)).toMatchObject({
      userName: 'user_12',
      roleIds: [12],
      postIds: [12],
    });
    expect(dialog.props('loading')).toBe(false);
    expect(dialog.props('okDisabled')).toBe(false);
  });

  it('does not let an old failure clear a newer loading state or display an error', async () => {
    const a = deferred(),
      b = deferred();
    vi.mocked(getUser).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const old = outcome(api.open(11)),
      current = api.open(12);
    a.reject(new Error('old failure'));
    await old;
    await nextTick();
    const dialog = wrapper.findComponent(dialogStub);
    expect(dialog.props('modelValue')).toBe(true);
    expect(dialog.props('loading')).toBe(true);
    expect(dialog.props('okDisabled')).toBe(true);
    expect(feedback.error).not.toHaveBeenCalled();
    expect(feedback.problem).not.toHaveBeenCalled();
    b.resolve(detail(12));
    await current;
    await nextTick();
    expect(draftOf(wrapper).userName).toBe('user_12');
    expect(dialog.props('loading')).toBe(false);
  });

  it('invalidates a closed opening and keeps its late response from releasing a reopened read', async () => {
    const old = deferred(),
      current = deferred();
    vi.mocked(getUser).mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise);
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const first = outcome(api.open(11));
    await nextTick();
    const dialog = wrapper.findComponent(dialogStub);
    dialog.vm.$emit('update:modelValue', false);
    await nextTick();
    expect(vi.mocked(getUser).mock.calls[0][1]?.signal).toBeInstanceOf(AbortSignal);
    expect(dialog.props('modelValue')).toBe(false);
    const next = api.open(11);
    await nextTick();
    old.resolve(detail(11));
    await first;
    await nextTick();
    expect(dialog.props('loading')).toBe(true);
    expect(wrapper.findComponent({ name: 'ZxSchemaForm' }).exists()).toBe(false);
    current.resolve({
      ...detail(11),
      data: { ...detail(11).data, nickName: 'Reopened' },
    });
    await next;
    await nextTick();
    expect(draftOf(wrapper).nickName).toBe('Reopened');
    expect(dialog.props('loading')).toBe(false);
  });

  it('keeps a newer create opening when an older edit read finishes', async () => {
    const edit = deferred();
    vi.mocked(getUser)
      .mockReturnValueOnce(edit.promise)
      .mockResolvedValueOnce({ posts: [], roles: [] });
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const old = outcome(api.open(11));
    await api.open();
    edit.resolve(detail(11));
    await old;
    await nextTick();
    const model = draftOf(wrapper);
    expect(formOf(wrapper).read()).not.toHaveProperty('userId');
    expect(model.userName).toBe('');
    expect(model.password).toBe('');
  });

  it('keeps a failed current read disabled and retries the same user explicitly', async () => {
    const error = new Error('read failed');
    vi.mocked(getUser).mockRejectedValueOnce(error).mockResolvedValueOnce(detail(12));
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const result = await outcome(api.open(12));
    await nextTick();
    expect(result).toEqual({ error });
    const dialog = wrapper.findComponent(dialogStub);
    expect(dialog.props('modelValue')).toBe(true);
    expect(dialog.props('loading')).toBe(false);
    expect(dialog.props('okDisabled')).toBe(true);
    expect(feedback.error).not.toHaveBeenCalled();
    const retry = wrapper.findAll('button').find((button) => button.text() === '重试');
    expect(retry).toBeDefined();
    await retry!.trigger('click');
    await flushPromises();
    expect(getUser).toHaveBeenLastCalledWith(
      12,
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(draftOf(wrapper).userName).toBe('user_12');
    expect(dialog.props('okDisabled')).toBe(false);
  });

  it('restores current 401 recovery while keeping an expired opening silent', async () => {
    const a = deferred(),
      b = deferred();
    vi.mocked(getUser).mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    const old = outcome(api.open(11));
    const current = outcome(api.open(22));
    const failure = Object.assign(new Error('expired'), {
      problem: { status: 401 },
      meta: { status: 401 },
      config: { silentError: true },
    });
    a.reject(failure);
    await old;
    expect(feedback.recovery).not.toHaveBeenCalled();
    b.reject(failure);
    expect(await current).toEqual({ error: failure });
    expect(feedback.recovery).toHaveBeenCalledExactlyOnceWith(
      failure,
      expect.objectContaining({
        silentError: false,
        feedback: { mode: 'auto' },
      })
    );
    expect(failure.config.silentError).toBe(true);
  });

  it('ignores a non-cooperating late response after disposal', async () => {
    const response = deferred();
    vi.mocked(getUser).mockReturnValueOnce(response.promise);
    const wrapper = mountDialog();
    const task = outcome((wrapper.vm as unknown as DialogApi).open(11));
    await nextTick();
    wrapper.unmount();
    expect(vi.mocked(getUser).mock.calls[0][1]?.signal).toBeInstanceOf(AbortSignal);
    response.resolve(detail(11));
    await task;
    expect(feedback.error).not.toHaveBeenCalled();
    expect(feedback.problem).not.toHaveBeenCalled();
    expect(wrapper.emitted('success')).toBeUndefined();
  });
});

it('submits only editable user fields when the draft contains response metadata', async () => {
  vi.mocked(getUser).mockResolvedValue(detail(42));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const dialog = wrapper.findComponent(dialogStub);
  const model = draftOf(wrapper);
  Object.assign(model, {
    password: 'must-not-write',
    loginIp: 'response-only',
    createBy: 'response-only',
    type: 'status',
    admin: true,
  });
  await dialog.props('confirm')(model);
  const payload = vi.mocked(updateUser).mock.calls[0][0];
  expect(payload).toMatchObject({
    userId: 42,
    nickName: 'User 42',
    roleIds: [42],
    postIds: [42],
  });
  for (const field of ['password', 'loginIp', 'createBy', 'type', 'admin'])
    expect(payload).not.toHaveProperty(field);
});

it('protects a format-only remark draft on close and replacement, while clean authority closes directly', async () => {
  const confirm = vi.spyOn(ElMessageBox, 'confirm').mockRejectedValue(new Error('继续编辑'));
  try {
    const original = readRemark(mockRemark('same text', 'userguard'))!;
    vi.mocked(getUser).mockResolvedValue({
      ...detail(42),
      data: { ...detail(42).data, remark: original },
    });
    const wrapper = mountDialog();
    const api = wrapper.vm as unknown as DialogApi;
    await api.open(42);
    const shell = wrapper.findComponent(dialogStub);
    const model = draftOf(wrapper);
    const formatted = structuredClone(original);
    const text = formatted.body.content.content[0].content![0];
    if (text.type !== 'text') throw new Error('Expected text fixture');
    text.marks = [{ type: 'bold' }];
    model.remark = formatted;
    await nextTick();
    await api.close();
    expect(shell.props('modelValue')).toBe(true);
    await api.open(43);
    expect(model.userName).toBe('user_42');
    expect(vi.mocked(getUser)).toHaveBeenCalledTimes(1);
    expect(model.remark).toEqual(formatted);
    confirm.mockResolvedValue(
      Object.assign('confirm' as const, {
        value: '',
        action: 'confirm' as const,
      })
    );
    await api.close();
    expect(shell.props('modelValue')).toBe(false);
    await api.open(42);
    confirm.mockClear();
    await api.close();
    expect(confirm).not.toHaveBeenCalled();
  } finally {
    confirm.mockRestore();
  }
});

it('blocks invalid creation with field feedback and retries a corrected draft', async () => {
  vi.mocked(getUser).mockResolvedValue({ posts: [], roles: [] });
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open();
  const form = formOf(wrapper);
  const dialog = wrapper.getComponent(dialogStub);
  expect(await dialog.props('confirm')()).toBe(false);
  expect(addUser).not.toHaveBeenCalled();
  expect(wrapper.text()).toContain('用户昵称不能为空');
  expect(wrapper.text()).toContain('用户密码需为');
  await form.setValues({
    ...form.read(),
    nickName: 'Created',
    userName: 'created_user',
    password: 'Secret123',
  });
  await dialog.props('confirm')();
  expect(addUser).toHaveBeenCalledTimes(1);
  expect(wrapper.emitted('success')).toHaveLength(1);
});

it('routes known server conflicts into the owner while permitting a corrected retry', async () => {
  vi.mocked(getUser).mockResolvedValue(detail(42));
  vi.mocked(updateUser).mockRejectedValueOnce(
    Object.assign(new Error('邮箱已存在'), {
      problem: { status: 409, errorCode: 30008, detail: '邮箱已存在' },
    })
  );
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const form = formOf(wrapper),
    shell = wrapper.getComponent(dialogStub);
  await shell.props('confirm')();
  expect(form.reconciliationRequired).toBe(false);
  expect(wrapper.text()).toContain('邮箱已存在');
  expect(feedback.problem).not.toHaveBeenCalled();
  await form.setValues({ ...form.read(), email: 'new@example.com' });
  await shell.props('confirm')();
  expect(updateUser).toHaveBeenCalledTimes(2);
  expect(wrapper.emitted('success')).toHaveLength(1);
});

it('locks an uncertain creation, reconciles its captured username, then edits by the new id', async () => {
  vi.mocked(getUser).mockImplementation(async (id) =>
    id === undefined
      ? { posts: [], roles: [] }
      : {
          ...detail(99),
          data: { ...detail(99).data, userName: 'created_user', nickName: 'Created' },
        }
  );
  vi.mocked(addUser).mockRejectedValueOnce(new Error('response lost'));
  vi.mocked(listUser).mockResolvedValue({
    items: [{ ...detail(99).data, userName: 'created_user' }],
    total: 1,
    page: 1,
    pageSize: 100,
  });
  const wrapper = mountDialog(),
    api = wrapper.vm as unknown as DialogApi;
  await api.open();
  let form = formOf(wrapper);
  await form.setValues({
    ...form.read(),
    nickName: 'Created',
    userName: 'created_user',
    password: 'Secret123',
  });
  const shell = wrapper.getComponent(dialogStub);
  await shell.props('confirm')();
  expect(form.reconciliationRequired).toBe(true);
  await shell.props('confirm')();
  await api.close();
  expect(addUser).toHaveBeenCalledTimes(1);
  expect(shell.props('modelValue')).toBe(true);
  await wrapper
    .findAll('button')
    .find((button) => button.text() === '读取并核对用户')!
    .trigger('click');
  await flushPromises();
  expect(listUser).toHaveBeenCalledWith(
    expect.objectContaining({ userName: 'created_user' }),
    expect.anything()
  );
  form = formOf(wrapper);
  expect(form.reconciliationRequired).toBe(false);
  expect(form.dirty).toBe(false);
  expect(form.read().password).toBe('');
  await form.setValues({ ...form.read(), nickName: 'After reconcile' });
  await shell.props('confirm')();
  expect(addUser).toHaveBeenCalledTimes(1);
  expect(updateUser).toHaveBeenCalledWith(
    expect.objectContaining({ userId: 99, nickName: 'After reconcile' }),
    expect.anything(),
    { silentError: true }
  );
  expect(vi.mocked(updateUser).mock.calls[0][0]).not.toHaveProperty('password');
});

it('keeps uncertainty after ambiguous lookup or mismatched authority until an exact match', async () => {
  vi.mocked(getUser).mockResolvedValueOnce({ posts: [], roles: [] });
  vi.mocked(addUser).mockRejectedValueOnce(new Error('response lost'));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open();
  const form = formOf(wrapper),
    shell = wrapper.getComponent(dialogStub);
  await form.setValues({
    ...form.read(),
    nickName: 'Created',
    userName: 'created_user',
    password: 'Secret123',
  });
  await shell.props('confirm')();
  vi.mocked(listUser).mockResolvedValueOnce({ items: [], total: 0, page: 1, pageSize: 100 });
  const reconcile = () =>
    wrapper
      .findAll('button')
      .find((button) => button.text() === '读取并核对用户')!
      .trigger('click');
  await reconcile();
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(true);
  vi.mocked(listUser).mockResolvedValue({
    items: [{ ...detail(99).data, userName: 'created_user' }],
    total: 1,
    page: 1,
    pageSize: 100,
  });
  vi.mocked(getUser).mockResolvedValueOnce({
    ...detail(99),
    data: { ...detail(99).data, userName: 'someone_else' },
  });
  await reconcile();
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(true);
  expect(wrapper.text()).toContain('读取的用户身份与本次保存不符');
  await shell.props('confirm')();
  expect(addUser).toHaveBeenCalledTimes(1);
});

it('reconciles an uncertain edit only with the captured user id', async () => {
  vi.mocked(getUser).mockResolvedValueOnce(detail(42));
  vi.mocked(updateUser).mockRejectedValueOnce(new Error('response lost'));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const shell = wrapper.getComponent(dialogStub);
  await shell.props('confirm')();
  vi.mocked(getUser).mockResolvedValueOnce(detail(43));
  await wrapper
    .findAll('button')
    .find((button) => button.text() === '读取并核对用户')!
    .trigger('click');
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(true);
  expect(listUser).not.toHaveBeenCalled();
  vi.mocked(getUser).mockResolvedValueOnce({
    ...detail(42),
    data: { ...detail(42).data, nickName: 'Server authority' },
  });
  await wrapper
    .findAll('button')
    .find((button) => button.text() === '读取并核对用户')!
    .trigger('click');
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(false);
  expect(formOf(wrapper).read().nickName).toBe('Server authority');
  expect(updateUser).toHaveBeenCalledTimes(1);
});

it('rejects malformed save authority and never retries an uncertain write automatically', async () => {
  vi.mocked(getUser).mockResolvedValue(detail(42));
  vi.mocked(updateUser).mockResolvedValueOnce(detail(43));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const shell = wrapper.getComponent(dialogStub);
  await shell.props('confirm')();
  expect(formOf(wrapper).reconciliationRequired).toBe(true);
  expect(wrapper.emitted('success')).toBeUndefined();
  await shell.props('confirm')();
  expect(updateUser).toHaveBeenCalledTimes(1);
});

it('blocks duplicate writes and old-scope completion while a save is in flight', async () => {
  vi.mocked(getUser).mockResolvedValue(detail(42));
  const save = deferred();
  vi.mocked(updateUser).mockReturnValueOnce(save.promise);
  const wrapper = mountDialog(),
    api = wrapper.vm as unknown as DialogApi;
  await api.open(42);
  const shell = wrapper.getComponent(dialogStub);
  const saving = shell.props('confirm')();
  await flushPromises();
  expect(formOf(wrapper).pending).toBe(true);
  await shell.props('confirm')();
  await api.open(43);
  expect(updateUser).toHaveBeenCalledTimes(1);
  expect(formOf(wrapper).read().userName).toBe('user_42');
  setQuerySession(2, [], []);
  await nextTick();
  save.resolve(detail(42));
  await saving;
  expect(shell.props('modelValue')).toBe(false);
  expect(wrapper.emitted('success')).toBeUndefined();
});

it('honors the rich remark validation port and keeps AI bindings inside the field owner', async () => {
  vi.mocked(getUser).mockResolvedValue(detail(42));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const form = formOf(wrapper),
    scope = aiScopes.at(-1)!;
  await form.setValues({
    ...form.read(),
    nickName: 'Current Nick',
    phonenumber: '13912345678',
    email: 'user@example.com',
  });
  expect(contextValue(scope, 'nickName')).toBe('Current Nick');
  expect(contextValue(scope, 'phonenumber')).toBe('13912345678');
  expect(contextValue(scope, 'email')).toBe('user@example.com');
  expect(contextValue(scope, 'userName')).toBe('user_42');
  expect(scope.binding('password')).toBeUndefined();
  const remark = wrapper.getComponent({ name: 'RemarkEditor' });
  const validate = vi
    .spyOn(remark.vm.$.exposed! as { validate(): boolean }, 'validate')
    .mockReturnValue(false);
  remark.vm.$emit('edit-state', { pending: true });
  await nextTick();
  expect(form.fieldPending).toBe(true);
  await wrapper.getComponent(dialogStub).props('confirm')();
  expect(updateUser).not.toHaveBeenCalled();
  validate.mockRestore();
  remark.vm.$emit('edit-state', { pending: false });
  await nextTick();
  expect(form.fieldPending).toBe(false);
  await wrapper.getComponent(dialogStub).props('confirm')();
  expect(updateUser).toHaveBeenCalledTimes(1);
  await nextTick();
  expect(scope.binding('nickName')).toBeUndefined();
});

it('reconciles from a new request after an uncertain write and invalidates list cache', async () => {
  const scope = setQuerySession(1, [], []);
  const list = userListOptions(scope, { page: 1, pageSize: 10 });
  queryClient.setQueryData(list.queryKey, {
    items: [detail(42).data],
    total: 1,
    page: 1,
    pageSize: 10,
  });
  vi.mocked(getUser).mockResolvedValueOnce(detail(42));
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const old = deferred(),
    fresh = deferred();
  vi.mocked(getUser).mockReturnValueOnce(old.promise);
  const background = queryClient.refetchQueries(
    { queryKey: userDetailOptions(scope, 42).queryKey, exact: true },
    { cancelRefetch: false }
  );
  await flushPromises();
  vi.mocked(updateUser).mockRejectedValueOnce(new Error('response lost'));
  await wrapper.getComponent(dialogStub).props('confirm')();
  vi.mocked(getUser).mockReturnValueOnce(fresh.promise);
  await wrapper
    .findAll('button')
    .find((button) => button.text() === '读取并核对用户')!
    .trigger('click');
  await flushPromises();
  expect(getUser).toHaveBeenCalledTimes(3);
  expect(vi.mocked(getUser).mock.calls[2][1]).toMatchObject({
    silentError: true,
    signal: expect.any(AbortSignal),
  });
  old.resolve({ ...detail(42), data: { ...detail(42).data, nickName: 'Before write' } });
  await background;
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(true);
  fresh.resolve({ ...detail(42), data: { ...detail(42).data, nickName: 'After write' } });
  await flushPromises();
  expect(formOf(wrapper).reconciliationRequired).toBe(false);
  expect(formOf(wrapper).read().nickName).toBe('After write');
  expect(queryClient.getQueryState(list.queryKey)?.isInvalidated).toBe(true);
  expect(updateUser).toHaveBeenCalledTimes(1);
});

it('submits native inputs and multiple choice controls through their actual field events', async () => {
  vi.mocked(getUser).mockResolvedValue({
    posts: [{ postId: 3, postName: '工程师', status: '0', remarkText: '' }],
    roles: [{ roleId: 2, roleName: '操作员', status: '0', remarkText: '' }],
  });
  const wrapper = mountDialog(true);
  await (wrapper.vm as unknown as DialogApi).open();
  await flushPromises();
  await wrapper.get('input[placeholder="请输入用户昵称"]').setValue('Native User');
  await wrapper.get('input[placeholder="请输入用户名称"]').setValue('native_user');
  await wrapper.get('input[placeholder="请输入用户密码"]').setValue('Secret123');
  const multiple = wrapper.findAllComponents(ElSelect).filter((select) => select.props('multiple'));
  expect(multiple).toHaveLength(2);
  for (const [index, label] of ['工程师', '操作员'].entries()) {
    await multiple[index].get('.el-select__wrapper').trigger('click');
    await flushPromises();
    const popupId = multiple[index].get('input').attributes('aria-controls');
    const option = [...document.getElementById(popupId!)!.querySelectorAll('[role="option"]')].find(
      (item) => item.textContent?.trim() === label
    );
    expect(option).toBeDefined();
    option!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await flushPromises();
  }
  expect(formOf(wrapper).read()).toMatchObject({
    nickName: 'Native User',
    userName: 'native_user',
    postIds: [3],
    roleIds: [2],
  });
  await wrapper.getComponent(dialogStub).props('confirm')();
  expect(addUser).toHaveBeenCalledWith(
    expect.objectContaining({
      nickName: 'Native User',
      userName: 'native_user',
      postIds: [3],
      roleIds: [2],
    }),
    expect.anything(),
    { silentError: true }
  );
});

it('does not accept a nonpositive identity from a successful create response', async () => {
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open();
  const form = formOf(wrapper);
  await form.setValues({
    ...form.read(),
    nickName: 'Created',
    userName: 'created_user',
    password: 'Secret123',
  });
  vi.mocked(addUser).mockResolvedValueOnce({
    ...detail(-1),
    data: { ...detail(-1).data, userName: 'created_user' },
  });
  await wrapper.getComponent(dialogStub).props('confirm')();
  expect(form.reconciliationRequired).toBe(true);
  expect(wrapper.emitted('success')).toBeUndefined();
});

it('restores current authentication recovery once for an owner-managed save rejection', async () => {
  const wrapper = mountDialog();
  await (wrapper.vm as unknown as DialogApi).open(42);
  const failure = Object.assign(new Error('expired'), {
    problem: { status: 401, errorCode: 20001 },
  });
  vi.mocked(updateUser).mockRejectedValueOnce(failure);
  await wrapper.getComponent(dialogStub).props('confirm')();
  expect(feedback.recovery).toHaveBeenCalledExactlyOnceWith(
    failure,
    expect.objectContaining({ silentError: false, feedback: { mode: 'auto' } })
  );
  expect(formOf(wrapper).reconciliationRequired).toBe(false);
  expect(wrapper.emitted('success')).toBeUndefined();
});
