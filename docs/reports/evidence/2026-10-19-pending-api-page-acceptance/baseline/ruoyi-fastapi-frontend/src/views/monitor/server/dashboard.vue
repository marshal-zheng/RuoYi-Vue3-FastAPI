<template>
  <div class="app-container" data-testid="server-dashboard">
    <PersistentDashboard
      scope="account"
      storage-key="monitor-server"
      title="服务器监控"
      :initial-document="initialDocument"
      :registry="registry"
    >
      <template #controls>
        <el-button :loading="loading" @click="refresh">刷新监控数据</el-button>
        <span v-if="updatedAt">数据更新时间 {{ updatedAt }}</span>
        <span v-if="error" role="alert">{{ error }}</span>
      </template>
    </PersistentDashboard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from 'vue';
import { createDashboardRegistry } from '@zxio/dashboard/widget';
import { createDashboardWidgets } from '@zxio/dashboard-widgets';
import PersistentDashboard from '@/components/business/Dashboard/PersistentDashboard.vue';
import { getServer, type ServerInfo } from '@/api/monitor/server';
import { useChartTheme } from '@/theme/useChartTheme';
import type { DashboardDocument, DashboardPanel, DashboardJsonValue } from '@zxio/dashboard/schema';
import '@zxio/dashboard-widgets/style';

const server = shallowRef<ServerInfo>();
const loading = ref(false);
const updatedAt = ref('');
const error = ref('');
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
      definition.resolveProps?.({ ...panel, data: data.value[panel.id] ?? null }, context) ?? {},
  })),
});
const initialDocument: DashboardDocument = {
  schemaVersion: 2,
  uid: 'monitor-server',
  title: '服务器监控',
  pluginVersions: Object.fromEntries(
    registry.list().map((widget) => [widget.name, widget.version!])
  ),
  panels: [
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
      gridPos: { x: Number(x), y: Number(y), w: Number(w), h: Number(h) },
      params: widget === 'zx.gauge' ? { unit: '%', decimals: 1 } : {},
    })
  ),
};
async function refresh() {
  if (loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    server.value = await getServer();
    updatedAt.value = new Date().toLocaleTimeString();
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '监控数据加载失败';
  } finally {
    loading.value = false;
  }
}
onMounted(refresh);
</script>
