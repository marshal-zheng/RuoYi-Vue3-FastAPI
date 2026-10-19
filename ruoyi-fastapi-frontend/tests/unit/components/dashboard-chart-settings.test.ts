import { expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { createDashboardPersistence } from '@zxio/dashboard/persistence';
import { createDashboardRegistry } from '@zxio/dashboard/widget';
import { createDashboardWidgets } from '@zxio/dashboard-widgets';
import TimeSeriesSettings from '@/components/business/Dashboard/TimeSeriesSettings.vue';
import { useTimeSeriesSettings } from '@/components/business/Dashboard/use-time-series-settings';
import { beginPanelSettings } from '@/components/business/Dashboard/panel-settings';
import type { DashboardDocument, DashboardJsonObject } from '@zxio/dashboard/schema';
import type { DashboardStoredDocument } from '@zxio/dashboard/persistence';

vi.mock('@zxio/zxui/input', async () => {
  const { defineComponent, h } = await import('vue');
  return {
    ZxInput: defineComponent({
      inheritAttrs: false,
      props: ['modelValue'],
      emits: ['update:modelValue'],
      setup:
        (props, { attrs, emit }) =>
        () =>
          h('input', {
            ...attrs,
            value: props.modelValue,
            onInput: (event: Event) =>
              emit('update:modelValue', (event.target as HTMLInputElement).value),
          }),
    }),
  };
});
const params = (): DashboardJsonObject => ({
  smooth: true,
  custom: { untouched: [1, 2] },
  chart: {
    title: { show: true, text: 'Original', sibling: 'keep' },
    legend: { show: true, position: 'bottom' },
    xAxis: { show: true },
    yAxis: { mode: 'fixed', min: 0, max: 100, name: '%', sibling: 9 },
  },
});
const document = (): DashboardDocument => ({
  schemaVersion: 2,
  panels: [
    {
      id: 'cpu',
      widget: 'zx.time-series',
      params: params(),
      gridPos: { x: 0, y: 0, w: 12, h: 8 },
    },
    {
      id: 'other',
      widget: 'zx.stat',
      params: { decimals: 2 },
      gridPos: { x: 12, y: 0, w: 12, h: 8 },
    },
  ],
});
const ElButton = {
  props: ['nativeType', 'disabled'],
  template: '<button :type="nativeType || \'button\'" :disabled="disabled"><slot /></button>',
};
const mountEditor = (save = vi.fn(async () => {})) =>
  mount(TimeSeriesSettings, {
    props: { params: params(), save },
    global: { stubs: { 'el-button': ElButton } },
  });
const labelled = (wrapper: ReturnType<typeof mountEditor>, text: string) => {
  const label = wrapper
    .findAll('label')
    .find((item) => item.text().replace('*', '').trim() === text)!;
  return wrapper
    .findAll('.zx-schema-field')
    .find((field) => field.element.contains(label.element))!
    .get('input, select');
};

it('preserves every unedited nested sibling and keeps raw invalid text outside JSON', () => {
  const initial = params();
  const before = JSON.stringify(initial);
  const editor = useTimeSeriesSettings(initial);
  editor.edit('title', 'text', 'Preview');
  editor.editNumber('min', '-');
  expect(editor.raw.value.min).toBe('-');
  expect(editor.valid.value).toBe(false);
  expect(editor.config.value.yAxis.min).toBe(0);
  editor.edit('yAxis', 'mode', 'auto');
  expect(editor.valid.value).toBe(true);
  expect(editor.draft.value).toMatchObject({
    custom: { untouched: [1, 2] },
    chart: {
      title: { text: 'Preview', sibling: 'keep' },
      yAxis: { min: 0, max: 100, sibling: 9 },
    },
  });
  editor.edit('yAxis', 'mode', 'fixed');
  expect(editor.valid.value).toBe(false);
  editor.editNumber('min', '-10');
  expect(editor.valid.value).toBe(true);
  expect(JSON.stringify(initial)).toBe(before);
});

it('previews valid nested edits, preserves hidden values and clears a cancelled session on remount', async () => {
  const wrapper = mountEditor();
  await labelled(wrapper, '图表标题').setValue('Live');
  expect(wrapper.emitted('preview')!.at(-1)![0]).toMatchObject({
    chart: { title: { text: 'Live' } },
  });
  await labelled(wrapper, '显示图表标题').setValue(false);
  expect(wrapper.findAll('label').some((item) => item.text() === '图表标题')).toBe(false);
  await labelled(wrapper, '显示图表标题').setValue(true);
  expect((labelled(wrapper, '图表标题').element as HTMLInputElement).value).toBe('Live');
  await labelled(wrapper, '最小值').setValue('1e');
  expect(labelled(wrapper, '最小值').attributes('aria-invalid')).toBe('true');
  await wrapper.get('button[type="button"]').trigger('click');
  expect(wrapper.emitted('cancel')).toHaveLength(1);
  wrapper.unmount();
  expect(wrapper.emitted('preview')!.at(-1)).toEqual([undefined]);
  const next = mountEditor();
  expect((labelled(next, '图表标题').element as HTMLInputElement).value).toBe('Original');
  expect((labelled(next, '最小值').element as HTMLInputElement).value).toBe('0');
  expect(next.find('[aria-invalid="true"]').exists()).toBe(false);
  next.unmount();
});

it('keeps draft on failure and retries the same candidate; blocks repeated submissions', async () => {
  let finish!: () => void;
  const save = vi
    .fn()
    .mockRejectedValueOnce(new Error('offline'))
    .mockImplementationOnce(
      () =>
        new Promise<void>((done) => {
          finish = done;
        })
    );
  const wrapper = mountEditor(save);
  await labelled(wrapper, '图表标题').setValue('Retry me');
  await wrapper.get('form').trigger('submit');
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toBe('offline');
  expect((labelled(wrapper, '图表标题').element as HTMLInputElement).value).toBe('Retry me');
  await wrapper.get('form').trigger('submit');
  await wrapper.get('form').trigger('submit');
  expect(save).toHaveBeenCalledTimes(2);
  expect(save.mock.calls[0][0]).toEqual(save.mock.calls[1][0]);
  finish();
  await flushPromises();
  expect(wrapper.emitted('saved')).toHaveLength(1);
  wrapper.unmount();
});

it('saves a candidate atomically, retains other panels, and rejects stale panel sessions', async () => {
  let remote: DashboardStoredDocument = { document: document(), revision: 1 };
  const save = vi.fn(async (_key: string, next: DashboardDocument) => {
    remote = { document: next, revision: remote.revision + 1 };
    return { status: 'saved' as const, snapshot: remote };
  });
  const persistence = createDashboardPersistence({
    key: 'cpu',
    adapter: {
      load: async () => remote,
      save,
      remove: async () => ({ status: 'removed' }),
    },
  });
  await persistence.load();
  const registry = createDashboardRegistry();
  registry.use(createDashboardWidgets({ themeProjection: undefined }));
  const current = () => persistence.getState().document!;
  const session = beginPanelSettings(persistence, current, registry, 'cpu');
  const next = params();
  next.chart = { title: { show: true, text: 'Saved' } };
  save.mockRejectedValueOnce(new Error('network'));
  await expect(session.save(next)).rejects.toThrow('network');
  expect(current()).toEqual(document());
  await session.save(next);
  expect(current().panels[0].params).toEqual(next);
  expect(current().panels[1]).toEqual(document().panels[1]);
  await expect(session.save(params())).rejects.toThrow('版本已变化');
  const stale = beginPanelSettings(persistence, current, registry, 'cpu');
  const changed = current();
  changed.panels[0].params = params();
  persistence.setDocument(changed);
  await expect(stale.save(next)).rejects.toThrow('版本已变化');
  persistence.dispose();
});
