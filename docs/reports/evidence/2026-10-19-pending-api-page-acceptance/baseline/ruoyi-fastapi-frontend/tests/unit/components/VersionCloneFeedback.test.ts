import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import VersionCloneDialog from '@/views/project/components/VersionCloneDialog.vue';

const api = vi.hoisted(() => ({ clone: vi.fn(), recover: vi.fn() }));
vi.mock('@/api/project/version', () => ({ cloneProjectVersion: api.clone }));
vi.mock('@/utils/http', () => ({ presentRequestError: api.recover }));
let wrapper: ReturnType<typeof mount>;
function editor() {
  wrapper = mount(VersionCloneDialog, {
    global: {
      stubs: {
        ZxDialog: {
          name: 'ZxDialog',
          inheritAttrs: false,
          props: ['modelValue', 'formModel', 'confirm'],
          template: '<section><slot /></section>',
        },
        ElForm: { inheritAttrs: false, template: '<form><slot /></form>' },
        ElFormItem: true,
        ElAlert: { props: ['title'], template: '<aside>{{ title }}</aside>' },
        ZxInput: true,
      },
    },
  });
  const exposed = wrapper.vm as unknown as {
    open: (row: object, callback?: () => void) => void;
    close: () => void;
  };
  const modal = () => wrapper.findComponent({ name: 'ZxDialog' });
  return { exposed, modal, confirm: () => modal().props('confirm')() as Promise<boolean> };
}
beforeEach(() => vi.resetAllMocks());
afterEach(() => wrapper?.unmount());
describe('version clone feedback ownership', () => {
  it('keeps a conflict inline and leaves the editor open', async () => {
    const e = editor();
    e.exposed.open({ versionId: 14, versionName: 'QA' });
    await flushPromises();
    api.clone.mockRejectedValue({ problem: { status: 409, detail: '版本号已存在' } });
    expect(await e.confirm()).toBe(false);
    expect(api.clone).toHaveBeenCalledWith(expect.objectContaining({ sourceVersionId: 14 }), {
      silentError: true,
    });
    expect(wrapper.get('aside').text()).toBe('版本号已存在');
    expect(e.modal().props('modelValue')).toBe(true);
    expect(api.recover).not.toHaveBeenCalled();
  });
  it('does not apply an earlier success to a reopened editor', async () => {
    const e = editor();
    const first = vi.fn();
    const second = vi.fn();
    e.exposed.open({ versionId: 14 }, first);
    await flushPromises();
    let resolve!: (value: object) => void;
    api.clone.mockReturnValue(
      new Promise((yes) => {
        resolve = yes;
      })
    );
    const pending = e.confirm();
    e.modal().vm.$emit('update:modelValue', false);
    e.exposed.open({ versionId: 16 }, second);
    resolve({ versionId: 20 });
    expect(await pending).toBe(false);
    expect(first).not.toHaveBeenCalled();
    expect(second).not.toHaveBeenCalled();
    expect(e.modal().props('formModel').sourceVersionId).toBe(16);
  });
  it('preserves the authentication recovery prompt', async () => {
    const e = editor();
    e.exposed.open({ versionId: 14 });
    await flushPromises();
    const error = { problem: { status: 401, detail: '会话已过期' } };
    api.clone.mockRejectedValue(error);
    expect(await e.confirm()).toBe(false);
    expect(api.recover).toHaveBeenCalledWith(error, {
      silentError: false,
      feedback: { mode: 'auto' },
    });
  });
});
