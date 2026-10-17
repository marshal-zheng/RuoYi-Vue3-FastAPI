import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue';

const { transport, feedback } = vi.hoisted(() => ({
  transport: vi.fn(),
  feedback: vi.fn(() => Promise.resolve()),
}));
vi.mock('@/utils/request', () => ({ default: transport }));
vi.mock('@/utils/feedback/message', () => ({ showMessage: feedback }));
vi.mock('@/components/business/Protocol/selector/ProtocolTypeSelector.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/EthernetProtocolTemplate.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/RS422ProtocolTemplate.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/CANProtocolTemplate.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
vi.mock('@/components/business/Protocol/templates/Protocol1553BTemplate.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
vi.mock('@/components/business/Protocol/ImportFileDialog.vue', () => ({
  default: { inheritAttrs: false, template: '<div />' },
}));
const shell = {
  name: 'ZxDrawer',
  inheritAttrs: false,
  props: ['confirm', 'okDisabled', 'modelValue', 'loading', 'formModel'],
  template: '<div><slot /></div>',
};
const stubs = Object.fromEntries(
  ['ElForm', 'ElFormItem', 'ZxInput', 'ElButton', 'ElAlert', 'ElTag'].map((name) => [
    name,
    { inheritAttrs: false, template: '<div><slot /></div>' },
  ])
);
function editor() {
  const save = vi.fn(() => Promise.resolve());
  const wrapper = mount(ProtocolFormDrawer, {
    props: { save },
    global: { stubs: { ...stubs, ZxDrawer: shell } },
  });
  const confirm = () => wrapper.findComponent(shell).props('confirm')({});
  return { wrapper, save, confirm };
}
beforeEach(() => vi.clearAllMocks());

describe('protocol edit identity', () => {
  it.each([new Error('HTTP 404'), { protocolId: 88 }, {}])(
    'does not allow an unsuccessful edit read to become a creation',
    async (failure) => {
      const { wrapper, save, confirm } = editor();
      try {
        if (failure instanceof Error) transport.mockRejectedValueOnce(failure);
        else transport.mockResolvedValueOnce(failure);
        await expect(wrapper.vm.open({ protocolId: 77 })).rejects.toBeDefined();
        expect(await confirm()).toBe(false);
        expect(save).not.toHaveBeenCalled();
      } finally {
        wrapper.unmount();
      }
    }
  );
  it('blocks saving when an edit draft loses its loaded identity', async () => {
    const { wrapper, save, confirm } = editor();
    try {
      transport.mockResolvedValueOnce({ protocolId: 77 });
      await wrapper.vm.open({ protocolId: 77 });
      const data = wrapper.findComponent(shell).props('formModel') as { protocolId?: number };
      data.protocolId = undefined;
      expect(await confirm()).toBe(false);
      expect(save).not.toHaveBeenCalled();
    } finally {
      wrapper.unmount();
    }
  });
  it('allows a successful edit and a later deliberate creation', async () => {
    const { wrapper, save, confirm } = editor();
    try {
      transport.mockResolvedValueOnce({
        protocolId: 77,
        protocolName: 'Protocol 77',
        protocolType: 'can',
      });
      await wrapper.vm.open({ protocolId: 77 });
      await confirm();
      expect(save).toHaveBeenLastCalledWith(expect.objectContaining({ protocolId: 77 }));
      await wrapper.vm.open();
      await confirm();
      expect(save).toHaveBeenLastCalledWith(expect.objectContaining({ protocolId: null }));
    } finally {
      wrapper.unmount();
    }
  });
});
