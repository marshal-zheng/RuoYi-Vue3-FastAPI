import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Cache from './index.vue';
import type { App, ShallowRef } from 'vue';
import type { useZxChartThemeProjection } from '@zxio/zxui';
import modal from '@/plugins/modal';

type ProjectionFixture = { ok: true; value: { identity: string } } | { ok: false };
type ProjectionInput = Parameters<typeof useZxChartThemeProjection>[0];

const state: {
  getCache: ReturnType<typeof vi.fn>;
  projection?: ShallowRef<ProjectionFixture>;
  resolveManifest?: ProjectionInput['resolveManifest'];
} = vi.hoisted(() => ({
  getCache: vi.fn(),
  projection: undefined,
  resolveManifest: undefined,
}));

vi.mock('@/api/monitor/cache', () => ({ getCache: state.getCache }));
vi.mock('@zxio/chart/style', () => ({}));
vi.mock('virtual:zxui-theme-deployment', () => ({
  default: {
    registrations: [{ manifest: { identity: { themeId: 'default' } } }],
  },
}));
vi.mock('@zxio/zxui', async () => {
  const { shallowRef } = await import('vue');
  state.projection = shallowRef<ProjectionFixture>({ ok: true, value: { identity: 'light' } });
  return {
    useZxChartThemeProjection: (input: ProjectionInput) => {
      state.resolveManifest = input.resolveManifest;
      return state.projection;
    },
  };
});
vi.mock('@zxio/chart', async () => {
  const { defineComponent, h } = await import('vue');
  return {
    ZxChart: defineComponent({
      name: 'ZxChart',
      props: ['options', 'themeProjection', 'height'],
      setup: () => () => h('div', { 'data-test': 'chart' }),
    }),
  };
});

describe('cache monitor chart theme integration', () => {
  beforeEach(() => {
    state.projection!.value = { ok: true, value: { identity: 'light' } };
    state.getCache.mockResolvedValue({
      info: { used_memory_human: '12M', used_cpu_user_children: '1.2' },
      commandStats: [{ name: 'get', value: 4 }],
    });
  });

  it('preserves chart data while updating both projections without another request', async () => {
    const loading = vi.fn();
    const closeLoading = vi.fn();
    const wrapper = mount(Cache, {
      global: {
        plugins: [
          {
            install(app: App) {
              app.config.globalProperties.$modal = { ...modal, loading, closeLoading };
            },
          },
        ],
        stubs: {
          ElRow: { template: '<div><slot /></div>' },
          ElCol: { template: '<div><slot /></div>' },
          ElCard: { template: '<div><slot /></div>' },
          Monitor: true,
          PieChart: true,
          Odometer: true,
        },
      },
    });
    await flushPromises();
    const charts = wrapper.findAllComponents({ name: 'ZxChart' });
    expect(charts).toHaveLength(2);
    expect(charts[0].props('options').series[0]).toMatchObject({
      type: 'pie',
      roseType: 'radius',
      data: [{ name: 'get', value: 4 }],
      animationDuration: 1000,
    });
    expect(charts[1].props('options').series[0]).toMatchObject({
      type: 'gauge',
      max: 1000,
      detail: { formatter: '12M' },
      data: [{ value: 12, name: '内存消耗' }],
    });
    expect(state.resolveManifest!('default')).toEqual({
      identity: { themeId: 'default' },
    });
    const options = charts.map((chart) => chart.props('options'));
    state.projection!.value = { ok: true, value: { identity: 'dark' } };
    await flushPromises();
    for (const [index, chart] of charts.entries()) {
      expect(chart.props('themeProjection')).toEqual({ identity: 'dark' });
      expect(chart.props('options')).toBe(options[index]);
    }
    expect(state.getCache).toHaveBeenCalledTimes(1);
    expect(closeLoading).toHaveBeenCalledTimes(1);
    state.projection!.value = { ok: false };
    await flushPromises();
    expect(wrapper.findAllComponents({ name: 'ZxChart' })).toHaveLength(0);
    wrapper.unmount();
  });
});
