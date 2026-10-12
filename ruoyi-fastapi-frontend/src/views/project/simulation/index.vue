<template>
  <div
    data-testid="simulation-page"
    class="simulation-shell flex h-full bg-zx-surface-canvas-fill"
    :class="{ 'fault-injection-mode': isFaultInjectionMode }"
  >
    <!-- 故障注入模式提示条 -->
    <Transition name="mode-banner">
      <div v-if="isFaultInjectionMode" class="fault-mode-banner">
        <div class="banner-content">
          <div class="banner-icon">
            <el-icon class="pulse-icon"><Warning /></el-icon>
          </div>
          <div class="banner-text">
            <span class="banner-title">故障注入</span>
            <span class="banner-hint">
              <template v-if="!selectedEdge"
                >点击拓扑图中的 <strong>链路</strong> 选择目标</template
              >
              <template v-else
                >已锁定 <strong class="text-cyan-400">{{ getSelectedEdgeId() }}</strong></template
              >
            </span>
          </div>
          <div class="banner-actions">
            <el-button
              v-if="selectedEdge"
              class="cancel-select-btn"
              size="small"
              @click="clearSelectedEdge"
            >
              取消
            </el-button>
            <el-button class="exit-mode-btn" size="small" @click="exitFaultMode"> 关闭 </el-button>
          </div>
        </div>
        <div class="banner-progress"></div>
      </div>
    </Transition>

    <!-- 左侧主区域：header + main + footer -->
    <div class="flex flex-col flex-1 min-w-0 h-full">
      <!-- 顶部控制栏 -->
      <header class="shrink-0 z-50" data-testid="simulation-header">
        <SimulationHeader
          :status="simulationState.status"
          :elapsed-time="simulationState.elapsedTime"
          :speed="simulationState.speed"
          :project-name="projectName"
          :readonly="isReadonlySession"
          @start="handleStart"
          @pause="handlePause"
          @resume="handleResume"
          @stop="handleStop"
          @step="handleStep"
          @speed-change="handleSpeedChange"
          @back="handleBack"
          @health-check="handleHealthCheck"
          @show-events="handleShowEvents"
          @show-report="handleShowReport"
        />
      </header>

      <div
        v-if="isReadonlySession"
        class="simulation-readonly-banner"
        data-testid="simulation-readonly-banner"
        role="status"
      >
        只读演示模式，仿真控制操作已禁用
      </div>

      <!-- 主内容区域 -->
      <main class="flex flex-1 min-h-0 p-3 relative">
        <!-- 拓扑画布 -->
        <section
          data-testid="simulation-canvas"
          class="sim-canvas pro-card flex-1 relative"
          :class="{ 'fault-target-canvas': isFaultInjectionMode }"
        >
          <!-- 故障注入模式下的选中链路高亮层 -->
          <div v-if="isFaultInjectionMode && selectedEdge" class="selected-edge-indicator">
            <div class="indicator-ring"></div>
            <span class="indicator-text">已锁定目标链路</span>
          </div>
          <XflowDAG
            ref="dagRef"
            :showToolbar="false"
            :showSidebar="false"
            :operators="operators"
            :operators-loading="loading"
            :layout="layoutMode"
            :dnd-config="dndConfig"
            :show-graph-control="false"
            @node-click="handleNodeClick"
            @node-dblclick="handleNodeDblclick"
            @edge-click="handleEdgeClick"
            @edge-mouseenter="handleEdgeMouseEnter"
            @edge-mouseleave="handleEdgeMouseLeave"
          />

          <!-- 链路悬停信息提示 -->
          <EdgeTooltip
            v-if="hoveredEdge"
            :edge="hoveredEdge"
            :position="tooltipPosition"
            :bandwidth-data="getEdgeBandwidth(hoveredEdge)"
          />
        </section>

        <!-- 带宽面板（封装组件，内部含浮动容器） -->
        <BandwidthChartPanel
          ref="bandwidthChartRef"
          v-if="dockState.bandwidth"
          :visible="dockState.bandwidth"
          :bandwidth-data="bandwidthData"
          :running="isRunning"
          :speed="simulationState.speed"
          :reset-on-stop="true"
          :position="{ top: '14px', left: '14px' }"
          :size="{ width: '520px', maxHeight: '430px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
        />

        <!-- 告警面板（封装组件，内部含浮动容器） -->
        <AlarmPanelFloating
          v-if="dockState.alarm"
          :alarms="alarmData"
          :position="{ top: '14px', right: '14px' }"
          :size="{ width: '520px', maxHeight: '420px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
          @alarm-click="handleAlarmClick"
          @filter-change="handleAlarmFilterChange"
        />

        <!-- 时序/延迟分析面板 -->
        <TimingLatencyPanel
          v-if="dockState.timing"
          :visible="dockState.timing"
          :messages="filteredMessages"
          :bandwidth-data="bandwidthData"
          :position="{ top: 'min(420px, max(14px, calc(100vh - 620px)))', left: '14px' }"
          :size="{ width: '520px', maxHeight: '430px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
        />
      </main>

      <!-- 底部：协议分析器 -->
      <footer class="shrink-0 h-64 mx-3 mb-3 pro-card" data-testid="simulation-message-list">
        <ProtocolAnalyzer
          ref="protocolAnalyzerRef"
          :messages="filteredMessages"
          :is-running="isRunning"
          :auto-scroll="autoScroll"
          :speed="simulationState.speed"
          @message-select="handleMessageSelect"
          @filter-change="handleMessageFilterChange"
          @export="handleExportMessages"
          @auto-scroll-change="autoScroll = $event"
        />
      </footer>
    </div>

    <!-- 故障板浮层 -->
    <FaultBoardFloating
      v-if="dockState.fault"
      :visible="dockState.fault"
      :faults="faults"
      :loading="faultsLoading"
      :selected-edge="selectedEdge"
      :hovered-edge="hoveredEdge"
      :is-running="isRunning"
      :position="{ top: '58px', right: '92px' }"
      @apply-template="handleFaultTemplate"
      @clear="handleFaultClear"
      @clear-all="handleClearAllFaults"
      @refresh="refreshFaults"
      @close="exitFaultMode"
    />

    <!-- 数据注入策略面板 -->
    <DataInjectionPanel
      ref="injectionPanelRef"
      :visible="dockState.injection"
      :position="{ bottom: '280px', left: '14px' }"
      :default-collapsed="false"
      @apply="handleInjectionStrategyApply"
    />

    <!-- 右侧通顶侧边栏 - 航空暗黑系 -->
    <aside class="sim-side-dock-aside">
      <SimulationSideDock
        :items="dockItems"
        :active-keys="activeDockKeys"
        :badges="dockBadges"
        :disabled-items="dockDisabledItems"
        :all-collapsed="allDockPanelsCollapsed"
        @toggle="handleDockToggle"
        @toggle-all="handleToggleAllPanels"
      />
    </aside>

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />

    <!-- 事件触发面板 -->
    <EventTriggerPanel
      v-model:visible="showEventPanel"
      :events="eventList"
      :nodes="topologyNodes"
      @create="handleEventCreate"
      @edit="handleEventEdit"
      @delete="handleEventDelete"
      @trigger="handleEventTrigger"
    />

    <!-- 仿真报告对话框 -->
    <SimulationReportDialog ref="reportDialogRef" />

    <!-- 健康自检对话框 -->
    <HealthCheckDialog ref="healthCheckDialogRef" @recheck="handleHealthCheck" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue';
import { throttle } from 'lodash-es';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Warning } from '@element-plus/icons-vue';

// 组件导入
import XflowDAG from '@/components/business/Dag/index.vue';
import SimulationHeader from './components/SimulationHeader.vue';
import BandwidthChartPanel from './components/BandwidthChartPanel.vue';
import AlarmPanelFloating from './components/AlarmPanelFloating.vue';
import SimulationSideDock from './components/SimulationSideDock.vue';
import ProtocolAnalyzer from './components/ProtocolAnalyzer.vue';
import EdgeTooltip from './components/EdgeTooltip.vue';
import FaultBoardFloating from './components/FaultBoardFloating.vue';
import EventTriggerPanel from './components/EventTriggerPanel.vue';
import SimulationReportDialog from './components/SimulationReportDialog.vue';
import HealthCheckDialog from './components/HealthCheckDialog.vue';
import TimingLatencyPanel from './components/TimingLatencyPanel.vue';
import DataInjectionPanel from './components/DataInjectionPanel.vue';
import { NodeEditDrawer } from '../components';

// Composables 导入
import { useSimulationControl } from './composables/useSimulationControl';
import { useSimulationData } from './composables/useSimulationData';
import { useTopologyAnimation } from './composables/useTopologyAnimation';
import { useFaultInjection } from './composables/useFaultInjection';
import { useFaultInjectionUI } from './composables/useFaultInjectionUI';
import { useAlarmHandler } from './composables/useAlarmHandler';
import { useSimulationReport } from './composables/useSimulationReport';
import { useEventTrigger } from './composables/useEventTrigger';
import { useHealthCheck } from './composables/useHealthCheck';
import useAppStore from '@/store/modules/app';

// 样式导入 - 注意：simulation-theme.css 已内部导入 variables.css
import './styles/simulation-theme.css';
import './styles/fault-injection-mode.less';

// API 导入
import { listDevice } from '@/api/device/device';
import { getProject } from '@/api/project/project';
import { getProjectTopology } from '@/api/project/topology';
import {
  createSimulationSession,
  getEvents,
  getSimulationAlarms,
  getSimulationBandwidth,
  getSimulationMessages,
  getSimulationStatus,
} from '@/api/simulation/simulation';
import { resolveTopologyGraphJson } from '../utils/topologyGraph';

defineOptions({ name: 'SimulationConsole' });

// 路由
const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.projectId));
const versionId = computed(() =>
  route.query.versionId ? Number(route.query.versionId) : undefined
);
const appStore = useAppStore();

// 项目信息
const projectName = ref('');
const isReadonlySession = ref(false);

// DAG 组件
const dagRef = ref(null);
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal');
const dndConfig = {
  title: '设备库',
  searchPlaceholder: '搜索设备...',
  textConfig: {
    loadingText: '正在加载设备库...',
    emptySearchText: '没有找到匹配的设备',
    emptySearchDesc: '请尝试使用其他关键词搜索',
    emptyDataText: '暂无可用设备',
    emptyDataDesc: '请先添加设备数据',
  },
};

// 仿真控制
const {
  simulationState,
  sessionId,
  isRunning,
  isPaused,
  start,
  pause,
  resume,
  stop,
  step,
  setSpeed,
  syncStatus,
} = useSimulationControl(projectId, versionId);
let stepLock = false;

// 仿真数据
const {
  bandwidthData,
  messageData,
  alarmData,
  statusData,
  filteredMessages,
  filteredAlarms,
  messageFilter,
  alarmFilter,
  setMessageFilter,
  setAlarmFilter,
  clearData,
  updateBandwidthData,
  updateMessageData,
  updateAlarmData,
  updateStatistics,
  faultEventData,
  getNewFaultEvents,
} = useSimulationData(sessionId);

watch(statusData, (status) => {
  if (!status) return;
  syncStatus(status);
});

// 拓扑动画
const {
  startAnimation,
  stopAnimation,
  triggerTrafficAnimation,
  triggerErrorAnimation,
  setNodeActive,
  setNodeError,
  highlightEdges,
  clearEdgeHighlight,
} = useTopologyAnimation(dagRef, () => simulationState.speed);

const { runHealthCheck, PROTOCOL_REQUIRED_PARAMS } = useHealthCheck();
const healthReport = ref(null);

// 协议参数持久化辅助：将必需字段写入 port.params，供健康检查使用
const PARAM_ALIAS_MAP = {
  baudRate: ['baudRate', 'speed', 'dataRate'],
  ipAddress: ['ipAddress', 'ip', 'host'],
  port: ['port', 'lanPort'],
  protocol: ['protocol', 'proto', 'protocolType'],
  busAddress: ['busAddress'],
  rtAddress: ['rtAddress'],
  subAddress: ['subAddress'],
};

const normalizePortParams = (port = {}) => {
  const interfaceType = (port.interfaceType || port.busType || '').toUpperCase();
  const requiredParams = PROTOCOL_REQUIRED_PARAMS?.[interfaceType];
  if (!requiredParams || requiredParams.length === 0) return port;

  const params = { ...(port.params || {}) };
  const header = port.messageConfig?.header || {};
  const sources = [params, header, port];

  const pickValue = (key) => {
    const aliases = PARAM_ALIAS_MAP[key] || [key];
    for (const source of sources) {
      for (const alias of aliases) {
        const val = source?.[alias];
        if (val !== undefined && val !== null && val !== '') return val;
      }
    }
    return undefined;
  };

  requiredParams.forEach((key) => {
    const currentVal = params[key];
    if (currentVal === undefined || currentVal === null || currentVal === '') {
      const value = pickValue(key);
      if (value !== undefined && value !== null && value !== '') {
        params[key] = value;
      }
    }
  });

  return {
    ...port,
    params,
  };
};

const normalizePorts = (ports = []) => {
  if (!Array.isArray(ports)) return [];
  return ports.map((p) => normalizePortParams(p || {}));
};

const normalizeGraphPorts = (graph) => {
  if (!graph) return;
  graph.getNodes?.().forEach((node) => {
    const data = node.getData?.() || {};
    const normalizedPorts = normalizePorts(data.ports || []);
    node.setData({ ...data, ports: normalizedPorts }, { overwrite: true });
  });
};

// 故障注入
const faultInjection = useFaultInjection(sessionId);
const { faults, injectFault, ingestFaultEvents, loading: faultsLoading } = faultInjection;

// 事件触发
const { eventList, loadEvents, createEvent, updateEvent, deleteEvent, triggerEvent } =
  useEventTrigger(sessionId);

// 获取拓扑节点列表（用于事件触发面板的设备选择）
const topologyNodes = ref([]);

// 更新拓扑节点列表
function updateTopologyNodes() {
  const graph = dagRef.value?.getGraph?.();
  if (!graph) return;
  const nodes = graph.getNodes?.() || [];
  topologyNodes.value = nodes.map((node) => ({
    id: node.id,
    data: node.getData?.() || node.data || {},
    label: node.getData?.()?.label || node.data?.label || node.id,
  }));
}

// UI 状态
const currentNode = ref(null);
const hoveredEdge = ref(null);
const tooltipPosition = ref({ x: 0, y: 0 });
const autoScroll = ref(true);
const dashboardShowTrend = ref(false);
const showEventPanel = ref(false);
const simulationSummary = ref(null);

// 数据注入策略配置
const injectionStrategy = ref({
  strategy: 'random',
  params: {
    valueRange: '0~255',
    startValue: 0,
    step: 1,
    fixedValue: '0',
    presetValues: '0,1,2,3,4,5',
    amplitude: 100,
    offset: 0,
    frequency: 1,
    phase: 0,
  },
});
const dockState = reactive({
  bandwidth: false,
  alarm: false,
  timing: false,
  fault: false,
  injection: false,
});

const dockItems = [
  { key: 'bandwidth', label: '带宽', icon: 'TrendCharts' },
  { key: 'alarm', label: '告警', icon: 'Bell' },
  { key: 'timing', label: '时序', icon: 'Timer' },
  { key: 'fault', label: '故障', icon: 'Warning' },
  { key: 'injection', label: '注入', icon: 'MagicStick' },
];
const activeDockKeys = computed(() => {
  const keys = [];
  if (dockState.bandwidth) keys.push('bandwidth');
  if (dockState.alarm) keys.push('alarm');
  if (dockState.timing) keys.push('timing');
  if (dockState.fault) keys.push('fault');
  if (dockState.injection) keys.push('injection');
  return keys;
});
const dockBadges = computed(() => {
  const uniqueAlarmCount = alarmData.value?.length
    ? new Set(alarmData.value.map((item) => item.alarmId)).size
    : 0;
  const activeFaultCount = faults.value?.filter?.((f) => f.status === 'active').length || 0;
  return {
    alarm: uniqueAlarmCount || '',
    fault: activeFaultCount || '',
  };
});

// 侧边栏按钮禁用配置
const dockDisabledItems = computed(() => {
  const disabled = {};
  // 仿真未运行时禁用故障注入
  if (!isRunning.value) {
    disabled.fault = '请先启动仿真后再进行故障注入';
  }
  return disabled;
});
const allDockPanelsCollapsed = computed(() => {
  return (
    !dockState.bandwidth &&
    !dockState.alarm &&
    !dockState.timing &&
    !dockState.fault &&
    !dockState.injection
  );
});

// 组件引用
const nodeEditDrawerRef = ref(null);
const protocolAnalyzerRef = ref(null);
const reportDialogRef = ref(null);
const healthCheckDialogRef = ref(null);
const bandwidthChartRef = ref(null);
const injectionPanelRef = ref(null);

// 获取图实例
function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

/**
 * 构建端口到对端设备名的映射
 * @param {Object} node - 当前节点
 * @returns {Record<string, string[]>} key 为端口 ID，value 为对端设备名称数组
 */
function buildPeerDeviceNameByPort(node) {
  const graph = getGraphInstance();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];

  const registerPeer = (portId, peerName) => {
    if (!portId || !peerName) return;
    const key = String(portId);
    const keys = [key];
    if (key.startsWith('port-')) {
      keys.push(key.replace(/^port-/, ''));
    }

    keys.forEach((k) => {
      if (!result[k]) {
        result[k] = [];
      }
      const list = Array.isArray(result[k]) ? result[k] : [result[k]];
      if (!list.includes(peerName)) {
        result[k] = list.concat(peerName);
      } else {
        result[k] = list;
      }
    });
  };

  edges.forEach((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    if (!sourceId || !targetId) return;

    let localPortId;
    let peerNodeId;

    if (sourceId === nodeId) {
      localPortId = edge.getSourcePortId?.();
      peerNodeId = targetId;
    } else if (targetId === nodeId) {
      localPortId = edge.getTargetPortId?.();
      peerNodeId = sourceId;
    } else {
      return;
    }

    if (!localPortId || !peerNodeId) return;

    const peerNode = graph.getCellById(peerNodeId);
    const data = peerNode?.getData?.() || {};
    const deviceName = data.name || data.label || data.deviceName || '';

    registerPeer(localPortId, deviceName);
  });

  return result;
}

// 故障注入 UI 交互
const {
  selectedEdge,
  isFaultInjectionMode,
  getSelectedEdgeId,
  setupEdgeEvents,
  clearSelectedEdge,
  exitFaultMode: _exitFaultMode,
  handleFaultClear,
  handleClearAllFaults,
  handleFaultTemplate: _handleFaultTemplate,
  refreshFaults,
} = useFaultInjectionUI({
  getGraphInstance,
  dockState,
  faultInjection,
});

// 退出故障模式（包装函数，额外清除图上的高亮状态）
async function exitFaultMode() {
  const graph = getGraphInstance();
  if (graph) {
    // 清除所有边的高亮
    const edgeIds = graph.getEdges().map((e) => e.id);
    clearEdgeHighlight(edgeIds);
    // 清除所有节点的错误状态
    graph.getNodes().forEach((node) => {
      setNodeError(node.id, false);
      setNodeActive(node.id, false, true);
    });
  }
  await _exitFaultMode();
}

// 告警处理
const { handleAlarmClick, handleAlarmFilterChange } = useAlarmHandler({
  getGraphInstance,
  topologyAnimation: {
    highlightEdges,
    clearEdgeHighlight,
    triggerErrorAnimation,
    setNodeError,
    setNodeActive,
  },
});

// 仿真报告
const { buildSimulationSummary } = useSimulationReport({
  messageData,
  alarmData,
  bandwidthData,
  simulationState,
});

// 加载项目信息（无权限时静默降级）
async function loadProjectInfo() {
  try {
    const res = await getProject(projectId.value, { silentError: true });
    // http 客户端已解包 payload.data，直接访问字段
    projectName.value = res?.projectName || '未命名工程';
  } catch (err) {
    console.warn('[仿真] 无法获取工程信息，可能缺少 project:project:query 权限');
    projectName.value = '未命名工程';
  }
}

// 加载设备列表（无权限时静默降级，不影响仿真主功能）
async function loadDeviceList() {
  loading.value = true;
  try {
    const response = await listDevice({ page: 1, pageSize: 9999 }, { silentError: true });
    const devices = response?.items || [];
    operators.value = devices.map((device) => ({
      name: device.deviceName,
      value: device.remark || device.deviceDesc || '设备',
      category: device.categoryName || device.category || '未分类',
      deviceId: device.deviceId,
      deviceType: device.deviceType,
      busType: device.busType,
      ports: normalizePorts(device.interfaces || []),
      nodeType: 'device-port-node',
    }));
  } catch (err) {
    // 无设备列表权限时静默降级，仅在控制台记录
    console.warn('[仿真] 无法加载设备库，可能缺少 device:list:list 权限');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

// 从后端加载并回显已保存的拓扑数据
function restoreSavedTopology() {
  if (!projectId.value) return;

  const tryRestore = () => {
    const graph = dagRef.value?.getGraph?.();
    if (!graph) {
      setTimeout(tryRestore, 200);
      return;
    }

    // 设置边的事件监听
    setupEdgeEvents(graph);
    setupEdgeHoverEvents(graph);

    getProjectTopology(projectId.value, versionId.value, { silentError: true })
      .then((res) => {
        // http 客户端已解包 payload.data，res 直接是拓扑数据
        const topoData = res?.topologyData || res?.graph;
        const graphJson = resolveTopologyGraphJson(topoData);
        if (graphJson) {
          graph.fromJSON(graphJson);
          normalizeGraphPorts(graph);
          // 拓扑加载完成后，更新节点列表
          updateTopologyNodes();
        }
      })
      .catch((err) => {
        console.warn('[仿真] 无法加载拓扑数据，可能缺少 project:project:query 权限', err);
        ElMessage.warning('无法加载拓扑数据，请检查权限配置');
      });
  };

  tryRestore();
}

async function loadReadonlySimulationSnapshot() {
  isReadonlySession.value = false;
  try {
    const session = await createSimulationSession({
      projectId: projectId.value,
      versionId: versionId.value,
      readonly: true,
    });
    isReadonlySession.value = session?.readonly === true;
    const readonlySessionId = session?.sessionId;
    if (!readonlySessionId) {
      return;
    }
    sessionId.value = readonlySessionId;
    if (session?.status) {
      syncStatus(session);
      updateStatistics(session);
    }

    const [status, messages, bandwidth, alarms, events] = await Promise.all([
      getSimulationStatus(readonlySessionId),
      getSimulationMessages(readonlySessionId, 100),
      getSimulationBandwidth(readonlySessionId),
      getSimulationAlarms(readonlySessionId),
      getEvents(readonlySessionId),
    ]);

    if (status) {
      syncStatus(status);
      updateStatistics(status);
    }
    if (Array.isArray(messages)) {
      updateMessageData(messages);
    }
    if (Array.isArray(bandwidth)) {
      updateBandwidthData(bandwidth);
    }
    if (Array.isArray(alarms)) {
      updateAlarmData(alarms);
    }
    if (Array.isArray(events)) {
      eventList.value = events;
    }
  } catch (err) {
    console.warn('[仿真] 无法加载只读演示数据', err);
  }
}

// 设置边的鼠标事件（hover 提示）
function setupEdgeHoverEvents(graph) {
  if (!graph) return;

  graph.on('edge:mouseenter', ({ edge, e }) => {
    hoveredEdge.value = edge;
    tooltipPosition.value = { x: e.clientX, y: e.clientY };
  });

  graph.on('edge:mouseleave', () => {
    hoveredEdge.value = null;
  });
}

// 仿真控制处理
async function handleStart() {
  if (isReadonlySession.value) {
    ElMessage.info('只读演示模式下不可启动仿真');
    return;
  }

  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('图实例不存在');
    return;
  }

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning('请至少放置两个设备节点');
    return;
  }

  if (!edges.length) {
    ElMessage.warning('请先建立设备之间的连接');
    return;
  }

  const passed = await runPreflightCheck(graph);
  if (!passed) return;

  // 构建数据注入策略参数
  const strategyConfig = injectionPanelRef.value?.getConfig?.() || injectionStrategy.value;
  const startOptions = {
    injection_strategy: strategyConfig.strategy,
    injection_params: strategyConfig.params,
  };

  try {
    await start(startOptions);
    startAnimation();
  } catch (err) {
    const message = err?.problem?.detail || err?.detail || err?.message || '启动失败';
    ElMessage.error(message);
  }
}

async function handlePause() {
  if (isReadonlySession.value) {
    ElMessage.info('只读演示模式下不可暂停仿真');
    return;
  }

  try {
    await pause();
    stopAnimation();
  } catch (err) {
    const message = err?.problem?.detail || err?.detail || err?.message || '暂停失败';
    ElMessage.error(message);
  }
}

function handleResume() {
  if (isReadonlySession.value) {
    ElMessage.info('只读演示模式下不可继续仿真');
    return;
  }

  resume();
  startAnimation();
}

async function handleStop() {
  if (isReadonlySession.value) {
    ElMessage.info('只读演示模式下不可停止仿真');
    return;
  }

  await stop();
  stopAnimation();
  simulationSummary.value = buildSimulationSummary();
  reportDialogRef.value?.open({
    sessionId: sessionId.value,
    summary: simulationSummary.value,
  });
}

const handleStep = throttle(
  () => {
    if (isReadonlySession.value) {
      ElMessage.info('只读演示模式下不可单步执行');
      return;
    }

    if (stepLock) return;
    stepLock = true;
    step()
      .then(() => {
        bandwidthChartRef.value?.stepScanline();
      })
      .catch((err) => {
        const message = err?.message || '单步执行失败';
        ElMessage.error(message);
      })
      .finally(() => {
        stepLock = false;
      });
  },
  500,
  { trailing: false }
);

function handleSpeedChange(speed) {
  setSpeed(speed);
}

function handleBack() {
  router.push(`/project/project-detail/index/${projectId.value}`);
}

// 节点事件处理
function handleNodeClick({ node }) {
  // 点击节点时取消链路选中
  selectedEdge.value = null;
}

function handleNodeDblclick({ node }) {
  // 构建端口到对端设备名的映射
  const peerDeviceNameByPort = buildPeerDeviceNameByPort(node);
  // 转为普通 JSON
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;
  // 附加映射数据
  const nodeData = jsonNode?.data || {};
  currentNode.value = {
    ...jsonNode,
    data: {
      ...nodeData,
      ports: normalizePorts(nodeData.ports || []),
    },
    peerDeviceNameByPort,
  };
  nodeEditDrawerRef.value?.open();
}

function handleNodeUpdate({ nodeId, name, ports }) {
  const graph = getGraphInstance();
  if (!graph) return;

  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) return;

  const currentData = cellNode.getData() || {};
  const normalizedPorts = normalizePorts(ports || currentData.ports);
  cellNode.setData(
    {
      ...currentData,
      name,
      label: name,
      ports: normalizedPorts,
    },
    { overwrite: false }
  );
}

// 链路事件处理 (这些函数现在由 setupEdgeEvents 中的图实例事件监听处理)
function handleEdgeClick({ edge, e }) {
  // 由 setupEdgeEvents 处理
}

function handleEdgeMouseEnter({ edge, e }) {
  // 由 setupEdgeEvents 处理
}

function handleEdgeMouseLeave() {
  // 由 setupEdgeEvents 处理
}

function getEdgeBandwidth(edge) {
  if (!edge) return null;
  const sourcePortId = edge.getSourcePortId?.();
  return bandwidthData.value.find((b) => b.portId === sourcePortId);
}

// 端口点击
function handlePortClick(portData) {
  const graph = getGraphInstance();
  if (!graph) return;

  const edges = graph.getEdges?.() || [];
  edges.forEach((edge) => {
    const sourcePortId = edge.getSourcePortId?.();
    const targetPortId = edge.getTargetPortId?.();
    if (sourcePortId === portData.portId || targetPortId === portData.portId) {
      triggerTrafficAnimation(edge.id, portData.protocolType);
    }
  });
}

// 报文处理
function handleMessageSelect(message) {
  if (message.senderNodeId && message.receiverNodeId) {
    const graph = getGraphInstance();
    if (graph) {
      const edges = graph.getEdges?.() || [];
      const edge = edges.find((e) => {
        const sourceId = e.getSourceCellId?.();
        const targetId = e.getTargetCellId?.();
        return (
          (sourceId === message.senderNodeId && targetId === message.receiverNodeId) ||
          (sourceId === message.receiverNodeId && targetId === message.senderNodeId)
        );
      });
      if (edge) {
        triggerTrafficAnimation(edge.id, message.protocolType);
      }
    }
  }
}

function handleMessageFilterChange(filter) {
  setMessageFilter(filter);
}

function handleDockToggle(key) {
  dockState[key] = !dockState[key];
}

function handleToggleAllPanels() {
  const allCollapsed =
    !dockState.bandwidth &&
    !dockState.alarm &&
    !dockState.timing &&
    !dockState.fault &&
    !dockState.injection;
  Object.keys(dockState).forEach((key) => {
    dockState[key] = allCollapsed;
  });
}

function handleExportMessages(format) {
  protocolAnalyzerRef.value?.exportData(format);
}

// 故障模板应用（包装 composable 方法，传入 hoveredEdge）
function handleFaultTemplate(tpl) {
  _handleFaultTemplate(tpl, hoveredEdge);
}

// 数据注入策略应用
function handleInjectionStrategyApply(config) {
  injectionStrategy.value = config;
}

// 事件触发处理
async function handleEventCreate(config) {
  if (!sessionId.value) {
    ElMessage.warning('请先启动仿真会话后再添加事件');
    return;
  }
  try {
    await createEvent(config);
  } catch (err) {
    console.error('创建事件失败', err);
  }
}

async function handleEventEdit(eventId, config) {
  if (!sessionId.value) {
    ElMessage.warning('当前无仿真会话，无法更新事件');
    return;
  }
  try {
    await updateEvent(eventId, config);
  } catch (err) {
    console.error('更新事件失败', err);
  }
}

async function handleEventDelete(eventId) {
  if (!sessionId.value) {
    ElMessage.warning('当前无仿真会话，无法删除事件');
    return;
  }
  try {
    await deleteEvent(eventId);
  } catch (err) {
    console.error('删除事件失败', err);
  }
}

async function handleEventTrigger(eventId) {
  if (!sessionId.value) {
    ElMessage.warning('当前无仿真会话，无法触发事件');
    return;
  }
  try {
    await triggerEvent(eventId);
  } catch (err) {
    console.error('触发事件失败', err);
  }
}

// 健康自检
function handleHealthCheck() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('图实例不存在');
    return;
  }
  const report = runHealthCheck(graph);
  healthReport.value = report;
  healthCheckDialogRef.value?.open(report);
}

// 显示事件面板
function handleShowEvents() {
  showEventPanel.value = true;
}

// 显示仿真报告
function handleShowReport() {
  if (!sessionId.value) {
    ElMessage.warning('当前无仿真会话，无法生成报告');
    return;
  }
  simulationSummary.value = buildSimulationSummary();
  reportDialogRef.value?.open({
    sessionId: sessionId.value,
    summary: simulationSummary.value,
  });
}

async function runPreflightCheck(graph) {
  const report = runHealthCheck(graph);
  healthReport.value = report;
  if (!report.canSimulate || report.errorChecks > 0) {
    healthCheckDialogRef.value?.open(report);
    ElMessage.error('拓扑检查未通过，无法启动仿真');
    return false;
  }
  if (report.warningChecks > 0) {
    healthCheckDialogRef.value?.open(report);
    ElMessage.warning('存在警告，请确认后继续');
  }
  return true;
}

watch(faultEventData, () => {
  const events = getNewFaultEvents();
  if (events && events.length) {
    ingestFaultEvents(events);
  }
});

watch(
  sessionId,
  (id) => {
    if (id) {
      refreshFaults();
      loadEvents();
    } else {
      console.log('eventList.valuesss', eventList.value);
      eventList.value = [];
    }
  },
  { immediate: true }
);

// 监听故障面板打开，自动获取故障列表
watch(
  () => dockState.fault,
  (opened) => {
    if (opened && sessionId.value) {
      refreshFaults();
    }
  }
);

// 生命周期
onMounted(async () => {
  // 进入页面时自动收起全局侧边栏
  appStore.closeSideBar({ withoutAnimation: true });
  await Promise.all([loadProjectInfo(), loadDeviceList()]);
  restoreSavedTopology();
  await loadReadonlySimulationSnapshot();
});

onUnmounted(() => {
  if (isRunning.value) {
    stop();
  }
  stopAnimation();
});

// 监听仿真状态变化
watch(isRunning, (running) => {
  if (running) {
    startAnimation();
  } else {
    stopAnimation();
  }
});
</script>

<style scoped>
@import './styles/animation.css';

/* 拓扑画布网格跟随 Host，设备/协议图形保留领域配色。 */
.sim-canvas {
  background-color: var(--zx-semantic-surface-canvas-fill);
  background-image:
    linear-gradient(var(--zx-semantic-border-subtle) 1px, transparent 1px),
    linear-gradient(90deg, var(--zx-semantic-border-subtle) 1px, transparent 1px);
  background-size:
    20px 20px,
    20px 20px;
  background-position:
    0 0,
    0 0;
}

.sim-canvas :deep(.xflow-dag),
.sim-canvas :deep(.xflow-dag-container) {
  width: 100% !important;
  height: 100% !important;
  position: relative;
  z-index: 1;
}

/* 仿真页面 DAG 暗黑主题覆盖 */
.sim-canvas :deep(.zx-dag-page) {
  background: transparent;
}

.sim-canvas :deep(.dag-center) {
  background: transparent !important;
}

.sim-canvas :deep(.dag-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.xflow-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.x6-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.x6-graph-svg) {
  background: transparent !important;
}

.simulation-shell {
  background: var(--zx-semantic-surface-canvas-fill);
}

.simulation-readonly-banner {
  border-bottom: 1px solid rgba(251, 191, 36, 0.35);
  background: rgba(120, 53, 15, 0.45);
  color: #fde68a;
  font-size: 13px;
  font-weight: 600;
  line-height: 32px;
  padding: 0 20px;
}

.floating-panel {
  position: absolute;
  z-index: 30;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.panel-title .title-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--zx-semantic-surface-panel-on-text);
  letter-spacing: 0.02em;
}

.panel-title .live-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 6px;
  border-radius: 3px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  font-size: 10px;
  font-weight: 600;
  color: #10b981;
  letter-spacing: 0.04em;
}

.panel-title .live-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10b981;
  animation: live-pulse 1.5s ease-in-out infinite;
}

@keyframes live-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.panel-actions {
  display: inline-flex;
  align-items: center;
}

.view-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.view-toggle .toggle-item {
  color: var(--zx-semantic-text-secondary);
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}

.view-toggle .toggle-item:hover {
  color: var(--zx-semantic-text-disabled);
}

.view-toggle .toggle-item.active {
  color: var(--zx-semantic-accent-on-surface);
  font-weight: 500;
}

.view-toggle .toggle-divider {
  color: var(--zx-semantic-text-secondary);
  font-weight: 300;
}

/* 右侧通顶侧边栏 - 航空暗黑系 */
.sim-side-dock-aside {
  position: relative;
  flex-shrink: 0;
  width: 80px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 10px;
  background: var(--zx-semantic-surface-panel-fill);
  color: var(--zx-semantic-surface-panel-on-text);
  border-left: 1px solid var(--zx-semantic-border-default);
  box-shadow: var(--zx-semantic-surface-panel-depth);
}

/* 侧边栏顶部光晕 */
.sim-side-dock-aside::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: radial-gradient(
    ellipse 100% 100% at 50% -20%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 8%, transparent) 0%,
    transparent 70%
  );
  pointer-events: none;
}

/* 侧边栏底部光晕 */
.sim-side-dock-aside::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: radial-gradient(
    ellipse 100% 100% at 50% 120%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 5%, transparent) 0%,
    transparent 70%
  );
  pointer-events: none;
}
</style>
