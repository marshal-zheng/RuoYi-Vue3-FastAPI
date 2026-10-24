import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { isAbortError } from '@zxio/http';
import { deptDetailOptions, deptExcludeChildOptions } from '@/queries/system/dept';
import { defineComponent, h, nextTick, type ComponentCustomProperties } from 'vue';
import DeptDlg from '@/views/system/dept/components/DeptDlg.vue';
import { addDept, getDept, listDept, listDeptExcludeChild, updateDept } from '@/api/system/dept';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { handleTree } from '@/utils/ruoyi';

vi.mock('@/api/system/dept', () => ({
  listDept: vi.fn(),
  getDept: vi.fn(),
  listDeptExcludeChild: vi.fn(),
  addDept: vi.fn(),
  updateDept: vi.fn(),
  delDept: vi.fn(),
}));
vi.mock('@/utils/dict', () => ({
  useDict: () => ({ sys_normal_disable: [] }),
}));
const feedback = vi.hoisted(() => ({ error: vi.fn(), recovery: vi.fn() }));
vi.mock('@/utils/http', () => ({ presentRequestError: feedback.recovery }));
vi.mock('element-plus', () => ({ ElMessage: { error: feedback.error } }));
const shell = defineComponent({
  name: 'DeptShell',
  inheritAttrs: false,
  props: ['confirm', 'formModel', 'okDisabled', 'loading', 'modelValue'],
  emits: ['update:modelValue', 'close'],
  setup(_, { slots, emit, expose }) {
    expose({
      close: () => {
        emit('update:modelValue', false);
        emit('close');
      },
    });
    return () => h('section', slots.default?.());
  },
});
const slot = { inheritAttrs: false, template: '<div><slot /></div>' };
const tree = defineComponent({
  name: 'DeptParents',
  props: ['data'],
  template: '<select />',
});
const mounted: ReturnType<typeof mount>[] = [];
type DialogApi = {
  open: (seed?: { deptId?: number; parentId?: number }) => Promise<void>;
  close: () => Promise<void>;
};
const detail = (id: number) => ({
  deptId: id,
  parentId: 1,
  deptName: `Dept ${id}`,
  orderNum: 0,
  status: '0' as const,
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((ok) => {
    resolve = ok;
  });
  return { promise, resolve };
}
const outcome = <T>(promise: Promise<T>) =>
  promise.then(
    (value) => ({ value }),
    (error) => ({ error })
  );
function mountDialog() {
  const wrapper = mount(DeptDlg, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      config: { globalProperties: { handleTree } as ComponentCustomProperties },
      stubs: {
        ZxDialog: shell,
        ElForm: slot,
        ElFormItem: slot,
        FormGrid: slot,
        ElTreeSelect: tree,
        ZxInput: true,
        ElInputNumber: true,
        DictStatus: true,
        ElRadioGroup: slot,
        ElRadio: true,
        ElAlert: {
          props: ['title'],
          template: '<aside>{{ title }}<slot /></aside>',
        },
        ElButton: { template: '<button><slot /></button>' },
      },
    },
  });
  mounted.push(wrapper);
  return {
    wrapper,
    api: wrapper.vm as unknown as DialogApi,
    shell: () => wrapper.findComponent(shell),
    model: () =>
      wrapper.findComponent(shell).props('formModel') as ReturnType<typeof detail> &
        Record<string, unknown>,
  };
}
beforeEach(() => {
  vi.resetAllMocks();
  queryClient.clear();
  setQuerySession(1, [], []);
  onlineManager.setOnline(true);
  vi.mocked(getDept).mockImplementation(async (id) => detail(Number(id)));
  vi.mocked(listDept).mockResolvedValue({
    items: [{ deptId: 1, parentId: 0, deptName: 'Root' }],
  });
  vi.mocked(listDeptExcludeChild).mockResolvedValue({
    items: [{ deptId: 1, parentId: 0, deptName: 'Root' }],
  });
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

describe('department editor resource lifecycle', () => {
  it.each(['close', 'unmount'] as const)(
    'ends a waiting opening on %s while another subscriber keeps its shared read',
    async (action) => {
      const scope = setQuerySession(1, [], []);
      const response = deferred<ReturnType<typeof detail>>();
      vi.mocked(getDept).mockReturnValueOnce(response.promise);
      const SharedReader = defineComponent({
        setup() {
          const query = useQuery(() => deptDetailOptions(scope, 11));
          return () => h('span', query.data.value?.deptName ?? '');
        },
      });
      const shared = mount(SharedReader, {
        global: { plugins: [[VueQueryPlugin, { queryClient }]] },
      });
      const e = mountDialog();
      const opening = outcome(e.api.open({ deptId: 11 }));
      let settled = false;
      void opening.then(() => {
        settled = true;
      });
      try {
        await nextTick();
        if (action === 'close') await e.api.close();
        else {
          e.wrapper.unmount();
          mounted.splice(mounted.indexOf(e.wrapper), 1);
        }
        await flushPromises();
        expect(settled).toBe(true);
        const result = await opening;
        expect('error' in result && isAbortError(result.error)).toBe(true);
        expect(vi.mocked(getDept).mock.calls[0][1]?.signal?.aborted).toBe(false);
        response.resolve(detail(11));
        await flushPromises();
        expect(shared.text()).toBe('Dept 11');
        expect(getDept).toHaveBeenCalledTimes(1);
        expect(feedback.error).not.toHaveBeenCalled();
      } finally {
        response.resolve(detail(11));
        shared.unmount();
      }
    }
  );

  it('retains parent choices and draft after a background failure and retries only choices', async () => {
    const scope = setQuerySession(1, [], []);
    const e = mountDialog();
    await e.api.open({ deptId: 11 });
    e.model().deptName = 'typing';
    vi.mocked(listDeptExcludeChild).mockRejectedValueOnce(new Error('parent refresh failed'));
    await queryClient.refetchQueries({ queryKey: deptExcludeChildOptions(scope, 11).queryKey });
    await flushPromises();
    expect(e.wrapper.text()).toContain('上级部门刷新失败');
    expect(e.model().deptName).toBe('typing');
    expect(e.wrapper.findComponent(tree).props('data')).toMatchObject([{ deptName: 'Root' }]);
    vi.mocked(listDeptExcludeChild).mockResolvedValueOnce({
      items: [{ deptId: 1, parentId: 0, deptName: 'Updated parent' }],
    });
    await e.wrapper
      .findAll('button')
      .find((button) => button.text() === '重试读取')!
      .trigger('click');
    await flushPromises();
    expect(e.wrapper.findComponent(tree).props('data')).toMatchObject([
      { deptName: 'Updated parent' },
    ]);
    expect(e.model().deptName).toBe('typing');
    expect(getDept).toHaveBeenCalledTimes(1);
  });

  it('observes refreshed parent choices while protecting the editable detail snapshot', async () => {
    const e = mountDialog();
    await e.api.open({ deptId: 11 });
    const cachedDetail = queryClient
      .getQueryCache()
      .getAll()
      .find((query) => query.state.data && (query.state.data as { deptId?: number }).deptId === 11);
    const cachedParents = queryClient
      .getQueryCache()
      .getAll()
      .find((query) => (query.state.data as { items?: unknown[] })?.items);
    expect(cachedDetail).toBeDefined();
    expect(cachedParents).toBeDefined();
    const model = e.model();
    model.deptName = 'typing';
    queryClient.setQueryData(cachedDetail!.queryKey, {
      ...detail(11),
      deptName: 'background',
    });
    queryClient.setQueryData(cachedParents!.queryKey, {
      items: [{ deptId: 1, parentId: 0, deptName: 'Renamed root' }],
    });
    await flushPromises();
    expect(e.model()).toBe(model);
    expect(e.model().deptName).toBe('typing');
    expect(e.wrapper.findComponent(tree).props('data')).toMatchObject([
      { deptName: 'Renamed root' },
    ]);
  });
  it('closes on authorization changes and rejects an old confirm callback', async () => {
    const e = mountDialog();
    await e.api.open({ deptId: 11 });
    const confirm = e.shell().props('confirm');
    setQuerySession(2, [], []);
    await nextTick();
    expect(e.shell().props('modelValue')).toBe(false);
    expect(await confirm({})).toBe(false);
    expect(updateDept).not.toHaveBeenCalled();
  });
  it('presents paused detail and options reads without enabling an empty draft', async () => {
    onlineManager.setOnline(false);
    const e = mountDialog();
    const opening = outcome(e.api.open({ deptId: 11 }));
    await flushPromises();
    expect(e.wrapper.text()).toContain('等待网络连接');
    expect(e.shell().props('okDisabled')).toBe(true);
    onlineManager.setOnline(true);
    await opening;
  });
  it('keeps current read failures visible and allows an explicit retry', async () => {
    const error = new Error('current read failed');
    vi.mocked(getDept).mockRejectedValueOnce(error);
    const e = mountDialog();
    expect(await outcome(e.api.open({ deptId: 11 }))).toEqual({ error });
    expect(e.shell().props('okDisabled')).toBe(true);
    expect(await e.shell().props('confirm')({})).toBe(false);
    const retry = e.wrapper.findAll('button').find((button) => button.text() === '重试');
    expect(retry).toBeDefined();
    await retry!.trigger('click');
    await flushPromises();
    expect(e.model().deptName).toBe('Dept 11');
    expect(e.shell().props('okDisabled')).toBe(false);
  });
  it('keeps a later opening when a previous read completes last', async () => {
    const first = deferred<ReturnType<typeof detail>>(),
      second = deferred<ReturnType<typeof detail>>();
    vi.mocked(getDept).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const e = mountDialog();
    const old = outcome(e.api.open({ deptId: 11 }));
    await nextTick();
    const current = e.api.open({ deptId: 22 });
    second.resolve(detail(22));
    await current;
    first.resolve(detail(11));
    await old;
    expect(e.model().deptId).toBe(22);
    expect(e.shell().props('okDisabled')).toBe(false);
  });
  it.each(['create', 'edit'] as const)('%s sends only operation fields', async (mode) => {
    const e = mountDialog();
    await e.api.open(mode === 'edit' ? { deptId: 11 } : { parentId: 1 });
    Object.assign(e.model(), {
      deptName: 'Department',
      orderNum: 0,
      createBy: 'forged',
      updateTime: 'forged',
      delFlag: '2',
      ancestors: '0,999',
      admin: true,
    });
    await e.shell().props('confirm')(e.model());
    const payload = vi.mocked(mode === 'edit' ? updateDept : addDept).mock.calls[0][0];
    expect(payload).toMatchObject({ deptName: 'Department', orderNum: 0 });
    for (const field of ['createBy', 'updateTime', 'delFlag', 'ancestors', 'admin'])
      expect(payload).not.toHaveProperty(field);
    if (mode === 'edit') expect(payload).toHaveProperty('deptId', 11);
    else expect(payload).not.toHaveProperty('deptId');
  });
});
