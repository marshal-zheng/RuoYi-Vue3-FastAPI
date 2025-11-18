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

              <!-- 导入功能 -->
              <template v-if="toolbarActionsConfig.importXmind">
                <el-upload
                  ref="xmindUploadRef"
                  :show-file-list="false"
                  :before-upload="handleBeforeImportXmind"
                  :http-request="handleImportXmind"
                  accept=".xmind"
                  :disabled="readonly"
                >
                  <el-button size="small" :disabled="readonly">导入 Xmind</el-button>
                </el-upload>
                <el-divider direction="vertical" />
              </template>
              
              <!-- 导出功能 -->
              <template
                v-if="
                  toolbarActionsConfig.exportPNG ||
                  toolbarActionsConfig.exportPDF ||
                  (toolbarActionsConfig.exportXmind && exportXmindHandler)
                "
              >
                <el-button-group>
                  <el-button
                    v-if="toolbarActionsConfig.exportPNG"
                    size="small"
                    @click="exportPNG"
                    :disabled="readonly"
                  >
                    导出 PNG
                  </el-button>
                  <el-button
                    v-if="toolbarActionsConfig.exportPDF"
                    size="small"
                    @click="exportPDF"
                    :disabled="readonly"
                  >
                    导出 PDF
                  </el-button>
                  <el-button
                    v-if="toolbarActionsConfig.exportXmind && exportXmindHandler"
                    size="small"
                    @click="exportXmind"
                    :disabled="readonly"
                  >
                    导出 Xmind
                  </el-button>
                </el-button-group>
                <el-divider direction="vertical" />
              </template>

              <!-- 工具栏左侧插槽，供业务层扩展 -->
              <slot name="toolbar-left"></slot>
            </div>
            <div class="dag-toolbar__right">
              <slot name="right"></slot>
              <!-- 全屏按钮 -->
              <!-- <el-button size="small" @click="toggleFullscreen">
                <el-icon>
                  <component :is="fullScreenIcon" />
                </el-icon>
              </el-button> -->
            </div>
          </div>
          <!-- 图形视图 -->
          <div class="dag-graph" :class="{ 'no-toolbar': !showToolbar }">
            <!-- 加载状态遮罩 -->
            <div
              v-loading="graphBusy"
              :element-loading-text="graphLoadingText"
              element-loading-background="rgba(255, 255, 255, 0.8)"
              class="dag-graph__loading"
              :class="{ 'is-loading': graphBusy }"
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
              <XFlowBackground color="#fafafa" />
              <XFlowGrid :size="14" type="mesh" :dot-size="2" color="#e6e6e6" />
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
              <div class="dag-graph__control">
                <DagGraphControl :graph="graphInstance" />
              </div>
            </XFlowGraph>
          </div>
        </div>
      </div>
    </div>
  </XFlow>
</template>

<script setup>
import { toRefs, ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { FullScreen, ScaleToOriginal } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { willCreateCycle } from './utils/graphConstraints.js'
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
  XFlowExport
} from '../ZxFlow/components'
import { useExport } from '../ZxFlow/composables'
import DagConnect from './components/DagConnect.vue'
import DagDnd from './components/DagDnd.vue'
import DagGraphControl from './components/DagGraphControl.vue'
import DagInitData from './components/DagInitData.vue'
import { DAG_CONNECTOR, DAG_EDGE, DAG_NODE } from './shapes/registerDagShapes'
import { DAG_EDGE_CONFIG } from './config/edgeConfig.js'
import { DAG_PORT_CONFIG, generateNodePorts } from './config/portConfig.js'
import { dagreLayout } from './utils/layout.js'
import { refreshCollapseState } from './utils/collapse.js'
import { getNodeSizeByLayout } from './utils/nodeGeometry.js'

defineOptions({
  name: 'DAGPage'
})

const connectionEdgeOptions = {
  shape: DAG_EDGE,
  animated: true,
  zIndex: -1,
  attrs: {
    line: {
      stroke: DAG_EDGE_CONFIG.style.normal.stroke,
      strokeWidth: DAG_EDGE_CONFIG.style.normal.strokeWidth,
      targetMarker: null
    }
  }
}

const props = defineProps({
  /**
   * 算子数据列表，支持静态数据、Promise或函数
   * @type {Array<{key: string, title: string, shortDesc?: string, category?: string, ports?: Array}> | Promise | Function}
   */
  operators: {
    type: [Array, Promise, Function],
    default: () => []
  },
  /**
   * 算子数据加载状态
   */
  operatorsLoading: {
    type: Boolean,
    default: false
  },
  /**
   * DnD 组件配置
   */
  dndConfig: {
    type: Object,
    default: () => ({
      title: '算子库',
      searchPlaceholder: '搜索算子、组件...'
    })
  },
  /**
   * 布局方向
   */
  layout: {
    type: String,
    default: 'horizontal'
  },
  /**
   * 图类型（树状图 / 网状图）
   */
  graphType: {
    type: String,
    default: 'tree',
    validator: (value) => ['tree', 'mesh'].includes(value)
  },
  /**
   * 自定义菜单处理器
   */
  customMenuHandler: {
    type: Function,
    default: null
  },
  /**
   * 对齐线配置
   */
  snaplineConfig: {
    type: Object,
    default: () => ({
      enabled: true,
      tolerance: 15, // 增加容差，更容易触发对齐
      sharp: false
    })
  },
  /**
   * 初始图数据，支持静态数据、Promise或函数
   */
  initialGraphData: {
    type: [Object, Promise, Function],
    default: null
  },
  /**
   * 图数据加载状态
   */
  graphLoading: {
    type: Boolean,
    default: false
  },
  /**
   * 是否自动布局
   */
  autoLayout: {
    type: Boolean,
    default: true
  },
  /**
   * 是否显示左侧指标库
   */
  showSidebar: {
    type: Boolean,
    default: true
  },
  /**
   * 是否为只读模式
   */
  readonly: {
    type: Boolean,
    default: false
  },
  /**
   * 是否显示工具栏
   */
  showToolbar: {
    type: Boolean,
    default: true
  },
  /**
   * 导出 Xmind 处理函数
   */
  exportXmindHandler: {
    type: Function,
    default: null
  },
  /**
   * 导入 Xmind 处理函数
   */
  importXmindHandler: {
    type: Function,
    default: null
  },
  /**
   * 工具栏操作显示配置
   */
  toolbarActions: {
    type: Object,
    default: () => ({
      importXmind: true,
      exportPNG: true,
      exportPDF: true,
      exportXmind: true
    })
  }
})

const emit = defineEmits([
  'edit-node',
  'delete-node',
  'copy-node',
  'add-node',
  'save',
  'ready',
  'node-click',
  'node-dblclick',
  'export-xmind',
  'import-xmind'
])

const currentLayout = ref(props.layout === 'vertical' ? 'vertical' : 'horizontal')
const minimapKey = ref(0)
const graphInstance = ref(null)
const dagPageRef = ref(null)
const isFullscreen = ref(false)
const isImporting = ref(false)
const exportActions = useExport(graphInstance)
const xmindUploadRef = ref(null)

// 对齐线配置
const snaplineEnabled = ref(props.snaplineConfig.enabled)
const snaplineTolerance = ref(props.snaplineConfig.tolerance)
const snaplineSharp = ref(props.snaplineConfig.sharp)

// 缩放配置 - 调慢缩放步进
const zoomOptions = {
  factor: 1.05, // 默认是 1.2，改为 1.05 让缩放更平缓
  minScale: 0.1, // 最小缩放比例
  maxScale: 3 // 最大缩放比例
}

const normalizedGraphType = computed(() => (props.graphType === 'mesh' ? 'mesh' : 'tree'))
const isTreeGraphMode = computed(() => normalizedGraphType.value === 'tree')
const graphBusy = computed(() => props.graphLoading || isImporting.value)
const graphLoadingText = computed(() =>
  isImporting.value ? '正在导入 Xmind 文件...' : '正在加载指标体系数据...'
)
const defaultToolbarActions = {
  importXmind: true,
  exportPNG: true,
  exportPDF: true,
  exportXmind: true
}
const toolbarActionsConfig = computed(() => ({
  ...defaultToolbarActions,
  ...(props.toolbarActions || {})
}))
const TREE_PARENT_WARNING_COOLDOWN = 1500
let lastTreeParentWarningAt = 0

const hasEffectiveIncomingEdges = (graph, cell) => {
  if (!graph || !cell) return false
  const viaGraph =
    typeof graph.getIncomingEdges === 'function' ? graph.getIncomingEdges(cell) : null
  const viaCell = typeof cell.getIncomingEdges === 'function' ? cell.getIncomingEdges() : null
  const incoming = Array.isArray(viaGraph) ? viaGraph : Array.isArray(viaCell) ? viaCell : []
  return incoming.some((edge) => {
    if (!edge) return false
    if (typeof edge.isRemoved === 'function') {
      return !edge.isRemoved()
    }
    return true
  })
}

const notifyTreeParentLimit = () => {
  const now = Date.now()
  if (now - lastTreeParentWarningAt < TREE_PARENT_WARNING_COOLDOWN) {
    return
  }
  lastTreeParentWarningAt = now
  ElMessage.warning('树状图每个节点只能有一个直接上级，请先删除已有连线。')
}

// 计算节点层级（到最近根节点的距离，根为第 0 层）
const calculateNodeLevel = (graph, nodeId) => {
  if (!graph || !nodeId) return null
  const visited = new Set()
  const queue = [{ id: nodeId, level: 0 }]
  let maxLevel = 0
  while (queue.length > 0) {
    const { id, level } = queue.shift()
    if (!id || visited.has(id)) continue
    visited.add(id)
    maxLevel = Math.max(maxLevel, level)
    // 优先使用 X6 API 获取入边
    const cell = graph.getCellById?.(id)
    if (!cell) {
      return null
    }
    const incoming = (cell?.getIncomingEdges?.() || graph.getIncomingEdges?.(cell) || []).filter((e) => {
      if (!e) return false
      return typeof e.isRemoved === 'function' ? !e.isRemoved() : true
    })
    if (!incoming.length) {
      return level
    }
    incoming.forEach((edge) => {
      const parentId = edge?.getSourceCellId?.()
      if (parentId && !visited.has(parentId)) {
        queue.push({ id: parentId, level: level + 1 })
      }
    })
  }
  return maxLevel
}

const getNodeLevelFromData = (cell) => {
  if (!cell?.getData) return null
  const data = cell.getData() || {}
  const rawLevel =
    data.properties?.level ??
    data.level ??
    data.properties?.content?.level ??
    data.content?.level
  if (rawLevel === undefined || rawLevel === null) {
    return null
  }
  const numericLevel = Number(rawLevel)
  if (Number.isNaN(numericLevel)) {
    return null
  }
  return Math.max(0, numericLevel - 1)
}

const resolveNodeLevel = (graph, cell, fallbackId) => {
  const structuralLevel = calculateNodeLevel(graph, fallbackId)
  const fromData = getNodeLevelFromData(cell)
  const levels = []
  if (typeof structuralLevel === 'number') levels.push(structuralLevel)
  if (fromData !== null && fromData !== undefined) levels.push(fromData)
  if (levels.length > 0) {
    return Math.max(...levels)
  }
  return 0
}

const removeEdgeIfTreeParentExceeded = (edge) => {
  if (!isTreeGraphMode.value || !edge) return
  const graph = graphInstance.value
  if (!graph) return
  const targetNode = edge.getTargetCell?.()
  if (!targetNode) return
  const incoming =
    graph.getIncomingEdges?.(targetNode) || targetNode.getIncomingEdges?.() || []
  const activeIncoming = (incoming || []).filter((item) => {
    if (!item) return false
    return typeof item.isRemoved === 'function' ? !item.isRemoved() : true
  })
  if (activeIncoming.length > 1) {
    notifyTreeParentLimit()
    // 延迟删除，避免与其他监听器冲突
    setTimeout(() => {
      edge.remove?.()
    }, 0)
  }
}

const connectionOptions = {
  snap: true,
  allowBlank: false,
  allowLoop: false,
  highlight: true,
  connectionPoint: 'anchor',
  anchor: 'center',
  // 显示连接端点为圆形指示
  endpoint: {
    name: 'circle',
    args: { r: 6 }
  },
  connector: DAG_CONNECTOR,
  validateMagnet({ magnet, cell }) {
    if (!magnet) return false
    // 设备节点（device-port-node）：允许任意端口作为起点
    if (cell?.shape === 'device-port-node') return true
    // 普通 DAG 节点：仅允许 bottom/right 作为起点
    const group = magnet.getAttribute('port-group')
    return group === 'bottom' || group === 'right'
  },
  validateConnection({ sourceCell, targetCell, sourceMagnet, targetMagnet, sourceView }) {
    if (!sourceMagnet || !targetMagnet) return false
    const isSourceDevice = sourceCell?.shape === 'device-port-node'
    const isTargetDevice = targetCell?.shape === 'device-port-node'
    // 设备节点参与的连接：放开方向限制
    if (isSourceDevice || isTargetDevice) {
      // 仍然做一次环路校验
      const g = sourceView?.graph
      if (!g) return true
      const sourceId = sourceCell?.id
      const targetId = targetCell?.id
      if (!sourceId || !targetId) return false
      if (willCreateCycle(g, sourceId, targetId)) return false
      return true
    }
    // 普通 DAG 节点之间：保持原有方向限制
    const sourceGroup = sourceMagnet.getAttribute('port-group')
    const targetGroup = targetMagnet.getAttribute('port-group')
    const outputGroups = ['bottom', 'right']
    const inputGroups = ['top', 'left']
    if (!outputGroups.includes(sourceGroup) || !inputGroups.includes(targetGroup)) {
      return false
    }
    // 从 sourceView 获取 graph 实例
    const g = sourceView?.graph
    if (!g) return true
    const sourceId = sourceCell?.id
    const targetId = targetCell?.id
    if (!sourceId || !targetId) return false
    // 树模式下阻止目标节点拥有多个直接上级
    if (isTreeGraphMode.value) {
      const targetHasParent = hasEffectiveIncomingEdges(g, targetCell)
      if (targetHasParent) {
        notifyTreeParentLimit()
        return false
      }
    }
    // 预防成环
    if (willCreateCycle(g, sourceId, targetId)) return false
    // 跨层级校验延后到 edge:connected 进行，以避免在起点拉线时提前提示
    return true
  }
}

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
  showToolbar
} = toRefs(props)

const toggleNodePortsVisibility = (node, visible, view) => {
  if (!node) return
  const graph = graphInstance.value
  const nodeView = view || graph?.findViewByCell?.(node)
  if (!nodeView?.container) return
  const portBodies = nodeView.container.querySelectorAll('.x6-port-body')
  const hideInputPorts = visible && isTreeGraphMode.value && hasEffectiveIncomingEdges(graph, node)
  portBodies.forEach((el) => {
    const group = el.getAttribute('port-group')
    const isInputGroup = group === 'top' || group === 'left'
    const allowVisible = visible && (!hideInputPorts || !isInputGroup)
    const opacity = allowVisible ? DAG_PORT_CONFIG.activeOpacity : DAG_PORT_CONFIG.defaultOpacity
    el.style.opacity = String(opacity)
    el.style.pointerEvents = allowVisible ? 'auto' : 'none'
  })
}

const handleNodeMouseEnter = ({ node, view }) => {
  if (!node || readonly.value) return
  toggleNodePortsVisibility(node, true, view)
}

const handleNodeMouseLeave = ({ node, view }) => {
  if (!node) return
  toggleNodePortsVisibility(node, false, view)
}

const handleNodeAdded = ({ node, view }) => {
  toggleNodePortsVisibility(node, false, view)
}

// 处理 operators 数据，支持 Promise 和静态数据
const operators = ref([])
const internalOperatorsLoading = ref(false)

// 加载 operators 数据的函数
const loadOperatorsData = async (dataSource) => {
  try {
    let data

    // 如果是函数，调用函数获取数据
    if (typeof dataSource === 'function') {
      data = await dataSource()
    }
    // 如果是Promise，等待解析
    else if (dataSource && typeof dataSource.then === 'function') {
      data = await dataSource
    } else if (Array.isArray(dataSource)) {
      data = dataSource
    } else {
      data = []
    }

    operators.value = data || []
  } catch (error) {
    console.error('加载算子数据失败:', error)
    operators.value = []
  } finally {
    internalOperatorsLoading.value = false
  }
}

// 监听 operators prop 变化
watch(
  operatorsProp,
  (newOperators) => {
    if (newOperators) {
      internalOperatorsLoading.value = true
      loadOperatorsData(newOperators)
    }
  },
  { immediate: true }
)

watch(
  readonly,
  (isReadonly) => {
    if (!isReadonly) {
      return
    }
    const graph = graphInstance.value
    if (!graph) return
    const nodes = graph.getNodes?.() || []
    nodes.forEach((node) => {
      const view = graph.findViewByCell?.(node)
      toggleNodePortsVisibility(node, false, view)
    })
  }
)

// 合并加载状态 - 外部传入的 loading 状态 或 内部处理 Promise 的 loading 状态
const finalOperatorsLoading = computed(() => {
  return operatorsLoading.value || internalOperatorsLoading.value
})

// 全屏图标
const fullScreenIcon = computed(() => (isFullscreen.value ? ScaleToOriginal : FullScreen))

const onToolbarLayoutChange = (dir) => {
  currentLayout.value = dir === 'LR' ? 'horizontal' : 'vertical'
  // 布局切换后强制重建小地图，避免插件偶发不同步/空白
  minimapKey.value += 1
}

// 通过单选按钮切换布局（横向/纵向），并实时应用 dagre 布局
const onLayoutRadioChange = async (val) => {
  try {
    currentLayout.value = val === 'vertical' ? 'vertical' : 'horizontal'
    minimapKey.value += 1
    const g = graphInstance.value
    if (g) {
      const dir = currentLayout.value === 'horizontal' ? 'LR' : 'TB'
      await dagreLayout(g, dir)
      refreshCollapseState(g)
      g.centerContent()
    }
  } catch (e) {
    console.warn('切换布局失败:', e)
  }
}

const exportPNG = () => {
  try {
    exportActions.exportPNG('graph.png', {
      backgroundColor: '#ffffff',
      padding: 20,
      quality: 1,
      scale: 2
    })
  } catch (error) {
    console.warn('导出 PNG 失败:', error)
  }
}

const exportPDF = async () => {
  try {
    await exportActions.exportPDF('graph.pdf', {
      backgroundColor: '#ffffff',
      padding: 20,
      quality: 1,
      scale: 2
    })
  } catch (error) {
    console.warn('导出 PDF 失败:', error)
  }
}

const exportXmind = async () => {
  try {
    if (props.exportXmindHandler && typeof props.exportXmindHandler === 'function') {
      const graphData = getSaveData()
      await props.exportXmindHandler(graphData)
      emit('export-xmind', graphData)
    } else {
      console.warn('导出 Xmind 处理函数未提供')
    }
  } catch (error) {
    console.warn('导出 Xmind 失败:', error)
  }
}

// 导入 Xmind 文件前的验证
const handleBeforeImportXmind = (file) => {
  const isXmind = file.name.toLowerCase().endsWith('.xmind')
  if (!isXmind) {
    ElMessage.error('只能上传 .xmind 格式的文件！')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB！')
    return false
  }
  
  return true
}

// 导入 Xmind 文件
const handleImportXmind = async ({ file }) => {
  let loadingMessage = null
  try {
    if (!props.importXmindHandler || typeof props.importXmindHandler !== 'function') {
      ElMessage.warning('导入 Xmind 处理函数未提供')
      return
    }
    
    // 检查是否有现有数据（编辑模式）
    const graph = graphInstance.value
    const hasExistingData = graph && (graph.getNodes()?.length > 0 || graph.getEdges()?.length > 0)
    
    // 如果是编辑模式且有现有数据，需要确认是否覆盖
    if (hasExistingData) {
      try {
        await ElMessageBox.confirm(
          '导入 Xmind 文件将覆盖当前的指标体系内容，是否继续？',
          '确认导入',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
      } catch {
        // 用户取消
        return
      }
    }
    
    isImporting.value = true
    
    // 调用父组件提供的导入处理函数
    const response = await props.importXmindHandler(file)
    
    loadingMessage?.close()
    
    // 检查返回的 detailContent
    if (response && response.detailContent) {
      // 渲染导入的数据到图中（覆盖现有数据）
      await renderImportedData(response.detailContent)
      emit('import-xmind', response)
    }
  } catch (error) {
    loadingMessage?.close()
  } finally {
    isImporting.value = false
  }
}

// 渲染导入的数据到图中（覆盖现有数据）
const renderImportedData = async (detailContent) => {
  const graph = graphInstance.value
  if (!graph) {
    console.warn('图实例不存在，无法渲染导入数据')
    return
  }
  
  try {
    // 解析 detailContent
    let graphData
    if (typeof detailContent === 'string') {
      try {
        graphData = JSON.parse(detailContent)
      } catch (parseError) {
        throw new Error('detailContent 格式错误，无法解析 JSON')
      }
    } else {
      graphData = detailContent
    }
    
    // 验证数据格式
    if (!graphData || !graphData.nodes || !Array.isArray(graphData.nodes)) {
      throw new Error('导入的数据格式不正确，缺少 nodes 数组')
    }
    
    // 清空当前图形（覆盖现有数据）
    graph.clearCells()

    const layoutOrientation = currentLayout.value === 'horizontal' ? 'horizontal' : 'vertical'
    const nodeSize = getNodeSizeByLayout(layoutOrientation)

    const childMap = new Map()
    ;(graphData.edges || []).forEach((edge) => {
      if (!edge?.sourceNodeId || !edge?.targetNodeId) return
      if (!childMap.has(edge.sourceNodeId)) {
        childMap.set(edge.sourceNodeId, new Set())
      }
      childMap.get(edge.sourceNodeId).add(edge.targetNodeId)
    })

    // 添加节点（保持与初始数据加载时一致的样式/配置）
    graphData.nodes.forEach((nodeData) => {
      const nodeType =
        nodeData.type ||
        (nodeData.properties?.level === 1 ? 'root-node' : nodeData.properties?.level > 1 ? 'sub-node' : 'leaf-node')
      const label = nodeData.properties?.content?.label || nodeData.label || '未命名节点'
      graph.addNode({
        id: nodeData.id,
        shape: DAG_NODE,
        x: nodeData.x || 0,
        y: nodeData.y || 0,
        width: nodeSize.width,
        height: nodeSize.height,
        data: {
          type: nodeType || 'leaf-node',
          properties: nodeData.properties || {},
          label,
          status: 'default',
          layoutDirection: layoutOrientation,
          collapsed: nodeData.collapsed === true,
          hasChildren: (childMap.get(nodeData.id)?.size || 0) > 0,
          originalData: nodeData
        },
        ports: generateNodePorts(nodeType || 'leaf-node'),
        draggable: true,
        locked: false
      })
    })

    // 添加边
    const edges = Array.isArray(graphData.edges) ? graphData.edges : []
    edges.forEach((edgeData) => {
      const weight = edgeData.properties?.weight ?? edgeData.weight
      const weightEditable = edgeData.properties?.weightEditable !== false
      const labels =
        weight !== undefined && weight !== null
          ? [
              {
                attrs: {
                  text: {
                    text: String(weight),
                    ...DAG_EDGE_CONFIG.label.weight
                  },
                  rect: {
                    ...DAG_EDGE_CONFIG.label.rect
                  }
                },
                position: DAG_EDGE_CONFIG.label.position
              }
            ]
          : undefined

      graph.addEdge({
        id: edgeData.id,
        shape: DAG_EDGE,
        source: { cell: edgeData.sourceNodeId, port: 'b' },
        target: { cell: edgeData.targetNodeId, port: 't' },
        data: {
          weight,
          weightEditable,
          properties: edgeData.properties || {}
        },
        labels
      })
    })

    // 应用布局
    const dir = currentLayout.value === 'horizontal' ? 'LR' : 'TB'
    await dagreLayout(graph, dir)
    refreshCollapseState(graph)
    
    // 居中显示
    graph.centerContent()
    
    console.log('成功渲染导入的数据:', {
      nodesCount: graphData.nodes.length,
      edgesCount: graphData.edges?.length || 0
    })
  } catch (error) {
    console.error('渲染导入数据失败:', error)
    throw new Error(error.message || '渲染导入数据失败')
  }
}

// 数据加载/布局完成后，强制重建小地图
const onGraphDataUpdated = () => {
  minimapKey.value += 1
}

// 保存数据处理
const onSave = (graphData) => {
  emit('save', graphData)
}

// 节点单击事件透传
const onNodeClick = ({ node, event, type }) => {
  // 选中与该节点相关的所有边
  if (node && graphInstance.value) {
    const graph = graphInstance.value
    
    // 获取与节点相连的所有边（入边和出边）
    const connectedEdges = graph.getConnectedEdges(node)
    
    // 取消所有边的选中状态
    const allEdges = graph.getEdges()
    allEdges.forEach(edge => {
      edge.removeTools()
    })
    
    // 选中与该节点相关的边
    if (connectedEdges && connectedEdges.length > 0) {
      connectedEdges.forEach(edge => {
        graph.select(edge)
      })
    }
  }
  
  emit('node-click', { node, event, type })
}

// 节点双击事件透传
const onNodeDblclick = ({ node, event, type }) => {
  console.log('DAGPage - onNodeDblclick 被调用:', { node, event, type })
  emit('node-dblclick', { node, event, type })
}


// 全屏功能
const toggleFullscreen = async () => {
  try {
    const elem = dagPageRef.value
    if (!elem) {
      console.warn('DAG 容器元素不存在')
      return
    }

    if (!isFullscreen.value) {
      // 进入全屏
      if (elem.requestFullscreen) {
        await elem.requestFullscreen()
      } else if (elem.webkitRequestFullscreen) {
        await elem.webkitRequestFullscreen()
      } else if (elem.mozRequestFullScreen) {
        await elem.mozRequestFullScreen()
      } else if (elem.msRequestFullscreen) {
        await elem.msRequestFullscreen()
      }
    } else {
      // 退出全屏
      if (document.exitFullscreen) {
        await document.exitFullscreen()
      } else if (document.webkitExitFullscreen) {
        await document.webkitExitFullscreen()
      } else if (document.mozCancelFullScreen) {
        await document.mozCancelFullScreen()
      } else if (document.msExitFullscreen) {
        await document.msExitFullscreen()
      }
    }
  } catch (error) {
    console.warn('全屏切换失败:', error)
    ElMessage.warning('全屏切换失败')
  }
}

// 监听全屏状态变化
const handleFullscreenChange = () => {
  const wasFullscreen = isFullscreen.value
  isFullscreen.value = !!(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  )
  console.log('全屏状态变化:', { 
    from: wasFullscreen, 
    to: isFullscreen.value,
    showToolbar: showToolbar.value 
  })
}

// 添加全屏事件监听
onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('mozfullscreenchange', handleFullscreenChange)
  document.addEventListener('MSFullscreenChange', handleFullscreenChange)
})

// 清理全屏事件监听
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
  document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
})

// 暴露方法供外部调用
const getSaveData = () => {
  // 这里直接调用 DagToolbar 的保存逻辑
  const g = graphInstance.value
  if (!g) {
    console.warn('图实例不存在')
    return null
  }

  try {
    // 清理节点数据，移除 originalData
    const cleanNodeData = (nodeData) => {
      if (!nodeData) return nodeData
      const cleaned = { ...nodeData }
      if (cleaned.originalData) {
        delete cleaned.originalData
      }
      return cleaned
    }

    // 获取所有节点数据，格式与data.json保持一致
    const nodes = g.getNodes().map((node) => {
      const position = node.getPosition()
      const nodeData = cleanNodeData(node.getData()) || {}

      return {
        id: node.id,
        type: nodeData.type || 'leaf-node', // 从节点数据中获取type
        x: position.x,
        y: position.y,
        properties: nodeData.properties || {}
      }
    })

    // 获取所有边数据，格式与data.json保持一致
    const edges = g.getEdges().map((edge) => {
      const sourceNode = edge.getSourceNode()
      const targetNode = edge.getTargetNode()
      const sourcePoint = edge.getSourcePoint()
      const targetPoint = edge.getTargetPoint()
      const edgeData = edge.getData() || {}

      return {
        id: edge.id,
        type: 'mindmap-edge', // 固定为mindmap-edge
        sourceNodeId: edge.getSourceCellId(),
        targetNodeId: edge.getTargetCellId(),
        startPoint: { x: sourcePoint.x, y: sourcePoint.y },
        endPoint: { x: targetPoint.x, y: targetPoint.y },
        properties: edgeData.properties || {},
        pointsList: edge.getVertices() || []
      }
    })

    // 构建完整的图数据，格式与data.json保持一致
    const graphData = {
      nodes,
      edges
    }

    console.log('格式化后的图数据:', graphData)
    return graphData
  } catch (error) {
    console.error('获取图数据时出错:', error)
    return null
  }
}

// 提供获取图实例的方法，供外部调用
const getGraph = () => {
  return graphInstance.value
}

// 处理边标签的双击编辑
const handleEdgeLabelEdit = async (edge) => {
  if (!edge || props.readonly) return
  
  const edgeData = edge.getData() || {}
  const weight = edgeData.properties?.weight ?? edgeData.weight
  const weightEditable = edgeData.weightEditable !== false
  
  if (!weightEditable) {
    return
  }
  
  const currentWeight = weight !== undefined && weight !== null ? String(weight) : ''
  // 计算允许范围：同一起点的所有出边权重之和 ≤ 100
  // const g = graphInstance.value
  // let allowedMax = 100
  // if (g) {
  //   const sourceNode = edge.getSourceNode()
  //   const outgoing = sourceNode && typeof g.getOutgoingEdges === 'function'
  //     ? (g.getOutgoingEdges(sourceNode) || [])
  //     : (g.getEdges?.().filter(e => e.getSourceCellId?.() === edge.getSourceCellId?.()) || [])
  //   let sumOthers = 0
  //   outgoing.forEach(e => {
  //     if (!e || e.id === edge.id) return
  //     const d = e.getData?.() || {}
  //     const w = d.properties?.weight ?? d.weight
  //     const n = typeof w === 'number' ? w : parseFloat(w)
  //     if (!isNaN(n) && n > 0) sumOthers += n
  //   })
  //   allowedMax = Math.max(0, 100 - sumOthers)
  // }
  
  try {
    const { value } = await ElMessageBox.prompt('请输入权重值（留空则移除权重）', '编辑权重', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: currentWeight,
      inputPlaceholder: `请输入权重值，留空则移除`,
      inputValidator: (val) => {
        if (val === '' || val === null || typeof val === 'undefined') return true
        const n = parseFloat(val)
        if (isNaN(n)) return '请输入有效的数字'
        // if (n < 0 || n > allowedMax) return `请输入 0 ~ ${allowedMax} 范围内的数值`
        return true
      }
    })
    
    // 允许为空，表示移除权重
    let newWeight = null
    if (value !== '' && value !== null && typeof value !== 'undefined') {
      newWeight = parseFloat(value)
      if (isNaN(newWeight)) {
        ElMessage.warning('请输入有效的数字')
        return
      }
    }
    
    // 更新边的数据 - 同时更新顶层weight和properties.weight
    edge.setData({
      ...edgeData,
      weight: newWeight,
      properties: {
        ...(edgeData.properties || {}),
        weight: newWeight
      }
    })
    
    // 更新边的标签显示
    if (newWeight !== null && newWeight !== undefined) {
      edge.setLabels([
        {
          attrs: {
            text: {
              text: String(newWeight),
              ...DAG_EDGE_CONFIG.label.weight
            },
            rect: {
              ...DAG_EDGE_CONFIG.label.rect
            }
          },
          position: DAG_EDGE_CONFIG.label.position
        }
      ])
      ElMessage.success('权重已更新')
    } else {
      edge.setLabels([])
      ElMessage.success('权重已移除')
    }
  } catch (error) {
    // 用户取消输入
  }
}

// 处理XFlowGraph的ready事件，确保standardInteractions正确初始化
const onGraphReady = (graph, keyboardMgr, standardInteractions) => {
  console.log('DAGPage - onGraphReady 被调用')
  console.log('DAGPage - 图实例:', graph)
  console.log('DAGPage - 图中的节点数量:', graph?.getNodes?.()?.length || 0)

  // 保存图实例引用
  graphInstance.value = graph

  // 添加边标签双击编辑功能
  graph.on('edge:dblclick', ({ edge, e }) => {
    console.log('edge:dblclick 触发', { edge: edge?.id, target: e?.target?.tagName })
    // 双击边直接编辑权重，不限制必须点击文本
    handleEdgeLabelEdit(edge)
  })

  // 节点 hover 时显示连接桩，离开后隐藏
  try {
    graph.off('node:mouseenter', handleNodeMouseEnter)
    graph.off('node:mouseleave', handleNodeMouseLeave)
    graph.off('node:added', handleNodeAdded)
  } catch (error) {
    // 忽略 off 失败
  }
  graph.on('node:mouseenter', handleNodeMouseEnter)
  graph.on('node:mouseleave', handleNodeMouseLeave)
  graph.on('node:added', handleNodeAdded)
  const existingNodes = graph.getNodes?.() || []
  existingNodes.forEach((node) => {
    const view = graph.findViewByCell?.(node)
    toggleNodePortsVisibility(node, false, view)
  })

  // 连接时显示端口（为容器添加/移除 connecting 类）
  try {
    const container = graph.container?.parentElement || graph.container
    if (container) {
      graph.on('edge:connecting', () => {
        container.classList.add('connecting')
      })
      graph.on('edge:connected', (event) => {
        container.classList.remove('connecting')
        removeEdgeIfTreeParentExceeded(event?.edge)
        try {
          const edge = event?.edge
          if (!edge) return
          const g = graphInstance.value
          if (!g) return
          const sourceId = edge.getSourceCellId?.()
          const targetId = edge.getTargetCellId?.()
          if (!sourceId || !targetId) return
          const sourceCell = edge.getSourceNode?.()
          const targetCell = edge.getTargetNode?.()
          // 目标节点在连线前是否已存在父节点（排除当前边）
          const prevIncoming = (g.getIncomingEdges?.(targetCell) || targetCell?.getIncomingEdges?.() || []).filter((e) => {
            if (!e || e.id === edge.id) return false
            return typeof e.isRemoved === 'function' ? !e.isRemoved() : true
          })
          const hadParentBefore = prevIncoming.length > 0
          const sLevel = resolveNodeLevel(g, sourceCell, sourceId)
          const tLevel = resolveNodeLevel(g, targetCell, targetId)
          // 若目标节点之前没有父节点，则允许作为新子节点连接，不做跨层级拦截
          if (hadParentBefore && Math.abs(sLevel - tLevel) > 1) {
            const sData = sourceCell?.getData?.() || {}
            const tData = targetCell?.getData?.() || {}
            const sName = sData.label || sData.properties?.content?.label || '源节点'
            const tName = tData.label || tData.properties?.content?.label || '目标节点'
            ElMessage.warning({
              message: `不允许跨层级连线：${sName}（第${sLevel + 1}层）与 ${tName}（第${tLevel + 1}层）仅允许相邻层级`,
              duration: 3000,
              showClose: true
            })
            setTimeout(() => {
              edge.remove?.()
            }, 0)
          }
        } catch (e) {}
      })
      graph.on('edge:connection-removed', () => {
        container.classList.remove('connecting')
      })
    }
  } catch (e) {}

  // 点击空白区域取消所有边的选中状态
  graph.on('blank:click', () => {
    const allEdges = graph.getEdges()
    allEdges.forEach(edge => {
      graph.unselect(edge)
    })
  })

  // 测试：手动触发一个点击事件看看
  setTimeout(() => {
    const nodes = graph?.getNodes?.() || []
    console.log('DAGPage - 2秒后检查节点:', nodes.length)
    if (nodes.length > 0) {
      console.log('DAGPage - 第一个节点:', nodes[0].id, nodes[0].getData())
    }
  }, 2000)

  // 检查对齐线插件是否正确加载
  setTimeout(() => {
    const snaplinePlugin = graph.getPlugin('snapline')
    if (snaplinePlugin) {
      console.log('✅ Snapline plugin loaded successfully:', snaplinePlugin)
      console.log('Snapline config:', {
        enabled: snaplineEnabled.value,
        tolerance: snaplineTolerance.value,
        sharp: snaplineSharp.value
      })
    } else {
      console.warn('❌ Snapline plugin not found')
    }
  }, 1000)

  // 这里可以添加额外的图形初始化逻辑
  // standardInteractions已经在XFlowGraph中正确设置了selectionHandler
  console.log('DAG Graph ready:', { graph, keyboardMgr, standardInteractions })
}

// 暴露给外部使用的方法
defineExpose({
  getSaveData,
  getGraph,
  renderImportedData
})
</script>

<style lang="scss">
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
    background: linear-gradient(180deg, #fbfdff 0%, #e6ecff 42%, #ccd6ff 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.08);
    box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.65), 8px 0 24px rgba(15, 23, 42, 0.06);

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
    background: #fff;

    .dag-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 42px;
      padding-left: 16px;
      background-color: #f6f8fa;
      border-bottom: 1px solid #eaebed;

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

/* 端口显示过渡 */
:deep(.x6-port-body) {
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.connecting :deep(.x6-port-body) {
  opacity: 1 !important;
  pointer-events: auto;
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
  border-color: #1890ff;
  border-radius: 2px;
  box-shadow: 0 0 0 4px #d4e8fe;

  &.success {
    border-color: #52c41a;
    box-shadow: 0 0 0 4px #ccecc0;
  }

  &.failed {
    border-color: #ff4d4f;
    box-shadow: 0 0 0 4px #fedcdc;
  }
}

/* 边的交互样式 */
.x6-edge:hover path:nth-child(1) {
  stroke: #66b1ff;
  stroke-width: 5px;
}

.x6-edge:hover path:nth-child(2) {
  stroke: #1890ff;
  stroke-width: 5px;
}

.x6-edge-selected path:nth-child(1) {
  stroke: #409eff !important;
  stroke-width: 6px !important;
  filter: drop-shadow(0 0 6px rgba(24, 144, 255, 0.4));
}

.x6-edge-selected path:nth-child(2) {
  stroke: #1890ff;
  stroke-width: 6px !important;
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
    background: #ff4d4f;
    color: white;
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
  border: 1px solid #e0e0e0 !important;
  border-radius: 6px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(4px) !important;

  &:hover {
    border-color: #1890ff !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  }
}

/* 小地图视窗边框增强 */
:deep(.xflow-minimap) {
  .x6-widget-minimap-viewport {
    stroke: #1890ff !important;
    stroke-width: 2px !important;
    fill: rgba(24, 144, 255, 0.08) !important;
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
      fill: #1890ff !important;
      stroke: #1890ff !important;
    }

    &.adsorbed {
      opacity: 1;
      fill: #52c41a !important;
      stroke: #52c41a !important;
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
  stroke: #ff4d4f !important;
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
}

/* 全屏模式样式 */
.zx-dag-page.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background: #fff !important;
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
