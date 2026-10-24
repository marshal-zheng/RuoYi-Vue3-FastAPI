<template>
  <PersistentDashboard
    ref="dashboard"
    scope="scene"
    :storage-key="String(projectId)"
    title="仿真监控面板"
    :initial-document="initialDocument"
    :registry="registry"
    :editable="!readonly && checkPermi(['project:project:edit'])"
    @document-change="syncVisibility"
  />
</template>

<script setup>
import { ref, watch, markRaw } from 'vue';
import './panel-content.css';
import { createDashboardRegistry } from '@zxio/dashboard/widget';
import PersistentDashboard from '@/components/business/Dashboard/PersistentDashboard.vue';
import { checkPermi } from '@/utils/permission';
import BandwidthChartPanel from '../components/BandwidthChartPanel.vue';
import AlarmDashboardPanel from '../components/AlarmDashboardPanel.vue';
import TimingLatencyPanel from '../components/TimingLatencyPanel.vue';
import FaultBoardPanel from '../components/FaultBoardPanel.vue';
import DataInjectionPanel from '../components/DataInjectionPanel.vue';

const props = defineProps({
  projectId: { type: Number, required: true },
  dockState: { type: Object, required: true },
  bandwidthData: { type: Array, default: () => [] },
  alarms: { type: Array, default: () => [] },
  messages: { type: Array, default: () => [] },
  running: Boolean,
  speed: { type: Number, default: 1 },
  readonly: Boolean,
  faults: { type: Array, default: () => [] },
  faultsLoading: Boolean,
  selectedEdge: { type: Object, default: null },
  hoveredEdge: { type: Object, default: null },
  injectionStrategy: { type: Object, required: true },
});
const emit = defineEmits([
  'visibility-change',
  'alarm-click',
  'apply-template',
  'clear',
  'clear-all',
  'refresh',
  'close-fault',
  'apply-injection',
]);
const dashboard = ref();
const bandwidth = ref();
// The draft survives hiding a panel, but is never serialized as dashboard geometry.
const injectionDraft = ref({
  strategy: props.injectionStrategy.strategy,
  params: { ...props.injectionStrategy.params },
});
const definitions = [
  {
    id: 'bandwidth',
    title: '带宽监控',
    component: BandwidthChartPanel,
    resolveProps: () => ({
      ref: (instance) => {
        bandwidth.value = instance;
      },
      bandwidthData: props.bandwidthData,
      running: props.running,
      speed: props.speed,
      resetOnStop: true,
    }),
  },
  {
    id: 'alarm',
    title: '告警',
    component: AlarmDashboardPanel,
    resolveProps: () => ({
      alarms: props.alarms,
      onAlarmClick: (alarm) => emit('alarm-click', alarm),
    }),
  },
  {
    id: 'timing',
    title: '时序 / 延迟分析',
    component: TimingLatencyPanel,
    resolveProps: () => ({
      messages: props.messages,
      bandwidthData: props.bandwidthData,
    }),
  },
  {
    id: 'fault',
    title: '故障板',
    component: FaultBoardPanel,
    resolveProps: () => ({
      faults: props.faults,
      loading: props.faultsLoading,
      selectedEdge: props.selectedEdge,
      hoveredEdge: props.hoveredEdge,
      isRunning: props.running,
      onApplyTemplate: (template) => emit('apply-template', template),
      onClear: (fault) => emit('clear', fault),
      onClearAll: () => emit('clear-all'),
      onRefresh: () => emit('refresh'),
      onClose: () => emit('close-fault'),
    }),
  },
  {
    id: 'injection',
    title: '数据注入策略',
    component: DataInjectionPanel,
    resolveProps: () => ({
      initialConfig: injectionDraft.value,
      onConfigChange: (config) => {
        injectionDraft.value = config;
      },
      onApply: (config) => emit('apply-injection', config),
    }),
  },
];
const registry = createDashboardRegistry();
for (const definition of definitions)
  registry.register({
    name: `simulation.${definition.id}`,
    title: definition.title,
    component: markRaw(definition.component),
    resolveProps: definition.resolveProps,
    version: '1.0.0',
    minGrid: { w: 12, h: 7 },
    defaultGrid: { w: 24, h: 10 },
  });
const initialDocument = {
  schemaVersion: 2,
  uid: `simulation-${props.projectId}`,
  title: '仿真监控',
  pluginVersions: Object.fromEntries(definitions.map(({ id }) => [`simulation.${id}`, '1.0.0'])),
  panels: definitions.map(({ id, title }, i) => ({
    id,
    title,
    widget: `simulation.${id}`,
    gridPos: { x: 0, y: i * 10, w: 24, h: 10 },
    metadata: { layout: { hidden: !props.dockState[id] } },
  })),
};
function syncVisibility(document) {
  emit(
    'visibility-change',
    Object.fromEntries(
      definitions.map(({ id }) => {
        const panel = document.panels.find((item) => item.id === id);
        return [id, !!panel && panel.metadata?.layout?.hidden !== true];
      })
    )
  );
}
watch(
  () => ({ ...props.dockState }),
  (visibility) => {
    const document = dashboard.value?.getDocument();
    if (!document) return;
    let changed = false;
    const panels = document.panels.map((panel) => {
      if (
        !(panel.id in visibility) ||
        (panel.metadata?.layout?.hidden !== true) === visibility[panel.id]
      )
        return panel;
      changed = true;
      return {
        ...panel,
        metadata: {
          ...panel.metadata,
          layout: { ...panel.metadata?.layout, hidden: !visibility[panel.id] },
        },
      };
    });
    if (changed) dashboard.value.update({ ...document, panels });
  }
);
defineExpose({
  stepScanline: () => bandwidth.value?.stepScanline(),
  getConfig: () => ({
    strategy: injectionDraft.value.strategy,
    params: { ...injectionDraft.value.params },
  }),
});
</script>
