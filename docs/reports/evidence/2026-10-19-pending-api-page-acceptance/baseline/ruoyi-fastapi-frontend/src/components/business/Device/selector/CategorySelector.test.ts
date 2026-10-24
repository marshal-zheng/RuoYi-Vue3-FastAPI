import { describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import CategorySelector from './CategorySelector.vue';
import { getDeviceCategoryOptions } from '@/api/device/category';

vi.mock('@/api/device/category', () => ({ getDeviceCategoryOptions: vi.fn() }));

describe('category options public API consumer', () => {
  it('consumes collection items without the obsolete business-type argument', async () => {
    vi.mocked(getDeviceCategoryOptions).mockResolvedValueOnce({
      items: [{ deviceCategoryId: 8, name: 'Network' }],
    });
    const wrapper = mount(CategorySelector, {
      global: {
        stubs: {
          ElSelect: { template: '<div><slot /></div>' },
          ElOption: { props: ['label', 'value'], template: '<div>{{ label }}:{{ value }}</div>' },
        },
      },
    });
    await flushPromises();
    expect(getDeviceCategoryOptions).toHaveBeenCalledExactlyOnceWith();
    expect(wrapper.text()).toContain('Network:Network');
    wrapper.unmount();
  });
});
