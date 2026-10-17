import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import * as Vue from 'vue';
import MenuDrawer from '@/views/system/menu/components/MenuDrawer.vue';
import NoticeDlg from '@/views/system/notice/components/NoticeDlg.vue';
import PostDlg from '@/views/system/post/components/PostDlg.vue';
import ProjectDlg from '@/views/system/project/components/ProjectDlg.vue';
import ProjectFormDialog from '@/views/project/components/ProjectFormDialog.vue';
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue';
import DictData from '@/views/system/dict/data.vue';
import { setQuerySession, endQuerySession } from '@/queries/context';

const api = vi.hoisted(() => ({
  menu: vi.fn(),
  tree: vi.fn(),
  notice: vi.fn(),
  post: vi.fn(),
  project: vi.fn(),
  projectMain: vi.fn(),
  protocol: vi.fn(),
  dictData: vi.fn(),
  write: vi.fn(),
  error: vi.fn(),
  recovery: vi.fn(),
}));
vi.mock('@/api/system/menu', () => ({
  getMenu: api.menu,
  treeselect: api.tree,
  addMenu: api.write,
  updateMenu: api.write,
}));
vi.mock('@/api/system/notice', () => ({
  getNotice: api.notice,
  addNotice: api.write,
  updateNotice: api.write,
}));
vi.mock('@/api/system/post', () => ({
  getPost: api.post,
  addPost: api.write,
  updatePost: api.write,
}));
vi.mock('@/api/system/project', () => ({
  getProject: api.project,
  addProject: api.write,
  updateProject: api.write,
}));
vi.mock('@/api/project/project', () => ({
  getProject: api.projectMain,
  addProject: api.write,
  updateProject: api.write,
}));
vi.mock('@/api/protocol/protocol', () => ({ getProtocol: api.protocol }));
vi.mock('@/api/system/dict/data', () => ({
  getData: api.dictData,
  listData: vi.fn(),
  delData: vi.fn(),
  addData: api.write,
  updateData: api.write,
}));
vi.mock('@/api/system/dict/type', () => ({
  getType: () => Promise.resolve({ dictType: 'test_type' }),
  optionselect: () => Promise.resolve({ items: [] }),
}));
vi.mock('vue-router', () => ({ useRoute: () => ({ params: { dictId: 1 } }) }));
vi.mock('@/utils/http', () => ({ presentRequestError: api.recovery }));
vi.mock('element-plus', () => ({ ElMessage: { error: api.error } }));
vi.mock('@/utils/feedback/presenter', () => ({
  presentProblemFeedback: api.error,
  resolveFeedbackOptions: (v: unknown) => v,
}));
vi.mock('@/utils/dict', () => ({
  useDict: () => ({ sys_normal_disable: [], sys_notice_status: [], sys_notice_type: [] }),
}));
vi.mock('@/components/ui/IconSelect/index.vue', () => ({ default: { template: '<div />' } }));
vi.mock('@/components/business/Protocol/selector/ProtocolTypeSelector.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/EthernetProtocolTemplate.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/RS422ProtocolTemplate.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/CANProtocolTemplate.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/Protocol1553BTemplate.vue', () => ({
  default: { template: '<div />' },
}));
vi.mock('@/components/business/Protocol/ImportFileDialog.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
const slot = { inheritAttrs: false, template: '<div><slot /></div>' };
const shell = Vue.defineComponent({
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
    return () => Vue.h('section', [slots.default?.(), slots.footer?.()]);
  },
});
const detail = (id: number, text = `Record ${id}`) => ({
  menuId: id,
  menuName: text,
  parentId: 1,
  menuType: 'F',
  orderNum: 0,
  noticeId: id,
  noticeTitle: text,
  noticeType: '1',
  noticeContent: '<p>Content</p>',
  postId: id,
  postName: text,
  postCode: `post_${id}`,
  postSort: 1,
  projectId: id,
  projectName: text,
  projectDesc: text,
  protocolId: id,
  protocolName: text,
  protocolType: '',
  protocolConfig: { fields: [{ name: 'data' }] },
  dictCode: id,
  dictType: 'test_type',
  dictLabel: text,
  dictValue: String(id),
  dictSort: 0,
  status: '0',
  data: { userId: id, nickName: text },
  posts: [],
  roles: [],
  postIds: [id],
  roleIds: [id],
});
function deferred<T = ReturnType<typeof detail>>() {
  let resolve!: (v: T) => void, reject!: (e: unknown) => void;
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}
// Query-backed user openings have their native shared-read suite in UserFormDialog.test.ts.
const cases = [
  {
    name: 'menu',
    component: MenuDrawer,
    read: api.menu,
    id: 'menuId',
    field: 'menuName',
    arg: (id?: number) => (id ? { menuId: id } : { parentId: 1 }),
  },
  {
    name: 'notice',
    component: NoticeDlg,
    read: api.notice,
    id: 'noticeId',
    field: 'noticeTitle',
    arg: (id?: number) => id,
  },
  {
    name: 'post',
    component: PostDlg,
    read: api.post,
    id: 'postId',
    field: 'postName',
    arg: (id?: number) => id,
  },
  {
    name: 'system project',
    component: ProjectDlg,
    read: api.project,
    id: 'projectId',
    field: 'projectDesc',
    arg: (id?: number) => id,
  },
  {
    name: 'project',
    component: ProjectFormDialog,
    read: api.projectMain,
    id: 'projectId',
    field: 'projectName',
    arg: (id?: number) => id,
  },
  {
    name: 'protocol',
    component: ProtocolFormDrawer,
    read: api.protocol,
    id: 'protocolId',
    field: 'protocolName',
    arg: (id?: number) => (id ? { protocolId: id } : undefined),
  },
  {
    name: 'dict data',
    component: DictData,
    read: api.dictData,
    id: 'dictCode',
    field: 'dictLabel',
    arg: (id?: number) => (id ? { dictCode: id } : undefined),
  },
];
const mounted: ReturnType<typeof mount>[] = [];
const queryClients: QueryClient[] = [];
function editor(item: (typeof cases)[number]) {
  const queryClient = new QueryClient();
  queryClients.push(queryClient);
  const wrapper = mount(item.component as Vue.Component, {
    props: item.name === 'protocol' ? { save: api.write } : {},
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      config: {
        globalProperties: {
          useDict: () => ({ sys_normal_disable: [] }),
          resetForm: vi.fn(),
        } as unknown as Vue.ComponentCustomProperties,
      },
      directives: { hasPermi: () => {}, loading: () => {} },
      stubs: {
        DictStatus: true,
        DictSelect: true,
        ZxDialog: shell,
        ZxDrawer: shell,
        ElForm: Vue.defineComponent({
          ...slot,
          setup(_, { expose }) {
            expose({ validate: () => Promise.resolve(true) });
          },
        }),
        ElFormItem: slot,
        FormGrid: slot,
        ElAlert: { props: ['title'], template: '<aside><slot /></aside>' },
        ElButton: {
          props: ['disabled'],
          template: '<button :disabled="disabled"><slot /></button>',
        },
        ZxInput: true,
        ElTreeSelect: {
          name: 'ElTreeSelect',
          props: ['data'],
          inheritAttrs: false,
          template: '<div />',
        },
        ElSelect: slot,
        ElOption: true,
        ElRadioGroup: slot,
        ElRadio: true,
        ElInputNumber: true,
        ElTooltip: slot,
        ElIcon: slot,
        ElPopover: slot,
        QuestionFilled: true,
        Search: true,
        SvgIcon: true,
        DictTag: true,
        Editor: true,
        ElTag: true,
        ZxContentWrap: true,
        ZxGridList: true,
        ZxButton: true,
        ZxListToolbar: true,
        ZxSearch: true,
        ElTable: true,
        ElTableColumn: true,
      },
    },
  });
  mounted.push(wrapper);
  const setup = (
    wrapper.vm.$ as unknown as {
      setupState: {
        openEditor: (id?: number) => Promise<void>;
        submitForm: () => Promise<unknown>;
      };
    }
  ).setupState;
  const exposed = wrapper.vm as unknown as {
    open: (id?: unknown) => Promise<void>;
    close: () => Promise<void>;
  };
  const modal = () => wrapper.findComponent(shell);
  return {
    wrapper,
    modal,
    open: (id?: number) =>
      item.name === 'dict data' ? setup.openEditor(id) : exposed.open(item.arg(id)),
    model: () => modal().props('formModel') as Record<string, unknown>,
    confirm: () =>
      item.name === 'dict data'
        ? setup.submitForm()
        : modal().props('confirm')(modal().props('formModel')),
  };
}
const outcome = <T>(p: Promise<T>) =>
  p.then(
    (value) => ({ value }),
    (error) => ({ error })
  );
beforeEach(() => {
  setQuerySession(1, [], []);
  vi.resetAllMocks();
  cases.forEach((item) => item.read.mockImplementation(async (id) => detail(id)));
  api.tree.mockResolvedValue({ items: [] });
});
afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount());
  queryClients.splice(0).forEach((client) => client.clear());
  vi.unstubAllGlobals();
  endQuerySession();
});
for (const item of cases)
  describe(`${item.name} opening ownership`, () => {
    it('opens immediately and keeps the latest response when older success arrives last', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item),
        first = e.open(11);
      await Vue.nextTick();
      expect(e.modal().props('modelValue')).toBe(true);
      expect(e.modal().props('loading')).toBe(true);
      expect(await e.confirm()).toBe(false);
      expect(api.write).not.toHaveBeenCalled();
      const second = e.open(22);
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      b.resolve(detail(22));
      await second;
      a.resolve(detail(11));
      await first;
      await Vue.nextTick();
      expect(e.model()[item.id]).toBe(22);
      expect(e.model()[item.field]).toBe('Record 22');
      expect(e.modal().props('loading')).toBe(false);
      expect(e.modal().props('okDisabled')).toBe(false);
    });
    it('ignores old failure and old finally while the new opening is pending', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item),
        old = outcome(e.open(11)),
        current = e.open(22);
      a.reject(new Error('old error'));
      await old;
      await Vue.nextTick();
      expect(e.modal().props('loading')).toBe(true);
      expect(e.modal().props('okDisabled')).toBe(true);
      expect(api.error).not.toHaveBeenCalled();
      b.resolve(detail(22));
      await current;
    });
    it('cancels a closed opening and isolates a reopen of the same ID', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item),
        old = e.open(11);
      await Vue.nextTick();
      e.modal().vm.$emit('update:modelValue', false);
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      const current = e.open(11);
      a.resolve(detail(11, 'Old'));
      await old;
      await Vue.nextTick();
      expect(e.modal().props('loading')).toBe(true);
      expect(e.model()[item.field]).toBeFalsy();
      b.resolve(detail(11, 'Reopened'));
      await current;
      expect(e.model()[item.field]).toBe('Reopened');
    });
    it('retains an intentional create draft after the previous edit completes', async () => {
      const a = deferred();
      item.read.mockReturnValueOnce(a.promise);
      const e = editor(item);
      await flushPromises();
      const old = e.open(11);
      await e.open();
      a.resolve(detail(11));
      await old;
      expect(e.model()[item.id] == null).toBe(true);
      expect(e.model()[item.field]).toBeFalsy();
      expect(e.modal().props('okDisabled')).toBe(false);
      if (item.name === 'menu') expect(e.model().parentId).toBe(1);
      if (item.name === 'dict data') expect(e.model().dictType).toBe('test_type');
    });
    it('blocks failed edits and retries the original ID', async () => {
      const failure = new Error('current failed');
      item.read.mockRejectedValueOnce(failure);
      const e = editor(item);
      expect(await outcome(e.open(11))).toEqual({ error: failure });
      await Vue.nextTick();
      expect(e.modal().props('okDisabled')).toBe(true);
      expect(await e.confirm()).toBe(false);
      expect(api.write).not.toHaveBeenCalled();
      expect(api.error).toHaveBeenCalledExactlyOnceWith(failure.message);
      const retry = e.wrapper.findAll('button').find((b) => b.text() === '重试');
      expect(retry).toBeDefined();
      await retry!.trigger('click');
      await flushPromises();
      expect(e.model()[item.id]).toBe(11);
      expect(e.modal().props('okDisabled')).toBe(false);
    });
    it('aborts at scope disposal without consuming late success', async () => {
      const a = deferred();
      item.read.mockReturnValueOnce(a.promise);
      const e = editor(item),
        old = e.open(11);
      e.wrapper.unmount();
      expect(item.read.mock.calls[0][1]?.signal.aborted).toBe(true);
      a.resolve(detail(11));
      await old;
      expect(api.error).not.toHaveBeenCalled();
    });
    it('restores current 401 recovery and keeps stale 401 silent', async () => {
      const a = deferred(),
        b = deferred();
      item.read.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
      const e = editor(item),
        old = outcome(e.open(11)),
        current = outcome(e.open(22));
      const failure = Object.assign(new Error('expired'), {
        problem: { status: 401 },
        meta: { status: 401 },
        config: { silentError: true },
      });
      a.reject(failure);
      await old;
      expect(api.recovery).not.toHaveBeenCalled();
      b.reject(failure);
      await current;
      expect(api.recovery).toHaveBeenCalledExactlyOnceWith(
        failure,
        expect.objectContaining({ silentError: false, feedback: { mode: 'auto' } })
      );
      expect(failure.config.silentError).toBe(true);
    });
  });
it('owns menu options together with the detail and preserves root creation', async () => {
  const a = deferred<{ items: { id: number; label: string }[] }>(),
    b = deferred<{ items: { id: number; label: string }[] }>();
  api.tree.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
  const e = editor(cases[0]);
  const old = e.open(11),
    current = e.open(22);
  b.resolve({ items: [{ id: 22, label: 'Current' }] });
  await current;
  a.resolve({ items: [{ id: 11, label: 'Old' }] });
  await old;
  expect(e.wrapper.findComponent({ name: 'ElTreeSelect' }).props('data')).toEqual([
    { id: 0, label: '主类目', children: [{ id: 22, label: 'Current' }] },
  ]);
  await (e.wrapper.vm as unknown as { open: () => Promise<void> }).open();
  expect(e.model().parentId).toBe(0);
  expect(e.modal().props('okDisabled')).toBe(false);
});
