/**
 * Unit tests for UserFormDialog component
 */
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { isAbortError } from '@zxio/http';
import { ElOption, ElSelect, ElTreeSelect } from 'element-plus';
import { defineComponent, h, nextTick, ref } from 'vue';
import { addUser, deptTreeSelect, getUser, updateUser } from '@/api/system/user';
import { updateDept } from '@/api/system/dept';
import UserFormDialog from '@/views/system/user/components/UserFormDialog.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { captureUserCommand, userCommands, userDetailOptions } from '@/queries/system/user';
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
}));
vi.mock('@/api/system/dept', () => ({
  listDept: vi.fn(),
  listDeptExcludeChild: vi.fn(),
  getDept: vi.fn(),
  addDept: vi.fn(),
  updateDept: vi.fn(),
  delDept: vi.fn(),
}));
vi.mock('@/utils/dict', () => ({ useDict: () => ({ sys_normal_disable: ref([]) }) }));

const feedback = vi.hoisted(() => ({ error: vi.fn(), problem: vi.fn(), recovery: vi.fn() }));
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
  props: ['confirm', 'formModel', 'okLoading', 'okDisabled', 'loading', 'modelValue'],
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

type DialogApi = { open: (id?: number) => Promise<void>; close: () => Promise<void> };
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
const detail = (id: number): UserDetail => ({
  data: { userId: id, userName: `user_${id}`, nickName: `User ${id}`, status: '0' },
  postIds: [id],
  roleIds: [id],
  posts: [],
  roles: [],
});
const outcome = <T>(promise: Promise<T>) =>
  promise.then(
    (value) => ({ value }),
    (error) => ({ error })
  );
const mounted: ReturnType<typeof mount>[] = [];

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
  const wrapper = mount(UserFormDialog, {
    attachTo: nativeTree ? document.body : undefined,
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      components: { ElTreeSelect, ElSelect, ElOption },
      stubs: {
        DictStatus: true,
        DictSelect: true,
        ZxDialog: dialogStub,
        ElForm: formStub,
        ElFormItem: renderSlotStub,
        ElRow: renderSlotStub,
        ElCol: renderSlotStub,
        ZxInput: { inheritAttrs: false, template: '<input />' },
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
        ElAlert: { props: ['title'], template: '<aside>{{ title }}<slot /></aside>' },
        ElButton: { template: '<button><slot /></button>' },
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}

beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, [], []);
  onlineManager.setOnline(true);
  vi.mocked(deptTreeSelect).mockResolvedValue({ items: [{ id: 1, label: '研发部' }] });
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
  vi.clearAllMocks();
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
    const tree = wrapper.getComponent(ElTreeSelect);
    const element = tree.element;
    expect(tree.props('modelValue')).toBeUndefined();
    expect(document.querySelector('.el-tree-node[data-key="9"]')).toBeNull();
    response.resolve({
      ...detail(42),
      data: { ...detail(42).data, deptId: 9, dept: { deptId: 9, deptName: '原部门' } },
    });
    await opening;
    await flushPromises();
    const selectedLabel = () => tree.get('.el-select__selected-item.el-select__placeholder').text();
    expect(selectedLabel()).toBe('原部门');
    const model = wrapper.findComponent(dialogStub).props('formModel');
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
        data: { ...detail(42).data, deptId: 9, dept: { deptId: 9, deptName: '停用部门旧名' } },
      })
      .mockResolvedValueOnce({
        ...detail(43),
        data: { ...detail(43).data, deptId: 9, dept: { deptId: 9, deptName: '停用部门新名' } },
      });
    const wrapper = mountDialog(true);
    const api = wrapper.vm as unknown as DialogApi;
    await api.open(42);
    await flushPromises();
    const tree = wrapper.getComponent(ElTreeSelect);
    const element = tree.element;
    const selectedLabel = () => tree.get('.el-select__selected-item.el-select__placeholder').text();
    expect(selectedLabel()).toBe('停用部门旧名');
    await api.close();
    await api.open(43);
    await flushPromises();
    expect(tree.props('data')).toEqual([]);
    expect(tree.props('modelValue')).toBe(9);
    expect(tree.props('cacheData')).toEqual([{ id: 9, label: '停用部门新名' }]);
    expect(tree.element).toBe(element);
    expect(selectedLabel()).toBe('停用部门新名');
  });

  it('shares department reads and follows department writes without replacing the user draft', async () => {
    const scope = setQuerySession(1, [], []);
    vi.mocked(deptTreeSelect).mockResolvedValue({ items: [{ id: 9, label: '原部门' }] });
    vi.mocked(getUser).mockResolvedValue({
      ...detail(42),
      data: { ...detail(42).data, deptId: 9, dept: { deptId: 9, deptName: '原部门' } },
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
    const model = wrapper.findComponent(dialogStub).props('formModel');
    model.nickName = '尚未保存的输入';
    vi.mocked(updateDept).mockResolvedValue({ deptId: 9, deptName: '新部门' });
    vi.mocked(deptTreeSelect).mockResolvedValue({ items: [{ id: 9, label: '新部门' }] });
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
      data: { ...detail(42).data, deptId: 9, dept: { deptId: 9, deptName: '停用部门' } },
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
    vi.mocked(updateUser).mockResolvedValueOnce({ userId: 43 });
    const wrapper = mountDialog();
    const opening = outcome((wrapper.vm as unknown as DialogApi).open(42));
    await nextTick();
    await userCommands.updateUser(captureUserCommand({ userId: 43, nickName: 'Sibling' }));
    await flushPromises();
    expect(feedback.error).not.toHaveBeenCalled();
    expect(getUser).toHaveBeenCalledTimes(2);
    replacement.resolve({ ...detail(42), data: { ...detail(42).data, nickName: 'Replacement' } });
    expect(await opening).toEqual({ value: undefined });
    const dialog = wrapper.findComponent(dialogStub);
    expect(dialog.props('formModel').nickName).toBe('Replacement');
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
    const model = wrapper.findComponent(dialogStub).props('formModel');
    const cached = queryClient.getQueryData(userDetailOptions(scope, 42).queryKey);
    expect(cached?.roleIds).toEqual([42]);
    model.roleIds.push(9);
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

  it('should render the user form inside the dialog shell', () => {
    const wrapper = mountDialog();
    expect(wrapper.find('form').exists()).toBe(true);
    expect(wrapper.findAll('input').length).toBeGreaterThan(0);
    expect(wrapper.find('select').exists()).toBe(true);
    wrapper.unmount();
  });

  it.each(['0', '1'] as const)(
    'omits the create-only password when editing status %s',
    async (status) => {
      vi.mocked(getUser).mockResolvedValue({
        data: { userId: 42, userName: 'edited_user', nickName: 'Before', status },
        postIds: [3],
        roleIds: [2],
        posts: [],
        roles: [],
      });
      const wrapper = mountDialog();
      await (wrapper.vm as unknown as { open: (id: number) => Promise<void> }).open(42);
      await nextTick();
      const dialog = wrapper.findComponent({ name: 'ZxDialog' });
      const model = dialog.props('formModel');
      expect(model.password).toBe('');
      await dialog.props('confirm')({});

      const sent = vi.mocked(updateUser).mock.calls[0][0];
      expect(sent).not.toHaveProperty('password');
      expect(sent).toMatchObject({ userId: 42, status, roleIds: [2], postIds: [3] });
      expect(model.password).toBe('');
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
    Object.assign(dialog.props('formModel'), { userName: 'created_user', password: 'Create123' });
    await dialog.props('confirm')({});

    expect(addUser).toHaveBeenCalledWith(
      expect.objectContaining({ password: 'Create123' }),
      expect.objectContaining({ context: expect.any(Object) })
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
    expect(dialog.props('formModel')).toMatchObject({ userId: 12, roleIds: [12], postIds: [12] });
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
    expect(dialog.props('formModel').userId).toBe(12);
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
    expect(dialog.props('formModel').nickName).toBe('');
    current.resolve({ ...detail(11), data: { ...detail(11).data, nickName: 'Reopened' } });
    await next;
    await nextTick();
    expect(dialog.props('formModel').nickName).toBe('Reopened');
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
    const model = wrapper.findComponent(dialogStub).props('formModel');
    expect(model.userId).toBeUndefined();
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
    expect(feedback.error).toHaveBeenCalledExactlyOnceWith(error.message);
    const retry = wrapper.findAll('button').find((button) => button.text() === '重试');
    expect(retry).toBeDefined();
    await retry!.trigger('click');
    await flushPromises();
    expect(getUser).toHaveBeenLastCalledWith(
      12,
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(dialog.props('formModel').userId).toBe(12);
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
      expect.objectContaining({ silentError: false, feedback: { mode: 'auto' } })
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
  const model = dialog.props('formModel');
  Object.assign(model, {
    password: 'must-not-write',
    loginIp: 'response-only',
    createBy: 'response-only',
    type: 'status',
    admin: true,
  });
  await dialog.props('confirm')(model);
  const payload = vi.mocked(updateUser).mock.calls[0][0];
  expect(payload).toMatchObject({ userId: 42, nickName: 'User 42', roleIds: [42], postIds: [42] });
  for (const field of ['password', 'loginIp', 'createBy', 'type', 'admin'])
    expect(payload).not.toHaveProperty(field);
});
