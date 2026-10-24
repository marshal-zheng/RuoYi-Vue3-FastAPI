import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import { onlineManager, VueQueryPlugin } from '@tanstack/vue-query';
import { getDicts } from '@/api/system/dict/data';
import { useDict } from './dict';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { dictKeys } from '@/queries/system/dict';
import DictStatus from '@/components/business/DictStatus/index.vue';

vi.mock('@/api/system/dict/data', () => ({ getDicts: vi.fn() }));
vi.mock('@/api/system/dict/type', () => ({}));
const wrappers: ReturnType<typeof mount>[] = [];
function consumer() {
  const wrapper = mount(
    defineComponent({
      setup() {
        const { sys_normal_disable } = useDict('sys_normal_disable');
        return () =>
          h('div', [
            h('span', sys_normal_disable.value.map((item) => item.label).join(',')),
            h(DictStatus, { types: ['sys_normal_disable'] }),
          ]);
      },
    }),
    {
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: { ElButton: { template: '<button @click="$emit(\'click\')"><slot /></button>' } },
      },
    }
  );
  wrappers.push(wrapper);
  return wrapper;
}
beforeEach(() => {
  onlineManager.setOnline(true);
  endQuerySession();
  queryClient.clear();
  vi.mocked(getDicts).mockReset();
  setQuerySession(1, [], []);
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  onlineManager.setOnline(true);
});

describe('legacy dictionary aliases with a public state boundary', () => {
  it('shares data and reacts to later invalidation without a copied array', async () => {
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '正常', dictValue: '0' }] });
    const first = consumer();
    const second = consumer();
    await flushPromises();
    expect(getDicts).toHaveBeenCalledTimes(1);
    expect(first.text()).toContain('正常');
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '已更新', dictValue: '0' }] });
    await queryClient.invalidateQueries({ queryKey: dictKeys.all(setQuerySession(1, [], [])) });
    await flushPromises();
    expect(second.text()).toContain('已更新');
    consumer();
    await flushPromises();
    expect(getDicts).toHaveBeenCalledTimes(2);
  });

  it('presents an initial failure and read-only retry rather than successful empty data', async () => {
    vi.mocked(getDicts).mockRejectedValueOnce(new Error('offline'));
    const wrapper = consumer();
    await flushPromises();
    expect(wrapper.text()).toContain('字典加载失败');
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '恢复', dictValue: '0' }] });
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('恢复');
    expect(wrapper.text()).not.toContain('字典加载失败');
  });

  it('presents paused state and clears old-scope labels', async () => {
    onlineManager.setOnline(false);
    const wrapper = consumer();
    await flushPromises();
    expect(wrapper.text()).toContain('字典等待网络连接');
    onlineManager.setOnline(true);
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '旧账号标签', dictValue: '0' }] });
    await flushPromises();
    endQuerySession();
    await flushPromises();
    expect(wrapper.text()).not.toContain('旧账号标签');
  });
});
