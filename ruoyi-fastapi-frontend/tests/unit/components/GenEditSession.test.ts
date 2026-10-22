import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { defineComponent, getCurrentInstance, reactive, type ComponentCustomProperties } from 'vue';
import GenEdit from '@/views/tool/gen/editTable.vue';
import { mockRemark } from '@/mocks/data/remark';

const api = vi.hoisted(() => ({
  read: vi.fn(),
  write: vi.fn(),
  confirm: vi.fn(),
  close: vi.fn(),
  error: vi.fn(),
  leave: undefined as undefined | (() => Promise<boolean>),
  update: undefined as
    | undefined
    | ((
        to: { params: { tableId: string } },
        from: { params: { tableId: string } }
      ) => Promise<boolean>),
}));
const route = reactive({ params: { tableId: '1' }, query: {} });
vi.mock('vue-router', () => ({
  useRoute: () => route,
  onBeforeRouteLeave: (guard: typeof api.leave) => {
    api.leave = guard;
  },
  onBeforeRouteUpdate: (guard: typeof api.update) => {
    api.update = guard;
  },
}));
vi.mock('@/api/tool/gen', () => ({ getGenTable: api.read, updateGenTable: api.write }));
vi.mock('element-plus', async (original) => ({
  ...(await original<typeof import('element-plus')>()),
  ElMessage: { error: api.error },
  ElMessageBox: { confirm: api.confirm },
}));

const detail = (id = 1, comment = '服务端') => ({
  info: {
    tableId: id,
    tableName: `article_${id}`,
    tableComment: comment,
    className: 'Article',
    functionAuthor: 'author',
    remark: mockRemark('原备注', `gen${id}`),
    remarkText: '原备注',
  },
  columns: [],
  tables: [],
});
const basic = defineComponent({
  setup(_, { expose }) {
    expose({ basicInfoForm: { validate: (done: (valid: boolean) => void) => done(true) } });
    return () => null;
  },
});
const generation = defineComponent({
  setup(_, { expose }) {
    expose({
      $refs: { genInfoForm: { validate: (done: (valid: boolean) => void) => done(true) } },
    });
    return () => null;
  },
});
const slots = { template: '<div><slot /></div>' };
const mounted: ReturnType<typeof shallowMount>[] = [];
type State = {
  info: Record<string, unknown>;
  loaded: boolean;
  dirty: boolean;
  close: () => Promise<void>;
  submitForm: () => Promise<void>;
};
function page() {
  const wrapper = shallowMount(GenEdit, {
    global: {
      config: {
        globalProperties: {
          $tab: { closeOpenPage: api.close },
        } as unknown as ComponentCustomProperties,
      },
      stubs: {
        ElCard: slots,
        ElTabs: slots,
        ElTabPane: slots,
        BasicInfoForm: basic,
        GenInfoForm: generation,
        ElForm: slots,
        ElButton: slots,
        ElAlert: slots,
        ElTable: true,
        ElTableColumn: true,
      },
    },
  });
  mounted.push(wrapper);
  return { wrapper, state: (wrapper.vm.$ as unknown as { setupState: State }).setupState };
}
beforeEach(() => {
  vi.resetAllMocks();
  api.leave = undefined;
  api.update = undefined;
  route.params.tableId = '1';
  api.read.mockResolvedValue(detail());
  api.write.mockResolvedValue(detail());
  api.confirm.mockRejectedValue(new Error('继续编辑'));
  vi.stubGlobal('useRoute', () => route);
  vi.stubGlobal('getCurrentInstance', getCurrentInstance);
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  vi.unstubAllGlobals();
});

describe('generation table editing session', () => {
  it('fills without dirty and protects return and route replacement after a document edit', async () => {
    const { state } = page();
    await flushPromises();
    expect(state.dirty).toBe(false);
    state.info.remark = mockRemark('已修改😀', 'gendraft');
    await flushPromises();
    expect(state.dirty).toBe(true);
    await state.close();
    expect(api.close).not.toHaveBeenCalled();
    expect(await api.leave!()).toBe(false);
    expect(await api.update!({ params: { tableId: '2' } }, route)).toBe(false);
    expect(state.info.tableId).toBe(1);
    api.confirm.mockResolvedValueOnce(undefined);
    expect(await api.update!({ params: { tableId: '2' } }, route)).toBe(true);
  });
  it('keeps a failed save draft and blocks navigation while the write is pending', async () => {
    const { state } = page();
    await flushPromises();
    state.info.tableComment = '草稿';
    let reject!: (reason: Error) => void;
    api.write.mockImplementation(
      () =>
        new Promise((_resolve, no) => {
          reject = no;
        })
    );
    const save = state.submitForm();
    await flushPromises();
    expect(await api.leave!()).toBe(false);
    expect(api.confirm).not.toHaveBeenCalled();
    reject(new Error('保存失败'));
    await expect(save).rejects.toThrow('保存失败');
    expect(state.info.tableComment).toBe('草稿');
    expect(state.dirty).toBe(true);
    expect(api.close).not.toHaveBeenCalled();
  });
  it('uses one discard decision for the return button and its route guard only', async () => {
    const { state } = page();
    await flushPromises();
    state.info.tableComment = '未保存的返回草稿';
    api.confirm.mockResolvedValueOnce(undefined);
    let left: boolean | undefined;
    api.close.mockImplementation(async () => {
      left = await api.leave!();
    });
    await state.close();
    expect(left).toBe(true);
    expect(api.confirm).toHaveBeenCalledTimes(1);
    // A canceled destination navigation does not authorize a later attempt.
    expect(await api.leave!()).toBe(false);
    expect(api.confirm).toHaveBeenCalledTimes(2);
  });
  it('accepts authoritative saved values before leaving and clears the dirty baseline', async () => {
    const { state } = page();
    await flushPromises();
    state.info.tableComment = '提交文本';
    api.write.mockResolvedValueOnce(detail(1, '服务端规范文本'));
    await state.submitForm();
    await flushPromises();
    expect(state.info.tableComment).toBe('服务端规范文本');
    expect(state.dirty).toBe(false);
    expect(api.close).toHaveBeenCalledTimes(1);
    expect(await api.leave!()).toBe(true);
    expect(api.confirm).not.toHaveBeenCalled();
  });
});
