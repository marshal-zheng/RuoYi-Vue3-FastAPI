<template>
  <XFlow>
    <div
      ref="dagPageRef"
      class="zx-dag-page"
      :class="{ readonly: readonly, fullscreen: isFullscreen }"
    >
      <div class="dag-container">
        <div v-if="showSidebar" class="dag-left">
          <div class="dag-left__header">算子组件库</div>
          <DagDnd
            :operators="operators"
            :loading="finalOperatorsLoading"
            :title="dndConfig.title"
            :search-placeholder="dndConfig.searchPlaceholder"
            :layout="currentLayout"
            :text-config="dndConfig.textConfig"
            :graph-instance="graphInstance"
            :readonly="readonly"
          />
        </div>
        <div class="dag-center">
          <div v-if="showToolbar" class="dag-toolbar">
            <div class="dag-toolbar__left">
              <!-- 布局控制 -->
              <el-radio-group
                size="small"
                :model-value="currentLayout"
                @change="onLayoutRadioChange"
                :disabled="readonly"
              >
                <el-radio-button label="horizontal">横向</el-radio-button>
                <el-radio-button label="vertical">纵向</el-radio-button>
              </el-radio-group>
              <el-divider direction="vertical" />

              <!-- 导出功能 -->
              <el-button-group>
                <el-button size="small" @click="exportPNG" :disabled="readonly">导出 PNG</el-button>
                <el-button size="small" @click="exportPDF" :disabled="readonly">导出 PDF</el-button>
                <el-button
                  v-if="exportXmindHandler"
                  size="small"
                  @click="exportXmind"
                  :disabled="readonly"
                >
                  导出 Xmind
                </el-button>
              </el-button-group>
              <!-- <el-divider direction="vertical" /> -->

              <!-- 矩阵视图按钮 -->
              <!-- <el-button size="small" type="primary" @click="showMatrixDialog" :disabled="readonly">
                矩阵视图
              </el-button> -->
            </div>
            <div class="dag-toolbar__right">
              <slot name="right"></slot>
              <!-- 全屏按钮 -->
              <el-button size="small" @click="toggleFullscreen">
                <el-icon>
                  <component :is="fullScreenIcon" />
                </el-icon>
              </el-button>
            </div>
          </div>
          <!-- 图形视图 -->
          <div class="dag-graph" :class="{ 'no-toolbar': !showToolbar }">
            <!-- 加载状态遮罩 -->
            <div
              v-loading="graphLoading"
              element-loading-text="正在加载指标体系数据..."
              class="dag-graph__loading"
              :class="{ 'is-loading': graphLoading }"
            ></div>

            <XFlowGraph
              :readonly="readonly"
              :connection-options="connectionOptions"
              :connection-edge-options="connectionEdgeOptions"
              :select-options="{ showEdgeSelectionBox: true, showNodeSelectionBox: false }"
              :custom-menu-handler="customMenuHandler"
              :fit-view="false"
              :zoom-options="zoomOptions"
              :enable-double-click-fit="false"
              @ready="onGraphReady"
              @node-click="onNodeClick"
              @node-dblclick="onNodeDblclick"
            >
              <XFlowState :edge-animation-duration="30" />
              <XFlowClipboard />
              <XFlowHistory />
              <XFlowSnapline
                :enabled="snaplineEnabled"
                :tolerance="snaplineTolerance"
                :sharp="snaplineSharp"
              />
              <XFlowExport />
              <DagInitData
                :initial-data="initialGraphData"
                :auto-layout="autoLayout"
                :layout-direction="currentLayout === 'horizontal' ? 'LR' : 'TB'"
                @data-updated="onGraphDataUpdated"
              />
              <DagConnect />
              <XFlowBackground :color="backgroundConfig.color" />
              <XFlowGrid
                :size="gridConfig.size"
                :type="gridConfig.type"
                :dot-size="gridConfig.dotSize"
                :color="gridConfig.color"
              />
              <!-- 小地图 -->
              <!-- <XFlowMinimap 
                :key="minimapKey"
                :width="200" 
                :height="150" 
                :simple="true"
                :padding="24"
                :style="{ right: '24px', top: '24px' }"
                class="dag-minimap"
              /> -->
              <div v-if="showGraphControl" class="dag-graph__control">
                <DagGraphControl :graph="graphInstance" />
              </div>
            </XFlowGraph>
          </div>

          <!-- 矩阵视图对话框 -->
          <!-- <DagMatrixDialog
            v-model="matrixDialogVisible"
            :title="matrixDialogTitle"
            :graph-data="currentGraphData"
            :readonly="readonly"
            :loading="matrixLoading"
            :columns="matrixColumns"
            :node-renderer="matrixNodeRenderer"
            :node-transformer="matrixNodeTransformer"
            :edit-form-component="matrixEditFormComponent"
            :default-expand-all="true"
            :show-level-tags="false"
            @update:graph-data="onMatrixGraphDataUpdate"
            @node-add="onMatrixNodeAdd"
            @node-update="onMatrixNodeUpdate"
            @node-delete="onMatrixNodeDelete"
            @row-click="onMatrixRowClick"
            @save="onMatrixSave"
            @close="onMatrixDialogClose"
          /> -->
        </div>
      </div>
    </div>
  </XFlow>
</template>

<script setup>
import { toRefs, ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { FullScreen, ScaleToOriginal } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

import { willCreateCycle } from './utils/graphConstraints.js';
import {
  XFlow,
  XFlowGraph,
  XFlowClipboard,
  XFlowState,
  XFlowHistory,
  XFlowGrid,
  XFlowBackground,
  XFlowMinimap,
  XFlowContextMenu,
  XFlowSnapline,
  XFlowExport,
} from '../ZxFlow/components';
import { useExport } from '../ZxFlow/composables';
import DagConnect from './components/DagConnect.vue';
import DagDnd from './components/DagDnd.vue';
import DagGraphControl from './components/DagGraphControl.vue';
import DagInitData from './components/DagInitData.vue';
// import DagMatrixDialog from './components/DagMatrixDialog.vue'
import { DAG_CONNECTOR, DAG_EDGE } from './shapes/registerDagShapes';
import { dagreLayout } from './utils/layout.js';
import { refreshCollapseState } from './utils/collapse.js';

defineOptions({
  name: 'DAGPage',
});

// 连接时的边配置（静态默认，颜色在 edge:connecting 事件里动态覆盖）
const connectionEdgeOptions = {
  shape: DAG_EDGE,
  animated: true,
  zIndex: -1,
  attrs: {
    line: {
      stroke: '#C2C8D5',
      strokeWidth: 5,
      targetMarker: null,
    },
  },
};

const props = defineProps({
  /**
   * 算子数据列表，支持静态数据、Promise或函数
   * @type {Array<{key: string, title: string, shortDesc?: string, category?: string, ports?: Array}> | Promise | Function}
   */
  operators: {
    type: [Array, Promise, Function],
    default: () => [],
  },
  /**
   * 算子数据加载状态
   */
  operatorsLoading: {
    type: Boolean,
    default: false,
  },
  /**
   * DnD 组件配置
   */
  dndConfig: {
    type: Object,
    default: () => ({
      title: '算子库',
      searchPlaceholder: '搜索算子、组件...',
    }),
  },
  /**
   * 布局方向
   */
  layout: {
    type: String,
    default: 'horizontal',
  },
  /**
   * 自定义菜单处理器
   */
  customMenuHandler: {
    type: Function,
    default: null,
  },
  /**
   * 对齐线配置
   */
  snaplineConfig: {
    type: Object,
    default: () => ({
      enabled: true,
      tolerance: 15, // 增加容差，更容易触发对齐
      sharp: false,
    }),
  },
  /**
   * 初始图数据，支持静态数据、Promise或函数
   */
  initialGraphData: {
    type: [Object, Promise, Function],
    default: null,
  },
  /**
   * 图数据加载状态
   */
  graphLoading: {
    type: Boolean,
    default: false,
  },
  /**
   * 是否自动布局
   */
  autoLayout: {
    type: Boolean,
    default: true,
  },
  /**
   * 是否显示左侧指标库
   */
  showSidebar: {
    type: Boolean,
    default: true,
  },
  /**
   * 是否为只读模式
   */
  readonly: {
    type: Boolean,
    default: false,
  },
  /**
   * 是否显示工具栏
   */
  showToolbar: {
    type: Boolean,
    default: true,
  },
  /**
   * 矩阵视图列配置
   */
  matrixColumns: {
    type: Array,
    default: () => [],
  },
  /**
   * 矩阵视图节点渲染器
   */
  matrixNodeRenderer: {
    type: Function,
    default: null,
  },
  /**
   * 矩阵视图节点转换器
   */
  matrixNodeTransformer: {
    type: Function,
    default: null,
  },
  /**
   * 矩阵视图编辑表单组件
   */
  matrixEditFormComponent: {
    type: [String, Object],
    default: null,
  },
  /**
   * 导出 Xmind 处理函数
   */
  exportXmindHandler: {
    type: Function,
    default: null,
  },
  /**
   * 是否显示缩放控制栏
   */
  showGraphControl: {
    type: Boolean,
    default: true,
  },
  /**
   * 主题模式：light | dark
   */
  theme: {
    type: String,
    default: '',
  },
});

// 根据主题计算背景和网格配置
const backgroundConfig = computed(() => {
  if (props.theme === 'dark') {
    return { color: '#0a0e14' };
  }
  return { color: undefined };
});

const gridConfig = computed(() => {
  if (props.theme === 'dark') {
    return {
      size: 20,
      type: 'mesh',
      dotSize: 1,
      color: 'rgba(34, 211, 238, 0.12)',
    };
  }
  return {
    size: 14,
    type: 'mesh',
    dotSize: 2,
    color: undefined,
  };
});

const emit = defineEmits([
  'edit-node',
  'delete-node',
  'copy-node',
  'add-node',
  'save',
  'ready',
  'node-click',
  'node-dblclick',
  'matrix-node-add',
  'matrix-node-update',
  'matrix-node-delete',
  'matrix-row-click',
  'view-mode-change',
  'export-xmind',
]);

const currentLayout = ref(props.layout === 'vertical' ? 'vertical' : 'horizontal');
const minimapKey = ref(0);
const graphInstance = ref(null);
const matrixViewRef = ref(null);
const dagPageRef = ref(null);
const isFullscreen = ref(false);
const exportActions = useExport(graphInstance);

// 矩阵视图对话框管理
const matrixDialogVisible = ref(false);
const matrixLoading = ref(false);
const currentGraphData = ref(null);

// 对齐线配置
const snaplineEnabled = ref(props.snaplineConfig.enabled);
const snaplineTolerance = ref(props.snaplineConfig.tolerance);
const snaplineSharp = ref(props.snaplineConfig.sharp);

// 缩放配置 - 调慢缩放步进
const zoomOptions = {
  factor: 1.05, // 默认是 1.2，改为 1.05 让缩放更平缓
  minScale: 0.1, // 最小缩放比例
  maxScale: 3, // 最大缩放比例
};

const connectionOptions = {
  snap: true,
  allowBlank: false,
  allowLoop: false,
  highlight: true,
  connectionPoint: 'anchor',
  anchor: 'center',
  connector: DAG_CONNECTOR,
  validateMagnet({ magnet, cell }) {
    if (!magnet) return false;
    // 设备节点（device-port-node）：允许任意端口作为起点
    if (cell?.shape === 'device-port-node') return true;
    // 普通 DAG 节点：仅允许 bottom/right 作为起点
    const group = magnet.getAttribute('port-group');
    return group === 'bottom' || group === 'right';
  },
  validateConnection({ sourceCell, targetCell, sourceMagnet, targetMagnet, sourceView }) {
    if (!sourceMagnet || !targetMagnet) return false;
    const isSourceDevice = sourceCell?.shape === 'device-port-node';
    const isTargetDevice = targetCell?.shape === 'device-port-node';
    // 设备节点参与的连接：放开方向限制
    if (isSourceDevice || isTargetDevice) {
      // 仍然做一次环路校验
      const g = sourceView?.graph;
      if (!g) return true;
      const sourceId = sourceCell?.id;
      const targetId = targetCell?.id;
      if (!sourceId || !targetId) return false;
      if (willCreateCycle(g, sourceId, targetId)) return false;
      return true;
    }
    // 普通 DAG 节点之间：保持原有方向限制
    const sourceGroup = sourceMagnet.getAttribute('port-group');
    const targetGroup = targetMagnet.getAttribute('port-group');
    const outputGroups = ['bottom', 'right'];
    const inputGroups = ['top', 'left'];
    if (!outputGroups.includes(sourceGroup) || !inputGroups.includes(targetGroup)) {
      return false;
    }
    // 从 sourceView 获取 graph 实例
    const g = sourceView?.graph;
    if (!g) return true;
    const sourceId = sourceCell?.id;
    const targetId = targetCell?.id;
    if (!sourceId || !targetId) return false;
    // 预防成环
    if (willCreateCycle(g, sourceId, targetId)) return false;
    return true;
  },
};

// 保持对 props 的响应式引用，避免值拷贝导致后续更新丢失
const {
  operators: operatorsProp,
  operatorsLoading,
  dndConfig,
  layout,
  customMenuHandler,
  initialGraphData,
  graphLoading,
  autoLayout,
  showSidebar,
  readonly,
  showToolbar,
} = toRefs(props);

// 处理 operators 数据，支持 Promise 和静态数据
const operators = ref([]);
const internalOperatorsLoading = ref(false);

// 加载 operators 数据的函数
const loadOperatorsData = async (dataSource) => {
  try {
    let data;

    // 如果是函数，调用函数获取数据
    if (typeof dataSource === 'function') {
      data = await dataSource();
    }
    // 如果是Promise，等待解析
    else if (dataSource && typeof dataSource.then === 'function') {
      data = await dataSource;
    } else if (Array.isArray(dataSource)) {
      data = dataSource;
    } else {
      data = [];
    }

    operators.value = data || [];
  } catch (error) {
    console.error('加载算子数据失败:', error);
    operators.value = [];
  } finally {
    internalOperatorsLoading.value = false;
  }
};

// 监听 operators prop 变化
watch(
  operatorsProp,
  (newOperators) => {
    if (newOperators) {
      internalOperatorsLoading.value = true;
      loadOperatorsData(newOperators);
    }
  },
  { immediate: true }
);

// 合并加载状态 - 外部传入的 loading 状态 或 内部处理 Promise 的 loading 状态
const finalOperatorsLoading = computed(() => {
  return operatorsLoading.value || internalOperatorsLoading.value;
});

// 矩阵视图相关计算属性
const matrixDialogTitle = computed(() => {
  return '矩阵视图 - 数据管理';
});

// 全屏图标
const fullScreenIcon = computed(() => (isFullscreen.value ? ScaleToOriginal : FullScreen));

const onToolbarLayoutChange = (dir) => {
  currentLayout.value = dir === 'LR' ? 'horizontal' : 'vertical';
  // 布局切换后强制重建小地图，避免插件偶发不同步/空白
  minimapKey.value += 1;
};

// 通过单选按钮切换布局（横向/纵向），并实时应用 dagre 布局
const onLayoutRadioChange = async (val) => {
  try {
    currentLayout.value = val === 'vertical' ? 'vertical' : 'horizontal';
    minimapKey.value += 1;
    const g = graphInstance.value;
    if (g) {
      const dir = currentLayout.value === 'horizontal' ? 'LR' : 'TB';
      await dagreLayout(g, dir);
      refreshCollapseState(g);
      g.centerContent();
    }
  } catch (e) {
    console.warn('切换布局失败:', e);
  }
};

const exportPNG = () => {
  try {
    exportActions.exportPNG('graph.png', {
      backgroundColor: '#ffffff',
      padding: 20,
      quality: 1,
      scale: 2,
    });
  } catch (error) {
    console.warn('导出 PNG 失败:', error);
  }
};

const exportPDF = async () => {
  try {
    await exportActions.exportPDF('graph.pdf', {
      backgroundColor: '#ffffff',
      padding: 20,
      quality: 1,
      scale: 2,
    });
  } catch (error) {
    console.warn('导出 PDF 失败:', error);
  }
};

const exportXmind = async () => {
  try {
    if (props.exportXmindHandler && typeof props.exportXmindHandler === 'function') {
      const graphData = getSaveData();
      await props.exportXmindHandler(graphData);
      emit('export-xmind', graphData);
    } else {
      console.warn('导出 Xmind 处理函数未提供');
    }
  } catch (error) {
    console.warn('导出 Xmind 失败:', error);
  }
};

// 数据加载/布局完成后，强制重建小地图
const onGraphDataUpdated = () => {
  minimapKey.value += 1;
};

// 保存数据处理
const onSave = (graphData) => {
  emit('save', graphData);
};

// 节点单击事件透传
const onNodeClick = ({ node, event, type }) => {
  emit('node-click', { node, event, type });
};

// 节点双击事件透传
const onNodeDblclick = ({ node, event, type }) => {
  console.log('DAGPage - onNodeDblclick 被调用:', { node, event, type });
  emit('node-dblclick', { node, event, type });
};

// 显示矩阵视图对话框
const showMatrixDialog = async () => {
  try {
    matrixLoading.value = true;
    const graphData = getSaveData();
    currentGraphData.value = graphData;
    matrixDialogVisible.value = true;
  } catch (error) {
    console.error('获取图数据失败:', error);
    ElMessage.error('获取图数据失败');
  } finally {
    matrixLoading.value = false;
  }
};

// 矩阵视图事件处理
const onMatrixGraphDataUpdate = (graphData) => {
  currentGraphData.value = graphData;
  // 同步更新到图形视图
  if (graphInstance.value && graphData) {
    // 这里需要重新加载图数据
    // 可以触发 DagInitData 的数据更新
    emit('save', graphData);
  }
};

const onMatrixNodeAdd = (nodeData) => {
  emit('matrix-node-add', nodeData);
};

const onMatrixNodeUpdate = (nodeData) => {
  emit('matrix-node-update', nodeData);
};

const onMatrixNodeDelete = (nodeData) => {
  emit('matrix-node-delete', nodeData);
};

const onMatrixRowClick = (data) => {
  emit('matrix-row-click', data);
};

const onMatrixSave = (graphData) => {
  // 保存矩阵视图的更改到图形视图
  currentGraphData.value = graphData;
  emit('save', graphData);
};

const onMatrixDialogClose = () => {
  matrixDialogVisible.value = false;
};

// 全屏功能
const toggleFullscreen = async () => {
  try {
    const elem = dagPageRef.value;
    if (!elem) {
      console.warn('DAG 容器元素不存在');
      return;
    }

    if (!isFullscreen.value) {
      // 进入全屏
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        await elem.webkitRequestFullscreen();
      } else if (elem.mozRequestFullScreen) {
        await elem.mozRequestFullScreen();
      } else if (elem.msRequestFullscreen) {
        await elem.msRequestFullscreen();
      }
    } else {
      // 退出全屏
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        await document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        await document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        await document.msExitFullscreen();
      }
    }
  } catch (error) {
    console.warn('全屏切换失败:', error);
    ElMessage.warning('全屏切换失败');
  }
};

// 监听全屏状态变化
const handleFullscreenChange = () => {
  const wasFullscreen = isFullscreen.value;
  isFullscreen.value = !!(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  );
  console.log('全屏状态变化:', {
    from: wasFullscreen,
    to: isFullscreen.value,
    showToolbar: showToolbar.value,
  });
};

// 添加全屏事件监听
onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('mozfullscreenchange', handleFullscreenChange);
  document.addEventListener('MSFullscreenChange', handleFullscreenChange);
});

// 清理全屏事件监听
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
  document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
});

// 暴露方法供外部调用
const getSaveData = () => {
  // 这里直接调用 DagToolbar 的保存逻辑
  const g = graphInstance.value;
  if (!g) {
    console.warn('图实例不存在');
    return null;
  }

  try {
    // 清理节点数据，移除 originalData
    const cleanNodeData = (nodeData) => {
      if (!nodeData) return nodeData;
      const cleaned = { ...nodeData };
      if (cleaned.originalData) {
        delete cleaned.originalData;
      }
      return cleaned;
    };

    // 获取所有节点数据，格式与data.json保持一致
    const nodes = g.getNodes().map((node) => {
      const position = node.getPosition();
      const nodeData = cleanNodeData(node.getData()) || {};

      return {
        id: node.id,
        type: nodeData.type || 'leaf-node', // 从节点数据中获取type
        x: position.x,
        y: position.y,
        properties: nodeData.properties || {},
      };
    });

    // 获取所有边数据，格式与data.json保持一致
    const edges = g.getEdges().map((edge) => {
      const sourceNode = edge.getSourceNode();
      const targetNode = edge.getTargetNode();
      const sourcePoint = edge.getSourcePoint();
      const targetPoint = edge.getTargetPoint();
      const edgeData = edge.getData() || {};

      return {
        id: edge.id,
        type: 'mindmap-edge', // 固定为mindmap-edge
        sourceNodeId: edge.getSourceCellId(),
        targetNodeId: edge.getTargetCellId(),
        startPoint: { x: sourcePoint.x, y: sourcePoint.y },
        endPoint: { x: targetPoint.x, y: targetPoint.y },
        properties: edgeData.properties || {},
        pointsList: edge.getVertices() || [],
      };
    });

    // 构建完整的图数据，格式与data.json保持一致
    const graphData = {
      nodes,
      edges,
    };

    console.log('格式化后的图数据:', graphData);
    return graphData;
  } catch (error) {
    console.error('获取图数据时出错:', error);
    return null;
  }
};

// 提供获取图实例的方法，供外部调用
const getGraph = () => {
  return graphInstance.value;
};

// 处理XFlowGraph的ready事件，确保standardInteractions正确初始化
const onGraphReady = (graph, keyboardMgr, standardInteractions) => {
  console.log('DAGPage - onGraphReady 被调用');
  console.log('DAGPage - 图实例:', graph);
  console.log('DAGPage - 图中的节点数量:', graph?.getNodes?.()?.length || 0);

  // 保存图实例引用
  graphInstance.value = graph;

  // 测试：手动触发一个点击事件看看
  setTimeout(() => {
    const nodes = graph?.getNodes?.() || [];
    console.log('DAGPage - 2秒后检查节点:', nodes.length);
    if (nodes.length > 0) {
      console.log('DAGPage - 第一个节点:', nodes[0].id, nodes[0].getData());
    }
  }, 2000);

  // 检查对齐线插件是否正确加载
  setTimeout(() => {
    const snaplinePlugin = graph.getPlugin('snapline');
    if (snaplinePlugin) {
      console.log('✅ Snapline plugin loaded successfully:', snaplinePlugin);
      console.log('Snapline config:', {
        enabled: snaplineEnabled.value,
        tolerance: snaplineTolerance.value,
        sharp: snaplineSharp.value,
      });
    } else {
      console.warn('❌ Snapline plugin not found');
    }
  }, 1000);

  // 这里可以添加额外的图形初始化逻辑
  // standardInteractions已经在XFlowGraph中正确设置了selectionHandler
  console.log('DAG Graph ready:', { graph, keyboardMgr, standardInteractions });
};

// 暴露给外部使用的方法
defineExpose({
  getSaveData,
  getGraph,
});
</script>

<style lang="less">
/* SVG foreignObject 修复 */
.zx-dag-page foreignObject > body {
  margin: 0;
  display: block;
  place-items: initial;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  min-height: 100%;
}

/* 主容器样式 */
.zx-dag-page {
  width: 100%;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;

  .dag-container {
    display: flex;
    width: 100%;
    // height: 100vh;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
  }

  /* 左侧边栏 */
  .dag-left {
    display: flex;
    flex-direction: column;
    width: 240px;
    height: 100%;
    background: var(--zx-semantic-surface-panel-fill);

    &__header {
      display: none; // 隐藏原有的头部，因为DagDnd组件现在有自己的头部
    }
  }

  /* 中心区域 */
  .dag-center {
    position: relative;
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    height: 100%;
    outline: none;
    background: var(--zx-semantic-surface-elevated);

    .dag-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 42px;
      padding: 0 16px;
      background-color: var(--zx-semantic-surface-panel-fill);
      border-bottom: 1px solid var(--zx-semantic-border-subtle);

      &__left,
      &__right {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .dag-graph {
      position: relative;
      flex: 1;
      min-height: 0;
      width: 100%;
      overflow: hidden;

      &__loading {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 100;

        &.is-loading {
          pointer-events: all;
        }

        &:not(.is-loading) {
          pointer-events: none;
          display: none;
        }
      }

      &__control {
        position: absolute;
        right: 24px;
        bottom: 24px;
        z-index: 10;
      }
    }
  }

  /* XFlow 图形容器 */
  .xflow-graph {
    width: 100%;
    height: 100%;
  }
}

/* X6 节点和形状修复 */
.zx-dag-page .x6-node[data-shape='dag-node'] {
  .vue-shape-view {
    width: 100% !important;
    height: 100% !important;
    box-sizing: border-box !important;
  }
}

/* 节点选中状态样式 */
.x6-node-selected .zx-dag-node {
  border-color: var(--zx-semantic-accent-base);
  border-radius: 2px;
  box-shadow: 0 0 0 4px var(--zx-semantic-fill-selected);

  &.success {
    border-color: var(--zx-semantic-status-success);
    box-shadow: 0 0 0 4px var(--el-color-success-light-8);
  }

  &.failed {
    border-color: var(--zx-semantic-status-danger);
    box-shadow: 0 0 0 4px var(--el-color-danger-light-8);
  }
}

/* 边的交互样式 */
.x6-edge:hover path:nth-child(2) {
  stroke: var(--zx-semantic-accent-base);
  stroke-width: 1px;
}

.x6-edge-selected path:nth-child(2) {
  stroke: var(--zx-semantic-accent-base);
  stroke-width: 1.5px !important;
}

/* 锁定节点的视觉样式 */
.zx-dag-page .x6-node[data-locked='true'] .zx-dag-node {
  opacity: 0.5;
  cursor: not-allowed;

  &::after {
    content: '🔒';
    position: absolute;
    top: -8px;
    right: -8px;
    font-size: 12px;
    background: var(--zx-semantic-status-danger);
    color: var(--zx-semantic-status-danger-on-fill);
    border-radius: 50%;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
}

/* 小地图样式 */
.dag-minimap {
  border: 1px solid var(--zx-semantic-border-default) !important;
  border-radius: 6px !important;
  box-shadow: var(--zx-semantic-surface-overlay-depth) !important;
  background: var(--zx-semantic-surface-overlay-fill) !important;
  backdrop-filter: blur(4px) !important;

  &:hover {
    border-color: var(--zx-semantic-accent-base) !important;
    box-shadow: var(--zx-semantic-surface-overlay-depth) !important;
  }
}

/* 小地图视窗边框增强 */
:deep(.xflow-minimap) {
  .x6-widget-minimap-viewport {
    stroke: var(--zx-semantic-accent-base) !important;
    stroke-width: 2px !important;
    fill: var(--zx-semantic-fill-selected) !important;
    shape-rendering: crispEdges;
  }
}

/* 端口连接点控制 */
.zx-dag-page {
  /* 普通 DAG 节点的连接桩默认隐藏 */
  .x6-node[data-shape='dag-node'] .x6-port-body {
    opacity: 0;
    transition: opacity 0.2s ease-in-out;

    &.available {
      opacity: 1;
      fill: var(--zx-semantic-accent-base) !important;
      stroke: var(--zx-semantic-accent-base) !important;
    }

    &.adsorbed {
      opacity: 1;
      fill: var(--zx-semantic-status-success) !important;
      stroke: var(--zx-semantic-status-success) !important;
    }
  }

  /* 设备节点的连接桩始终可见 */
  .x6-node[data-shape='device-port-node'] .x6-port-body {
    opacity: 1 !important;
  }

  /* 连接模式时显示所有端口 */
  &.connecting .x6-port-body {
    opacity: 1;
  }
}

/* 对齐线样式 - 增强可见性 */
:deep(.x6-widget-snapline) {
  opacity: 0.9 !important;
  pointer-events: none;
  z-index: 9999;
}

:deep(.x6-widget-snapline-horizontal),
:deep(.x6-widget-snapline-vertical) {
  stroke: var(--zx-semantic-status-danger) !important;
  stroke-width: 2 !important;
  stroke-dasharray: 8, 4 !important;
  opacity: 0.9 !important;
  animation: snapline-pulse 1s ease-in-out infinite alternate;
}

@keyframes snapline-pulse {
  from {
    opacity: 0.7;
  }
  to {
    opacity: 1;
  }
}

/* 只读模式样式 */
.zx-dag-page.readonly {
  .dag-left {
    opacity: 0.8;
    pointer-events: none;
  }

  .dag-toolbar {
    opacity: 0.8;
  }

  .x6-node {
    cursor: default !important;
  }

  .x6-port-body {
    display: none !important;
  }

  &::after {
    content: '只读模式';
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--zx-semantic-status-danger);
    color: var(--zx-semantic-status-danger-on-fill);
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }
}

/* 全屏模式样式 */
.zx-dag-page.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background: var(--zx-semantic-surface-elevated) !important;
  margin: 0 !important;
  padding: 0 !important;

  .dag-container {
    height: 100vh !important;
  }

  .dag-toolbar {
    display: flex !important;
  }

  .dag-toolbar__right {
    display: flex !important;
  }
}
</style>
