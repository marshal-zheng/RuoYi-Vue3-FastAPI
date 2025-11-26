<template>
  <transition name="page-fade" mode="out-in">
    <ZxContentWrap class="simulation-page" v-if="!pageLoading">
      <!-- header-right插槽添加 '仿真'操作 -->
      <template #header-right>
        <template v-if="simulationStatus === 'running'">
          <el-tag type="success" effect="dark" class="simulation-running-tag">
            <el-icon class="is-loading"><Loading /></el-icon>
            {{ simulationContinuousMode ? `持续运行 - 第${simulationLoopCount || 1}轮` : '运行中' }}
          </el-tag>
          <zx-button type="danger" icon="VideoPause" @click="handleStopSimulation">
            停止仿真
          </zx-button>
        </template>
        <template v-else>
          <el-dropdown @command="handleRunSimulation">
            <el-button type="primary">
              执行仿真
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="once">
                  <el-icon><VideoPlay /></el-icon>
                  执行一轮
                </el-dropdown-item>
                <el-dropdown-item command="continuous">
                  <el-icon><Refresh /></el-icon>
                  持续播放
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <zx-button type="success" icon="Cpu" @click="handleHealthCheck"> 健康自检 </zx-button>
      </template>
      <XflowDAG
        ref="dagRef"
        :showToolbar="false"
        :showSidebar="false"
        :operators="operators"
        :operators-loading="loading"
        :layout="layoutMode"
        :dnd-config="dndConfig"
        :show-graph-control="false"
        @node-dblclick="handleNodeDblclick"
      >
        <template #right>
          <template v-if="simulationStatus === 'running'">
            <zx-button size="small" type="danger" @click="handleStopSimulation">
              停止仿真
            </zx-button>
          </template>
          <template v-else>
            <el-dropdown @command="handleRunSimulation" :disabled="loading || simulationLoading">
              <el-button size="small" type="success" :loading="simulationLoading">
                执行仿真
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="once">
                    <el-icon><VideoPlay /></el-icon>
                    执行一轮
                  </el-dropdown-item>
                  <el-dropdown-item command="continuous">
                    <el-icon><Refresh /></el-icon>
                    持续播放
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <zx-button size="small" type="primary" :disabled="loading" @click="handleSaveTopo">
            保存
          </zx-button>
        </template>
      </XflowDAG>

      <!-- 仿真进度面板（左上角） -->
      <SimulationStatusPanel
        :narration="simulationNarration"
        :position="{ top: '40px', left: '30px' }"
      />

      <!-- 告警信息面板（左下角） -->
      <SimulationMonitorPanel
        :visible="showAlarmPanel"
        :alarms="alarmData"
        :position="{ bottom: '30px', left: '30px' }"
        :default-collapsed="false"
      />

      <!-- 带宽图表面板 -->
      <BandwidthChartPanel
        :visible="showPanels"
        :bandwidth-data="bandwidthData"
        :position="{ top: '40px', right: '30px' }"
        :default-collapsed="false"
      />

      <!-- 报文列表面板（常态显示） -->
      <MessageListPanel
        ref="messageListRef"
        :visible="showMessagePanel"
        :messages="messageData"
        :position="{ bottom: '20px', right: '20px' }"
        :default-collapsed="false"
      />

      <!-- 节点编辑抽屉 -->
      <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />

      <!-- 仿真结果对话框 -->
      <SimulationResultDialog ref="simulationDialogRef" @reopen="handleReopenSimulationDialog" />

      <!-- 健康自检对话框 -->
      <HealthCheckDialog ref="healthCheckDialogRef" @recheck="handleHealthCheck" />
    </ZxContentWrap>
    <ZxContentWrap v-else class="simulation-page simulation-page--loading">
      <SkeletonLoader type="default" />
    </ZxContentWrap>
  </transition>
</template>

<script setup name="Index">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Loading, ArrowDown, VideoPlay, Refresh } from '@element-plus/icons-vue';
import XflowDAG from '@/components/business/Dag/index.vue';
import {
  NodeEditDrawer,
  SimulationResultDialog,
  SimulationMonitorPanel,
  BandwidthChartPanel,
  MessageListPanel,
  HealthCheckDialog,
} from './simulation/components';
import SimulationStatusPanel from './components/SimulationStatusPanel.vue';
import { listDevice } from '@/api/device/device';
import {
  createSimulationSession,
  startSimulationSession,
  stopSimulationSession,
} from '@/api/simulation/simulation';
import { ElMessage } from 'element-plus';

// 引入拆分的 composables
import { useGraphStyle } from './composables/useGraphStyle';
import { useSimulationAnimation } from './composables/useSimulationAnimation';
import { useSimulationCore } from './composables/useSimulationCore';
import { useDataTransform } from './composables/useDataTransform';
import { useSimulationFiles } from './composables/useSimulationFiles';
import { useTopology } from './composables/useTopology';
import { useSimulationWebSocket } from './simulation/composables/useSimulationWebSocket';
import { useHealthCheck } from './simulation/composables/useHealthCheck';
import { useSimulationDataManager } from './simulation/composables/useSimulationDataManager';

// 版本号
const version = ref('3.9.0');

// 路由参数
const route = useRoute();
const router = useRouter();
const projectId = computed(() => route.params.projectId);
const versionId = computed(() => route.query.versionId);

function getProjectIdNumber() {
  const id = projectId.value;
  return id ? Number(id) : null;
}

function getVersionIdNumber() {
  const id = versionId.value;
  return id ? Number(id) : undefined;
}

// DAG 组件配置 - 设备列表（从后端获取）
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal');

// DAG 组件引用
const dagRef = ref(null);

// 节点编辑抽屉
const nodeEditDrawerRef = ref(null);
const currentNode = ref(null);
const simulationDialogRef = ref(null);
const messageListRef = ref(null);
const healthCheckDialogRef = ref(null);

// 健康自检
const { runHealthCheck } = useHealthCheck();

// 仿真会话管理
const currentSessionId = ref(null);

// 使用优化的数据管理器
const dataManager = useSimulationDataManager();
const {
  bandwidthData,
  messageData,
  alarmData,
  updateBandwidthData,
  updateMessageData,
  updateAlarmData,
  clearAllData,
} = dataManager;

// UI状态
const pageLoading = ref(true);

// 面板显示控制
const showAlarmPanel = computed(() => alarmData.value.length > 0);
const showPanels = computed(
  () => simulationStatus.value === 'running' || simulationStatus.value === 'completed'
);
// 报文追踪面板常态显示（有数据就显示，或仿真运行中）
const showMessagePanel = computed(() => messageData.value.length > 0 || showPanels.value);

// 可配置的文案和设置
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

// 获取图实例
function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

// 清除图内容
function clearGraphContent(graphInstance) {
  const graph = graphInstance || getGraphInstance();
  if (graph && typeof graph.clearCells === 'function') {
    graph.clearCells();
  }
}

// 初始化 composables
const graphStyleUtils = useGraphStyle();
const animationUtils = useSimulationAnimation();
const simulationCore = useSimulationCore({
  graphStyleUtils,
  animationUtils,
});
const dataTransform = useDataTransform();
const simulationFiles = useSimulationFiles(version);
const topologyUtils = useTopology(
  version,
  getGraphInstance,
  clearGraphContent,
  graphStyleUtils.isSimulationToken
);

// 解构 simulationCore 导出的状态和方法
const {
  simulationStatus,
  simulationSteps,
  simulationPointer,
  simulationLoading,
  simulationNarration,
  simulationTimelinePhases,
  simulationResultPayload,
  simulationLoopCount,
  simulationContinuousMode,
  buildSimulationSteps,
  buildPhaseTimeline,
  announceSimulationSchedule,
  runSimulationFlow,
  stopSimulationRunner,
  queueSimulationResult,
  resetSimulationNarration,
  resetSimulationState,
  setContinuousMode,
} = simulationCore;

/**
 * 重新打开仿真对话框
 */
function handleReopenSimulationDialog() {
  if (!simulationResultPayload.value) {
    ElMessage.warning('暂无仿真结果，请先执行仿真');
    return;
  }
  simulationDialogRef.value?.open(simulationResultPayload.value);
}

/**
 * 停止仿真
 */
async function handleStopSimulation() {
  if (simulationStatus.value !== 'running') {
    return;
  }

  // 调用后端停止仿真
  if (currentSessionId.value) {
    try {
      await stopSimulationSession(currentSessionId.value);
    } catch (err) {
      console.error('停止仿真会话失败:', err);
    }
  }

  // 断开WebSocket
  wsManager.disconnect();

  stopSimulationRunner('idle');
  animationUtils.disposeSimulationAnimations();
  animationUtils.disposeAllSimulationTokens();

  const graph = getGraphInstance();
  if (graph) {
    graphStyleUtils.resetGraphSimulationState(graph);
  }

  resetSimulationState();
  currentSessionId.value = null;
}

/**
 * 执行仿真
 * @param {string} mode - 执行模式：'once' 执行一轮, 'continuous' 持续播放
 */
async function handleRunSimulation(mode = 'continuous') {
  if (simulationLoading.value) {
    return;
  }
  if (simulationStatus.value === 'running') {
    ElMessage.warning('仿真正在执行，请稍后');
    return;
  }

  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('仿真失败：图实例不存在');
    return;
  }

  const currentProjectId = getProjectIdNumber();
  const currentVersionId = getVersionIdNumber();

  if (!currentProjectId) {
    ElMessage.error('仿真失败：缺少工程ID');
    return;
  }

  // 设置仿真模式
  setContinuousMode(mode === 'continuous');

  resetSimulationNarration();
  resetSimulationState();

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning('请至少放置两个设备节点后再生成仿真');
    return;
  }

  if (!edges.length) {
    ElMessage.warning('请先建立设备之间的接口连线');
    return;
  }

  stopSimulationRunner('idle');
  simulationResultPayload.value = null;
  simulationSteps.value = [];
  simulationPointer.value = 0;
  simulationLoading.value = true;

  // 清空之前的数据
  clearAllData();
  wsManager.clearData();

  try {
    // 1. 创建后端仿真会话
    simulationNarration.value = {
      badge: '准备中',
      title: '正在创建仿真会话',
      description: '正在与服务器建立连接...',
      busType: '',
    };

    const createResult = await createSimulationSession({
      projectId: currentProjectId,
      versionId: currentVersionId,
    });

    if (!createResult?.data?.sessionId) {
      throw new Error('创建仿真会话失败');
    }

    currentSessionId.value = createResult.data.sessionId;

    // 2. 启动后端仿真
    simulationNarration.value = {
      badge: '启动中',
      title: '正在启动仿真引擎',
      description: '仿真引擎正在初始化...',
      busType: '',
    };

    await startSimulationSession(currentSessionId.value);

    // 3. 连接WebSocket接收实时数据
    wsManager.connect(currentSessionId.value);

    // 4. 准备前端动画
    const { nodes: nodePayload, edges: edgePayload } = dataTransform.buildSimulationPayload(
      graph,
      graphStyleUtils.isSimulationToken
    );

    const steps = buildSimulationSteps(graph);

    animationUtils.disposeSimulationAnimations();
    animationUtils.disposeAllSimulationTokens();
    graphStyleUtils.resetGraphSimulationState(graph);
    graphStyleUtils.markQueuedEdges(steps);
    simulationSteps.value = steps;
    simulationTimelinePhases.value = buildPhaseTimeline(steps);
    announceSimulationSchedule(steps);
    simulationPointer.value = 0;
    simulationStatus.value = 'running';

    const summary = simulationFiles.buildSimulationSummary(
      nodePayload,
      edgePayload,
      dataTransform.BUS_TYPES
    );
    const designContent = simulationFiles.generateDesignFilePayload(
      '多总线仿真工程',
      version.value,
      nodePayload,
      edgePayload
    );
    const icdContent = simulationFiles.generateIcdFilePayload(
      '多总线仿真工程',
      version.value,
      nodePayload,
      edgePayload
    );
    const timeline =
      simulationTimelinePhases.value?.length > 0
        ? simulationTimelinePhases.value
        : simulationFiles.generateSimulationTimeline(edgePayload);

    queueSimulationResult({
      summary,
      timeline,
      designFile: {
        name: 'bus_design.csv',
        content: designContent,
      },
      icdFile: {
        name: 'interface_control.csv',
        content: icdContent,
      },
    });

    simulationLoading.value = false;

    // 运行前端动画流程
    runSimulationFlow();
  } catch (error) {
    console.error('启动仿真失败:', error);
    ElMessage.error(error?.message || '启动仿真失败，请稍后重试');
    simulationLoading.value = false;
    simulationStatus.value = 'idle';
    currentSessionId.value = null;
    resetSimulationNarration();
  }
}

/**
 * 从后端加载设备列表数据
 */
async function loadDeviceList() {
  loading.value = true;
  try {
    const response = await listDevice({});
    const devices = response?.rows || [];

    if (devices.length === 0) {
      operators.value = [];
      return;
    }

    operators.value = dataTransform.convertDevicesToOperators(devices);
  } catch (error) {
    void error;
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 处理节点双击事件
 */
function handleNodeDblclick({ node }) {
  const graph = dagRef.value?.getGraph();
  const peerDeviceNameByPort = topologyUtils.buildPeerDeviceNameByPort(node, graph);
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;

  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
  };

  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 */
function handleNodeUpdate({ nodeId, name, ports }) {
  const graph = dagRef.value?.getGraph();
  if (!graph) {
    ElMessage.error('更新失败：图实例不存在');
    return;
  }

  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) {
    ElMessage.error('更新失败：节点不存在');
    return;
  }

  const currentData = cellNode.getData() || {};

  const updatedData = {
    ...currentData,
    name: name,
    label: name,
    ports: ports || currentData.ports,
  };

  if (currentData.properties?.content) {
    updatedData.properties = {
      ...currentData.properties,
      content: {
        ...currentData.properties.content,
        label: name,
      },
    };
  }

  cellNode.setData(updatedData, { overwrite: false });
}

/**
 * 保存工程拓扑
 */
function handleSaveTopo() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    ElMessage.error('保存失败：缺少工程ID');
    return;
  }

  topologyUtils
    .saveTopo(currentProjectId, getVersionIdNumber())
    .then((success) => {
      if (success) {
        router.push(`/project/project-detail/index/${currentProjectId}`);
      }
    })
    .catch(() => {
      ElMessage.error('拓扑保存失败，请稍后重试');
    });
}

/**
 * 执行健康自检
 */
function handleHealthCheck() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('无法执行健康检查：图实例不存在');
    return;
  }

  const report = runHealthCheck(graph, graphStyleUtils.isSimulationToken);
  healthCheckDialogRef.value?.open(report);
}

/**
 * 从后端加载并回显已保存的拓扑数据
 */
function restoreSavedTopology() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    return;
  }
  topologyUtils.restoreSavedTopology(currentProjectId, getVersionIdNumber(), dagRef);
}

watch(
  () => [projectId.value, versionId.value],
  () => {
    restoreSavedTopology();
  }
);

// WebSocket连接（用于实时数据推送）
const wsManager = useSimulationWebSocket();
const {
  bandwidthData: wsBandwidthData,
  messagesData: wsMessagesData,
  alarmsData: wsAlarmsData,
  statusData: wsStatusData,
} = wsManager;

// 监听WebSocket带宽数据更新（优化：使用节流）
watch(
  () => wsBandwidthData.value,
  (newData) => {
    updateBandwidthData(newData);
  }
);

// 监听WebSocket报文数据更新（优化：使用节流）
watch(
  () => wsMessagesData.value,
  (newData) => {
    updateMessageData(newData);
  }
);

// 监听WebSocket告警数据更新
watch(
  () => wsAlarmsData.value,
  (newData) => {
    updateAlarmData(newData);
  }
);

// 监听WebSocket状态更新
watch(
  () => wsStatusData.value,
  (newStatus) => {
    if (newStatus) {
      // 更新仿真旁白信息
      if (newStatus.status === 'running') {
        const elapsedTime = newStatus.elapsedTime || 0;
        simulationNarration.value = {
          badge: '运行中',
          title: `仿真持续运行`,
          description: `已运行 ${elapsedTime.toFixed(1)} 秒，报文数: ${newStatus.messageCount || 0}`,
          busType: '',
        };
      } else if (newStatus.status === 'stopped') {
        simulationNarration.value = {
          badge: '已停止',
          title: '仿真已停止',
          description: `总计生成 ${newStatus.messageCount || 0} 条报文`,
          busType: '',
        };
      }
    }
  },
  { deep: true }
);

// 页面加载时获取设备列表并尝试回显拓扑
onMounted(async () => {
  pageLoading.value = true;
  try {
    await loadDeviceList();
    await restoreSavedTopology();
  } finally {
    // 添加短暂延迟以显示加载动画
    setTimeout(() => {
      pageLoading.value = false;
    }, 500);
  }
});

onUnmounted(async () => {
  // 如果仿真正在运行，停止后端仿真
  if (currentSessionId.value && simulationStatus.value === 'running') {
    try {
      await stopSimulationSession(currentSessionId.value);
    } catch (err) {
      console.error('停止仿真会话失败:', err);
    }
  }

  stopSimulationRunner('idle');
  animationUtils.disposeSimulationAnimations();
  animationUtils.disposeAllSimulationTokens();
  wsManager.disconnect();
});
</script>

<style lang="less">
.simulation-page {
  height: calc(100vh - 130px);
  display: flex;
  flex-direction: column;
  &.zx-content-wrap .el-card__body {
    height: 100%;
    .zx-content-wrap__content {
      height: 100%;
    }
  }
}

.simulation-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.simulation-summary {
  margin-bottom: 16px;
}

.simulation-tabs {
  .el-tab-pane {
    min-height: 240px;
  }
}

.simulation-file__header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.simulation-file__viewer {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  max-height: 280px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.simulation-timeline__title {
  font-weight: 600;
  margin-bottom: 4px;
}

.simulation-timeline__desc {
  color: #606266;
  margin: 0;
  font-size: 12px;
}

.simulation-running-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;

  .el-icon {
    font-size: 14px;
  }
}
</style>
