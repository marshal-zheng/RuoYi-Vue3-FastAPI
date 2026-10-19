<template>
  <div
    class="app-container server-dashboard"
    :class="{ 'has-settings': !!settings }"
    data-testid="server-dashboard"
  >
    <PersistentDashboard
      scope="account"
      storage-key="monitor-server"
      title="服务器监控"
      :initial-document="initialDocument"
      :registry="registry"
      :settings-active="!!settings"
    >
      <template #controls="{ beginSettings, settingsReady, document, updateDocument }">
        <el-button :loading="loading" @click="refresh">刷新监控数据</el-button>
        <el-button
          v-if="!document.panels.some((panel) => panel.id === 'cpu-trend')"
          :disabled="!settingsReady || !!settings"
          @click="addTrend(document, updateDocument)"
          >添加 CPU 时序图</el-button
        >
        <el-button
          v-else
          ref="settingsButton"
          :disabled="!settingsReady || !!settings"
          @click="openSettings(beginSettings)"
          >CPU 时序图设置</el-button
        >
        <span v-if="settingsMessage" role="status">{{ settingsMessage }}</span>
        <span v-if="updatedAt">数据更新时间 {{ updatedAt }}</span>
        <span v-if="error" role="alert">{{ error }}</span>
      </template>
    </PersistentDashboard>
    <TimeSeriesSettings
      v-if="settings"
      :params="settings.panel.params ?? {}"
      :save="settings.save"
      @preview="preview = $event"
      @cancel="closeSettings"
      @saved="savedSettings"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, shallowRef } from 'vue';
import { createDashboardRegistry } from '@zxio/dashboard/widget';
import { createDashboardWidgets } from '@zxio/dashboard-widgets';
import PersistentDashboard from '@/components/business/Dashboard/PersistentDashboard.vue';
import TimeSeriesSettings from '@/components/business/Dashboard/TimeSeriesSettings.vue';
import type { PanelSettingsSession } from '@/components/business/Dashboard/panel-settings';
import { getServer, type ServerInfo } from '@/api/monitor/server';
import { useChartTheme } from '@/theme/useChartTheme';
import type { DashboardDocument, DashboardPanel, DashboardJsonValue } from '@zxio/dashboard/schema';
import '@zxio/dashboard-widgets/style';

const server = shallowRef<ServerInfo>();
const loading = ref(false);
const updatedAt = ref('');
const error = ref('');
const samples = shallowRef<[number, number][]>([]);
const settings = shallowRef<PanelSettingsSession>();
const preview = shallowRef<Record<string, DashboardJsonValue>>();
const settingsMessage = ref('');
const settingsButton = ref<{ $el: HTMLButtonElement }>();
const { projection } = useChartTheme();
const columns = [
  { key: 'name', label: '属性' },
  { key: 'value', label: '值' },
];
function table(rows: [string, string | number | undefined][]) {
  return {
    columns,
    rows: rows.map(([name, value]) => ({ name, value: value ?? '—' })),
  };
}
const data = computed((): Record<string, DashboardJsonValue> => {
  const s = server.value;
  if (!s) return {};
  return {
    cpu: { value: s.cpu.used + s.cpu.sys },
    'cpu-trend': { series: [{ name: 'CPU 使用率', points: samples.value }] },
    memory: { value: s.mem.usage },
    python: { value: s.py.usage },
    'cpu-details': table([
      ['核心数', s.cpu.cpuNum],
      ['用户使用率 (%)', s.cpu.used],
      ['系统使用率 (%)', s.cpu.sys],
      ['当前空闲率 (%)', s.cpu.free],
    ]),
    'memory-details': {
      columns: [
        { key: 'name', label: '属性' },
        { key: 'memory', label: '内存' },
        { key: 'python', label: 'Python' },
      ],
      rows: (['total', 'used', 'free', 'usage'] as const).map((key, i) => ({
        name: ['总内存', '已用内存', '剩余内存', '使用率 (%)'][i],
        memory: s.mem[key],
        python: s.py[key],
      })),
    },
    system: table([
      ['服务器名称', s.sys.computerName],
      ['操作系统', s.sys.osName],
      ['服务器 IP', s.sys.computerIp],
      ['系统架构', s.sys.osArch],
      ['项目路径', s.sys.userDir],
    ]),
    runtime: table([
      ['Python 名称', s.py.name],
      ['Python 版本', s.py.version],
      ['启动时间', s.py.startTime],
      ['运行时长', s.py.runTime],
      ['安装路径', s.py.home],
    ]),
    disks: {
      columns: [
        ['dirName', '盘符路径'],
        ['sysTypeName', '文件系统'],
        ['typeName', '盘符名称'],
        ['total', '总大小'],
        ['free', '可用大小'],
        ['used', '已用大小'],
        ['usage', '已用百分比 (%)'],
      ].map(([key, label]) => ({ key, label })),
      rows: s.sysFiles.map((file) => ({ ...file })),
    },
  };
});
const registry = createDashboardRegistry();
const pack = createDashboardWidgets({
  locale: 'zh-CN',
  themeProjection: projection,
});
registry.use({
  ...pack,
  widgets: (pack.widgets ?? []).map((definition) => ({
    ...definition,
    resolveProps: (panel, context) =>
      definition.resolveProps?.(
        {
          ...panel,
          params: panel.id === 'cpu-trend' && preview.value ? preview.value : panel.params,
          data: data.value[panel.id] ?? null,
        },
        context
      ) ?? {},
  })),
});
const trendPanel: DashboardPanel = {
  id: 'cpu-trend',
  widget: 'zx.time-series',
  title: 'CPU 使用率趋势',
  gridPos: { x: 0, y: 0, w: 24, h: 8 },
  params: {
    smooth: false,
    chart: {
      title: { show: true, text: 'CPU 使用率趋势' },
      legend: { show: true, position: 'top' },
      xAxis: { show: true },
      yAxis: { mode: 'fixed', min: 0, max: 100, name: '%' },
    },
  },
};
const initialDocument: DashboardDocument = {
  schemaVersion: 2,
  uid: 'monitor-server',
  title: '服务器监控',
  pluginVersions: Object.fromEntries(
    registry.list().map((widget) => [widget.name, widget.version!])
  ),
  panels: [
    trendPanel,
    ...[
      ['cpu', 'CPU 使用率', 'zx.gauge', 0, 0, 8, 6],
      ['memory', '内存使用率', 'zx.gauge', 8, 0, 8, 6],
      ['python', 'Python 内存使用率', 'zx.gauge', 16, 0, 8, 6],
      ['cpu-details', 'CPU', 'zx.table', 0, 6, 12, 6],
      ['memory-details', '内存', 'zx.table', 12, 6, 12, 6],
      ['system', '服务器信息', 'zx.table', 0, 12, 12, 7],
      ['runtime', 'Python 解释器', 'zx.table', 12, 12, 12, 7],
      ['disks', '磁盘状态', 'zx.table', 0, 19, 24, 7],
    ].map(
      ([id, title, widget, x, y, w, h]): DashboardPanel => ({
        id: String(id),
        title: String(title),
        widget: String(widget),
        gridPos: { x: Number(x), y: Number(y) + 8, w: Number(w), h: Number(h) },
        params: widget === 'zx.gauge' ? { unit: '%', decimals: 1 } : {},
      })
    ),
  ],
};
function addTrend(document: DashboardDocument, update: (document: DashboardDocument) => void) {
  if (document.panels.some((panel) => panel.id === trendPanel.id)) return;
  const y = Math.max(0, ...document.panels.map((panel) => panel.gridPos.y + panel.gridPos.h));
  update({
    ...document,
    panels: [...document.panels, { ...trendPanel, gridPos: { ...trendPanel.gridPos, y } }],
  });
}
function openSettings(begin: (panelId: string) => PanelSettingsSession) {
  settingsMessage.value = '';
  try {
    settings.value = begin('cpu-trend');
  } catch (cause) {
    settingsMessage.value = cause instanceof Error ? cause.message : '打开设置失败';
  }
}
function closeSettings() {
  preview.value = undefined;
  settings.value = undefined;
  nextTick(() => settingsButton.value?.$el.focus());
}
function savedSettings() {
  closeSettings();
  settingsMessage.value = '图表设置已保存';
}
async function refresh() {
  if (loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    server.value = await getServer();
    samples.value = [
      ...samples.value,
      [Date.now(), server.value.cpu.used + server.value.cpu.sys] as [number, number],
    ].slice(-120);
    updatedAt.value = new Date().toLocaleTimeString();
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '监控数据加载失败';
  } finally {
    loading.value = false;
  }
}
onMounted(refresh);
</script>

<style scoped>
.server-dashboard.has-settings {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}
.has-settings :deep(.chart-settings) {
  position: sticky;
  top: 12px;
  max-height: calc(100vh - 110px);
  overflow: auto;
}
@media (max-width: 900px) {
  .server-dashboard.has-settings {
    grid-template-columns: minmax(0, 1fr);
  }
  .has-settings :deep(.chart-settings) {
    position: static;
    grid-row: 1;
    max-height: none;
  }
}
</style>
