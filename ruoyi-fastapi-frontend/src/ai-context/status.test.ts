import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent, h, inject } from 'vue';
import { aiContextStatusKey } from '@zxio/zxui/ai-context';
import { getTextFieldAIStatus, type TextFieldAIStatus } from '@/api/system/textFieldAi';
import useUserStore from '@/store/modules/user';
import { reloadAIContextStatus, useAIContextStatusProvider } from './status';
import { manifestRevision } from './manifest-revision';

vi.mock('@/api/system/textFieldAi', () => ({ getTextFieldAIStatus: vi.fn() }));
const wire = (): TextFieldAIStatus => ({
  available: true,
  contract: 'ai-context/v1',
  manifestRevision,
  policyRevision: 'b'.repeat(64),
  providerClass: 'third-party',
  policy: { personal: 'mask', maxItems: 16, maxChars: 6000 },
});
const wrappers: ReturnType<typeof mount>[] = [];
function mountRoot() {
  const child = defineComponent({
    setup() {
      const status = inject(aiContextStatusKey)!;
      return () => h('output', status().state);
    },
  });
  const root = defineComponent({
    setup() {
      useAIContextStatusProvider();
      return () => h(child);
    },
  });
  const wrapper = mount(root, { global: { plugins: [createPinia()] } });
  wrappers.push(wrapper);
  return wrapper;
}
beforeEach(() => {
  vi.mocked(getTextFieldAIStatus).mockReset();
  setActivePinia(createPinia());
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
});

describe('application-root optional AI status', () => {
  it('does not request status before login and disables the policy on logout', async () => {
    const wrapper = mountRoot();
    const user = useUserStore();
    expect(wrapper.text()).toBe('unavailable');
    expect(getTextFieldAIStatus).not.toHaveBeenCalled();
    vi.mocked(getTextFieldAIStatus).mockResolvedValue(wire());
    user.token = 'synthetic-session';
    await flushPromises();
    expect(wrapper.text()).toBe('ready');
    expect(getTextFieldAIStatus).toHaveBeenCalledTimes(1);
    user.token = '';
    await flushPromises();
    expect(wrapper.text()).toBe('unavailable');
  });
  it.each([
    { available: false },
    { contract: 'other/v1' },
    { manifestRevision: 'a'.repeat(64) },
    { policyRevision: null },
    { policy: { personal: 'plain', maxItems: 16, maxChars: 6000 } },
    { policy: { personal: 'mask' } },
  ])('rejects unavailable, stale or malformed public policy (%j)', async (changes) => {
    vi.mocked(getTextFieldAIStatus).mockResolvedValue({
      ...wire(),
      ...changes,
    } as TextFieldAIStatus);
    const wrapper = mountRoot();
    useUserStore().token = 'synthetic-session';
    await flushPromises();
    expect(wrapper.text()).toBe('unavailable');
  });
  it('invalidates current policy while reloading and ignores an older response', async () => {
    const pending: ((value: TextFieldAIStatus) => void)[] = [];
    vi.mocked(getTextFieldAIStatus).mockImplementation(
      () => new Promise((resolve) => pending.push(resolve))
    );
    const wrapper = mountRoot();
    useUserStore().token = 'synthetic-session';
    await flushPromises();
    expect(wrapper.text()).toBe('loading');
    const reload = reloadAIContextStatus();
    await flushPromises();
    expect(vi.mocked(getTextFieldAIStatus).mock.calls[0][0]?.signal?.aborted).toBe(true);
    pending[0](wire());
    await flushPromises();
    expect(wrapper.text()).toBe('loading');
    pending[1]({ ...wire(), available: false });
    await reload;
    await flushPromises();
    expect(wrapper.text()).toBe('unavailable');
    expect(getTextFieldAIStatus).toHaveBeenCalledTimes(2);
  });
});
