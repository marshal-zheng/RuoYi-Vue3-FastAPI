// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h, markRaw, nextTick, reactive, ref, type Component } from 'vue';
import {
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElTreeSelect,
  ElRadio,
  ElRadioGroup,
  type FormInstance,
} from 'element-plus';
import {
  aiContextStatusKey,
  provideAIContextScope,
  type AIContextStatus,
} from '@zxio/zxui/ai-context';
import { ZxSchemaForm, type SchemaFormInstance } from '@zxio/schema-form/formily';
import { ZxTextEditor } from '@zxio/text-editor';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { useAIContextHost } from '@/ai-context/host';
import { aiContextDefinitions } from '@/ai-context/definitions';
import { manifestRevision } from '@/ai-context/manifest-revision';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import {
  createPostSchema,
  initialPost,
  type PostValues,
} from '@/views/system/post/components/post-form';
import { mockRemark } from '@/mocks/data/remark';
import type { TextFieldAIRequest } from '@/api/system/textFieldAi';
import request from '@/utils/request';
import { VueQueryPlugin } from '@tanstack/vue-query';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import UserFormDialog from '@/views/system/user/components/UserFormDialog.vue';
import { getUser, deptTreeSelect } from '@/api/system/user';

vi.mock('@/api/system/user', () => ({
  getUser: vi.fn(),
  deptTreeSelect: vi.fn(),
  addUser: vi.fn(),
  updateUser: vi.fn(),
}));
vi.mock('@/utils/dict', () => ({ useDict: () => ({ sys_normal_disable: ref([]) }) }));
vi.mock('@/utils/request', () => ({ default: vi.fn() }));
const A = '13900000111',
  B = '13900000222',
  EMAIL_A = 'synthetic-a@example.test',
  EMAIL_B = 'synthetic-b@example.test';
const ready = (): AIContextStatus => ({
  state: 'ready',
  contract: 'ai-context/v1',
  manifestRevision,
  policyRevision: 'b'.repeat(64),
  policy: { personal: 'mask', providerClass: 'third-party', maxItems: 16, maxChars: 6000 },
});
let host: ReturnType<typeof createRemarkFieldTestHost>;
const outbound: TextFieldAIRequest[] = [];
const card = () => document.querySelector<HTMLElement>('.zx-field-ai');
const button = (id: string) => {
  const value = document.querySelector<HTMLButtonElement>(`[data-testid="${id}"]`);
  if (!value) throw new Error('Missing AI control: ' + id);
  return value;
};
const text = (doc: RemarkValue | null) => JSON.stringify(doc?.body.content ?? '');
function sse(body: TextFieldAIRequest, document: unknown, notices: unknown[] = []) {
  const event = {
    type: 'result',
    requestId: body.requestId,
    captureId: body.captureId,
    document,
    notices,
    meta: {
      promptVersion: 'text-field/v1',
      model: 'lan-model',
      contextIds: body.context.map((item) => item.id),
    },
  };
  return {
    status: 200,
    headers: { 'content-type': 'text/event-stream' },
    data: new Response(`event: message\ndata: ${JSON.stringify(event)}\n\n`).body!,
  };
}
function respond(
  project: (body: TextFieldAIRequest) => unknown = () => mockRemark('负责设备巡检。', 'ai')
) {
  vi.mocked(request).mockImplementation(async (config) => {
    const body = config.data as TextFieldAIRequest;
    outbound.push(structuredClone(body));
    return sse(body, readRemark(project(body)));
  });
}
async function open(wrapper: ReturnType<typeof mount>) {
  await wrapper.get('.zx-text-editor-field__ai').trigger('click');
  await flushPromises();
}
async function ask(instruction: string) {
  const input = card()?.querySelector<HTMLTextAreaElement>('textarea');
  if (!input) throw new Error('Missing AI composer');
  input.value = instruction;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  await nextTick();
  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  await flushPromises();
}
async function select(id: string) {
  const input = card()?.querySelector<HTMLInputElement>(`[data-context-id="${id}"]`);
  if (!input) throw new Error('Missing context choice ' + id);
  input.click();
  await flushPromises();
}
function userHost(initial: RemarkValue = null) {
  const form = reactive({
    deptName: '维护部',
    status: '0',
    phonenumber: A,
    email: EMAIL_A,
    remark: initial,
  });
  const session = ref(1),
    policy = ref(ready());
  const secret = vi.fn(() => {
    throw new Error('secret must never be read');
  });
  const phone = vi.fn(() => form.phonenumber),
    email = vi.fn(() => form.email);
  const component = defineComponent({
    setup() {
      useAIContextHost('user', {
        instanceKey: () => session.value,
        revisionSource: () => form,
        bindings: {
          deptName: { value: () => form.deptName },
          status: { value: () => (form.status === '0' ? '正常' : '停用') },
          phonenumber: { value: phone },
          email: { value: email },
          password: { value: secret },
        },
      });
      return () =>
        h(RemarkEditor, {
          key: session.value,
          modelValue: form.remark,
          'onUpdate:modelValue': (value: RemarkValue) => {
            form.remark = value;
          },
        });
    },
  });
  const wrapper = mount(component, {
    attachTo: document.body,
    global: {
      ...host.global,
      provide: { ...host.global.provide, [aiContextStatusKey as symbol]: () => policy.value },
    },
  });
  return { wrapper, form, session, policy, secret, phone, email };
}

const dialogStub = defineComponent({
  name: 'ZxDialog',
  inheritAttrs: false,
  props: ['formModel'],
  setup(_props, { slots }) {
    return () => h('section', slots.default?.());
  },
});
async function actualUserHost() {
  const policy = ref(ready());
  setQuerySession(1, [], []);
  vi.mocked(deptTreeSelect).mockResolvedValue({ items: [{ id: 1, label: '维护部' }] });
  vi.mocked(getUser).mockResolvedValue({
    data: {
      userId: 42,
      deptId: 1,
      dept: { deptId: 1, deptName: '维护部' },
      userName: 'synthetic-user',
      nickName: '合成用户',
      phonenumber: A,
      email: EMAIL_A,
      status: '0',
      remark: null,
      remarkText: '',
    },
    postIds: [1],
    roleIds: [1],
    posts: [{ postId: 1, postName: '巡检岗', status: '0', remarkText: '' }],
    roles: [{ roleId: 1, roleName: '维护角色', status: '0', remarkText: '' }],
  });
  const wrapper = mount(UserFormDialog, {
    attachTo: document.body,
    global: {
      ...host.global,
      plugins: [...host.global.plugins, [VueQueryPlugin, { queryClient }]],
      provide: { ...host.global.provide, [aiContextStatusKey as symbol]: () => policy.value },
      components: { ElForm, ElFormItem, ElSelect, ElOption, ElTreeSelect, ElRadio, ElRadioGroup },
      stubs: {
        ZxDialog: dialogStub,
        DictStatus: true,
        ZxInput: { props: ['modelValue'], template: '<input :value="modelValue" />' },
      },
    },
  });
  await (wrapper.vm as unknown as { open(id: number): Promise<void> }).open(42);
  await flushPromises();
  const form = wrapper.getComponent(dialogStub).props('formModel') as {
    phonenumber: string;
    email: string;
    remark: RemarkValue;
  };
  (form as typeof form & { password: string }).password = 'never-send-password';
  return { wrapper, form, policy };
}
beforeEach(() => {
  vi.mocked(request).mockReset();
  outbound.length = 0;
  host = createRemarkFieldTestHost('remark-ai-business');
  host.attach();
});
afterEach(() => {
  host.dispose();
  endQuerySession();
  queryClient.clear();
});

describe('business scope → real shared field → actual HTTP payload', () => {
  it('drafts, selects contacts, protects A/B through third round, adopts, reopens and blocks never', async () => {
    respond((body) => {
      const phone = body.context.find((item) => item.id === 'phonenumber')?.value;
      const email = body.context.find((item) => item.id === 'email')?.value;
      if (!phone) return readRemark(body.document) ?? mockRemark('负责设备巡检。', 'draft');
      const previous = body.candidate
        ? JSON.parse(JSON.stringify(body.candidate))
            .body.content.content[0].content.map((node: { text?: string }) => node.text ?? '')
            .join('')
        : '';
      return mockRemark(`${previous} 电话 ${phone} 邮箱 ${email}`, 'contacts');
    });
    const state = await actualUserHost();
    try {
      await flushPromises();
      await open(state.wrapper);
      await ask('根据表单写备注');
      expect(outbound[0].action).toBe('draft');
      expect(outbound[0].context.map((item) => item.id)).toEqual([
        'deptName',
        'postNames',
        'roleNames',
        'status',
      ]);
      expect(state.form.remark).toBeNull();
      await select('phonenumber');
      await select('email');
      await ask('把手机号和邮箱备注上');
      expect(card()!.textContent).toContain(A);
      expect(card()!.textContent).toContain(EMAIL_A);
      expect(card()!.querySelector('[data-testid="field-ai-receipt"]')!.textContent).toContain(
        '已脱敏'
      );
      state.form.phonenumber = B;
      state.form.email = EMAIL_B;
      await flushPromises();
      expect(card()!.querySelector('[data-testid="field-ai-accept"]')).toBeNull();
      await ask(`保留 ${A} 和 ${EMAIL_A}，补充当前联系方式`);
      expect(card()!.textContent).toContain(A);
      expect(card()!.textContent).toContain(B);
      expect(state.form.remark).toBeNull();
      button('field-ai-accept').click();
      await flushPromises();
      expect(text(state.form.remark)).toContain(A);
      expect(text(state.form.remark)).toContain(B);
      const editor = state.wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor.commands.undo();
      await flushPromises();
      expect(state.form.remark).toBeNull();
      editor.commands.redo();
      await flushPromises();
      await open(state.wrapper);
      await ask('再整理一次');
      expect(outbound).toHaveLength(4);
      expect(outbound[3].action).toBe('rewrite');
      expect(outbound[3].context).toEqual([]);
      for (const body of outbound)
        for (const secret of [A, B, EMAIL_A, EMAIL_B])
          expect(JSON.stringify(body)).not.toContain(secret);
      expect(JSON.stringify(outbound)).not.toContain('never-send-password');
      button('field-ai-discard').click();
      await flushPromises();
      state.policy.value = {
        ...ready(),
        policyRevision: 'c'.repeat(64),
        policy: { ...ready().policy!, personal: 'never' },
      };
      await flushPromises();
      await open(state.wrapper);
      await ask('继续改写');
      expect(outbound).toHaveLength(4);
      expect(card()!.querySelector('[role="alert"]')!.textContent).toContain('个人信息');
    } finally {
      state.wrapper.unmount();
    }
  });
  it('blocks a known personal value in a link before the actual request', async () => {
    respond((body) =>
      mockRemark(String(body.context.find((item) => item.id === 'phonenumber')?.value), 'phone')
    );
    const state = userHost();
    try {
      await flushPromises();
      await open(state.wrapper);
      await select('phonenumber');
      await ask('写联系方式');
      button('field-ai-accept').click();
      await flushPromises();
      const editor = state.wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor
        .chain()
        .selectAll()
        .setLink({ href: `tel:${A}` })
        .run();
      await flushPromises();
      await open(state.wrapper);
      await ask('改写');
      expect(outbound).toHaveLength(1);
      expect(card()!.querySelector('[role="alert"]')).not.toBeNull();
    } finally {
      state.wrapper.unmount();
    }
  });
  it('keeps ordinary editing available with AI unavailable', async () => {
    const state = userHost();
    state.policy.value = { ...ready(), state: 'unavailable', policy: null };
    try {
      await flushPromises();
      expect(state.wrapper.find('.zx-text-editor-field__ai').exists()).toBe(false);
      state.wrapper
        .findComponent(ZxTextEditor)
        .vm.$.exposed!.editor.value.commands.insertContent('手动编辑');
      await flushPromises();
      expect(text(state.form.remark)).toContain('手动编辑');
      expect(request).not.toHaveBeenCalled();
    } finally {
      state.wrapper.unmount();
    }
  });
  it('discards a late response after the edit instance is replaced', async () => {
    let resolve!: (value: ReturnType<typeof sse>) => void;
    let payload!: TextFieldAIRequest;
    let signal!: AbortSignal;
    vi.mocked(request).mockImplementation((config) => {
      payload = config.data as TextFieldAIRequest;
      signal = config.signal as AbortSignal;
      return new Promise((done) => {
        resolve = done;
      });
    });
    const state = userHost();
    try {
      await flushPromises();
      await open(state.wrapper);
      await ask('写备注');
      expect(signal.aborted).toBe(false);
      state.session.value++;
      await flushPromises();
      expect(signal.aborted).toBe(true);
      resolve(sse(payload, mockRemark('过期候选', 'late')));
      await flushPromises();
      expect(state.form.remark).toBeNull();
      expect(card()).toBeNull();
    } finally {
      state.wrapper.unmount();
    }
  });
  it('uses real Formily declarations and the formatted script binding without mirroring values', async () => {
    respond();
    const form = ref<SchemaFormInstance<PostValues>>();
    const authoring = createPostSchema(() => [
      { label: '正常', value: '0' },
      { label: '停用', value: '1' },
    ]);
    const parent = defineComponent({
      setup() {
        provideAIContextScope(aiContextDefinitions.post, {
          instanceKey: () => 1,
          revision: () => 0,
          bindings: {
            status: { value: () => (form.value?.read().status === '0' ? '正常' : '停用') },
          },
        });
        return () =>
          h(ZxSchemaForm as unknown as Component, {
            ref: form,
            initial: initialPost(),
            createSchema: authoring.createSchema,
            bindings: {
              RemarkEditor: { component: markRaw(RemarkEditor), composite: true, group: false },
            },
          });
      },
    });
    const wrapper = mount(parent, {
      attachTo: document.body,
      global: {
        ...host.global,
        provide: { ...host.global.provide, [aiContextStatusKey as symbol]: ready },
      },
    });
    try {
      await flushPromises();
      expect(form.value!.ready).toBe(true);
      form.value!.setValues({ postName: '设备维护员', postCode: 'maintenance', status: '1' });
      await flushPromises();
      await open(wrapper);
      await ask('写岗位备注');
      expect(outbound[0].scope).toBe('system.post');
      expect(outbound[0].context.map((item) => [item.id, item.value])).toEqual([
        ['postName', '设备维护员'],
        ['postCode', 'maintenance'],
        ['status', '停用'],
      ]);
      expect(form.value!.read().remark).toBeNull();
    } finally {
      wrapper.unmount();
    }
  });
  it('keeps pending review out of change/blur errors, blocks submit and clears errors after discard', async () => {
    respond();
    const model = reactive({ remark: readRemark(mockRemark('原始备注', 'original')) });
    const form = ref<FormInstance>();
    const nativeForm = defineComponent({
      setup() {
        useAIContextHost('user', {
          instanceKey: () => 1,
          revisionSource: () => model,
          bindings: {},
        });
        const { remarkRef, remarkRule } = useRemarkField();
        return () =>
          h('div', [
            h(ElForm, { ref: form, model, rules: { remark: [remarkRule] } }, () =>
              h(ElFormItem, { prop: 'remark' }, () =>
                h(RemarkEditor, {
                  ref: remarkRef,
                  modelValue: model.remark,
                  'onUpdate:modelValue': (value) => {
                    model.remark = value;
                  },
                })
              )
            ),
            h('button', { class: 'outside-field', type: 'button' }, '外部操作'),
          ]);
      },
    });
    const wrapper = mount(nativeForm, {
      attachTo: document.body,
      global: {
        ...host.global,
        provide: { ...host.global.provide, [aiContextStatusKey as symbol]: ready },
      },
    });
    try {
      await flushPromises();
      await open(wrapper);
      await ask('整理成要点');
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor.commands.insertContent('手动补充');
      editor.view.dom.focus();
      (wrapper.get('.outside-field').element as HTMLButtonElement).focus();
      await flushPromises();
      expect(card()!.querySelector('[role="alert"]')!.textContent).toContain('原文已变化');
      expect(wrapper.findComponent(ElFormItem).vm.validateState).not.toBe('error');
      expect(wrapper.find('.el-form-item__error').exists()).toBe(false);

      await expect(form.value!.validate()).rejects.toBeDefined();
      await vi.waitFor(() => expect(wrapper.find('.el-form-item__error').exists()).toBe(true));
      expect(wrapper.get('.el-form-item__error').text()).toContain('请完成备注编辑');

      button('field-ai-discard').click();
      await flushPromises();
      expect(card()).toBeNull();
      await vi.waitFor(() => expect(wrapper.find('.el-form-item__error').exists()).toBe(false));
      expect(editor.getText()).toContain('手动补充');
      await expect(form.value!.validate()).resolves.toBe(true);
    } finally {
      wrapper.unmount();
    }
  });
});
