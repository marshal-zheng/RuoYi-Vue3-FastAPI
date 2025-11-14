<template>
  <div class="xflow-graph" :class="className" :style="style">
    <div ref="containerRef" class="xflow-graph-container"></div>
    <div class="xflow-graph-wrapper">
      <slot></slot>
    </div>

    <!-- 右键菜单 -->
    <XFlowContextMenu
      v-if="standardInteractions && standardInteractions.contextMenu"
      :context-menu="standardInteractions.contextMenu"
      @menu-click="handleContextMenuClick"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Graph, Options, Shape } from '@antv/x6'
import { Keyboard } from '@antv/x6-plugin-keyboard'
import { Scroller } from '@antv/x6-plugin-scroller'
import { useGraphInstance } from '../composables/useGraphInstance'
import { useKeyboardManager } from '../composables/useKeyboardManager'
import { useClipboard } from '../composables/useClipboard'
import { useHistory } from '../composables/useHistory'
import { useStandardInteractions } from '../composables/useStandardInteractions'
import XFlowContextMenu from './XFlowContextMenu.vue'

// Props 定义
const props = defineProps({
  className: {
    type: String,
    default: ''
  },
  style: {
    type: Object,
    default: () => ({})
  },
  readonly: {
    type: Boolean,
    default: false
  },
  virtual: {
    type: Boolean,
    default: false
  },
  minScale: {
    type: Number,
    default: 0.05
  },
  maxScale: {
    type: Number,
    default: 12
  },
  zoomable: {
    type: Boolean,
    default: true
  },
  zoomOptions: {
    type: Object,
    default: () => ({})
  },
  pannable: {
    type: Boolean,
    default: true
  },
  panOptions: {
    type: Object,
    default: () => ({})
  },
  embedable: {
    type: Boolean,
    default: false
  },
  embedOptions: {
    type: Object,
    default: () => ({})
  },
  restrict: {
    type: Boolean,
    default: false
  },
  restrictOptions: {
    type: Object,
    default: () => ({})
  },
  connectionOptions: {
    type: Object,
    default: () => ({})
  },
  onPortRendered: {
    type: Function,
    default: null
  },
  onEdgeLabelRendered: {
    type: Function,
    default: null
  },
  createCellView: {
    type: Function,
    default: null
  },
  selectOptions: {
    type: Object,
    default: () => ({})
  },
  keyboardOptions: {
    type: Object,
    default: () => ({})
  },
  scroller: {
    type: Boolean,
    default: false
  },
  scrollerOptions: {
    type: Object,
    default: () => ({})
  },
  connectionEdgeOptions: {
    type: Object,
    default: () => ({})
  },
  defaultHighlightOptions: {
    type: Object,
    default: () => ({})
  },
  embedHighlightOptions: {
    type: Object,
    default: () => ({})
  },
  nodeAvailableHighlightOptions: {
    type: Object,
    default: () => ({})
  },
  magnetAvailableHighlightOptions: {
    type: Object,
    default: () => ({})
  },
  magnetAdsorbedHighlightOptions: {
    type: Object,
    default: () => ({})
  },
  centerView: {
    type: Boolean,
    default: false
  },
  centerViewOptions: {
    type: Object,
    default: () => ({})
  },
  fitView: {
    type: Boolean,
    default: false
  },
  fitViewOptions: {
    type: Object,
    default: () => ({})
  },
  // 标准交互配置
  enableStandardInteractions: {
    type: Boolean,
    default: true
  },
  enableContextMenu: {
    type: Boolean,
    default: true
  },
  enableDoubleClickFit: {
    type: Boolean,
    default: true
  },
  contextMenuOptions: {
    type: Object,
    default: () => ({})
  },
  // 自定义右键菜单项（向后兼容）
  customMenuItems: {
    type: Object,
    default: () => ({})
  },
  // 自定义菜单处理器（新方式）
  customMenuHandler: {
    type: Function,
    default: null
  },
  // 锁定模式：节点不可拖拽移动
  locked: {
    type: Boolean,
    default: false
  },
  // 自定义节点锁定判断：返回 true 表示该节点锁定（不可拖拽）
  isNodeLocked: {
    type: Function,
    default: null
  },
  // 分组子元素是否可拖拽（有父节点时），默认 true
  groupChildDraggable: {
    type: Boolean,
    default: true
  },
  // 分组边界是否随子元素拖拽自适应，默认 true
  groupAutoResize: {
    type: Boolean,
    default: true
  },
  // 分组内边距（用于自适应与边界限制），默认 16
  groupPadding: {
    type: Number,
    default: 16
  }
})

const containerRef = ref(null)
const graph = useGraphInstance()
const emit = defineEmits(['ready', 'node-click', 'node-dblclick'])

// 缓存事件处理器，便于在重新初始化或销毁时解绑
let nodeClickHandler = null

// 键盘管理器
const {
  initKeyboardManager,
  setInteractionMode,
  setClipboardHandler,
  setHistoryHandler,
  INTERACTION_MODES
} = useKeyboardManager(graph)

// 标准交互管理器
const standardInteractions = props.enableStandardInteractions
  ? useStandardInteractions(graph, {
      enableContextMenu: props.enableContextMenu && !props.readonly, // 只读模式禁用右键菜单
      enableDoubleClickFit: props.enableDoubleClickFit,
      contextMenuOptions: {
        ...props.contextMenuOptions,
        customItems: props.customMenuItems,
        customMenuHandler: props.customMenuHandler
      },
      // 当未开启边的选择框时，不允许边被选中/框选
      allowEdgeSelection:
        props.selectOptions?.showEdgeSelectionBox === true ||
        props.selectOptions?.allowEdgeSelection === true
    })
  : null

// 初始化 Graph
const initGraph = async () => {
  await nextTick()

  if (!containerRef.value) return

  const g = new Graph({
    container: containerRef.value,
    autoResize: true,
    virtual: props.virtual,
    scaling: {
      min: props.minScale,
      max: props.maxScale
    },
    // 关键：确保交互功能启用，这对 vue-shape 特别重要
    interacting: true,
    // 确保右键菜单不会干扰事件
    preventDefaultContextMenu: false,
    preventDefaultBlankAction: false,
    // 启用内置选择功能
    selecting: {
      enabled: true,
      multiple: true,
      rubberband: true,
      movable: true,
      showNodeSelectionBox: true,
      showEdgeSelectionBox: props.selectOptions?.showEdgeSelectionBox === true,
      ...props.selectOptions
    },
    connecting: {
      ...props.connectionOptions,
      allowBlank: false,
      allowLoop: false,
      allowEdge: false,
      highlight: true,
      snap: true,
      // 关键：使用端口锚点作为连接点，避免在 normal 路由下出现箭头与连线偏移
      anchor: 'center',
      connectionPoint: 'anchor',
      validateConnection(args) {
        // 只读模式下禁止所有连接
        if (props.readonly) {
          return false
        }
        const validator = props.connectionOptions?.validateConnection
        if (typeof validator === 'function') {
          return validator.call(props.connectionOptions, args)
        }
        const { sourceMagnet, targetMagnet } = args
        return !!(sourceMagnet && targetMagnet)
      },
      createEdge() {
        return new Shape.Edge({
          ...props.connectionEdgeOptions
        })
      }
    },
    // 关键：开启嵌入与吸附支持
    embedding: {
      enabled: true,
      findParent({ node }) {
        // 允许所有节点作为父容器
        const bbox = node.getBBox()
        const candidates = g.getNodes()
        return candidates.filter((candidate) => {
          if (candidate === node) return false
          if (node.getAncestors()?.includes(candidate)) return false
          const cb = candidate.getBBox()
          return cb.containsRect(bbox)
        })
      }
    },
    highlighting: {
      default: {
        name: 'stroke',
        args: {
          padding: 3,
          attrs: {
            strokeWidth: 3,
            stroke: '#1890ff'
          }
        },
        ...props.defaultHighlightOptions
      },
      embedding: {
        name: 'stroke',
        args: {
          padding: 3,
          attrs: {
            strokeWidth: 3,
            stroke: '#52c41a'
          }
        },
        ...props.embedHighlightOptions
      },
      nodeAvailable: {
        name: 'className',
        args: {
          className: 'available'
        },
        ...props.nodeAvailableHighlightOptions
      },
      magnetAvailable: {
        name: 'className',
        args: {
          className: 'available'
        },
        ...props.magnetAvailableHighlightOptions
      },
      magnetAdsorbed: {
        name: 'className',
        args: {
          className: 'adsorbed'
        },
        ...props.magnetAdsorbedHighlightOptions
      }
    },
    onPortRendered: props.onPortRendered,
    onEdgeLabelRendered: props.onEdgeLabelRendered,
    createCellView: props.createCellView
  })

  // 使用内置 selecting（替代有已知问题的 selection 插件）
  // 详见 https://github.com/antvis/X6/issues/2110
  // selecting 相关配置在 Graph 构造器中指定
  g.use(new Keyboard({ enabled: true, ...props.keyboardOptions }))

  if (props.scroller) {
    g.use(new Scroller({ enabled: true, ...props.scrollerOptions }))
  }

  // 设置 graph 实例
  if (graph) {
    graph.value = g
  }

  // 初始应用交互与限制配置
  updateZoom(props.zoomable, props.zoomOptions)
  updatePan(props.pannable, props.panOptions)
  updateEmbed(props.embedable, props.embedOptions)
  updateRestrict(props.restrict, props.restrictOptions)
  updateReadonly(props.readonly)

  console.log('XFlowGraph - 图实例初始化完成:', g)
  console.log('XFlowGraph - 图中的节点数量:', g.getNodes?.()?.length || 0)

  // 初始化键盘管理器
  const keyboardMgr = initKeyboardManager()

  // 接入剪贴板与历史处理器（用于快捷键与右键菜单）
  try {
    const clipboardApi = useClipboard(graph)
    const historyApi = useHistory(graph)

    setClipboardHandler((action) => {
      switch (action) {
        case 'copy':
          clipboardApi.copy()
          break
        case 'paste':
          clipboardApi.paste()
          break
        case 'cut':
          clipboardApi.cut()
          break
        default:
          break
      }
    })

    setHistoryHandler((action) => {
      switch (action) {
        case 'undo':
          historyApi.undo()
          break
        case 'redo':
          historyApi.redo()
          break
        default:
          break
      }
    })

    // 将处理器同步给标准交互（右键菜单）
    if (standardInteractions && typeof standardInteractions.setupHandlers === 'function') {
      standardInteractions.setupHandlers(clipboardApi, historyApi)
    }
  } catch (e) {
    // 忽略组合式初始化异常，保持基本交互可用
  }
  // 将边选择开关同步给 keyboardManager
  keyboardMgr.options.allowEdgeSelection =
    props.selectOptions?.showEdgeSelectionBox === true ||
    props.selectOptions?.allowEdgeSelection === true

  // 初始化标准交互（在键盘管理器之后）
  if (standardInteractions) {
    // 直接传递 graph 实例
    standardInteractions.setupStandardEvents(g)
  }

  // 节点单击事件转发（统一由 XFlowGraph 对外抛出）
  if (nodeClickHandler) {
    try {
      g.off('node:click', nodeClickHandler)
    } catch (e) {}
  }
  nodeClickHandler = ({ node, e }) => {
    if (!node) return
    console.log('XFlowGraph - node:click 事件触发:', { node, detail: e?.detail, event: e })
    emit('node-click', { node, event: e, type: 'node' })
    const detail = e?.detail
    console.log('XFlowGraph - 检测双击, detail =', detail)
    if (detail === 2) {
      console.log('XFlowGraph - 触发 node-dblclick 事件')
      emit('node-dblclick', { node, event: e, type: 'node' })
    }
  }
  console.log('XFlowGraph - 绑定 node:click 事件监听器')
  g.on('node:click', nodeClickHandler)

  // 测试：添加更底层的事件监听
  g.on('node:mousedown', ({ node }) => {
    console.log('XFlowGraph - node:mousedown 事件触发:', node?.id)
  })
  g.on('node:mouseup', ({ node }) => {
    console.log('XFlowGraph - node:mouseup 事件触发:', node?.id)
  })

  // 同时监听 X6 原生的双击事件（如果存在）
  g.on('node:dblclick', ({ node, e }) => {
    console.log('XFlowGraph - node:dblclick 原生事件触发:', { node, event: e })
    if (!node) return
    emit('node-dblclick', { node, event: e, type: 'node' })
  })

  // 底层事件兜底日志：判断事件是否到达 Graph 层
  g.on('cell:click', ({ cell, e }) => {
    console.log('XFlowGraph - cell:click 事件触发:', {
      cell,
      isNode: cell?.isNode?.(),
      isEdge: cell?.isEdge?.(),
      detail: e?.detail
    })
  })
  g.on('cell:dblclick', ({ cell, e }) => {
    console.log('XFlowGraph - cell:dblclick 事件触发:', {
      cell,
      isNode: cell?.isNode?.(),
      isEdge: cell?.isEdge?.()
    })
  })

  // 容器原生 dblclick 捕获（用于排查是否被上层遮挡）
  try {
    containerRef?.value?.addEventListener?.(
      'dblclick',
      (ev) => {
        console.log('XFlowGraph - 容器原生 dblclick 捕获:', ev?.target)
      },
      true
    )
  } catch (e) {}

  // 向外通知已就绪，同时传递键盘管理器和标准交互
  emit('ready', g, keyboardMgr, standardInteractions)

  return g
}

// 销毁 Graph
const destroyGraph = () => {
  if (!graph || !graph.value) return

  try {
    if (nodeClickHandler) {
      graph.value.off('node:click', nodeClickHandler)
    }
  } catch (e) {}

  graph.value.dispose()
  graph.value = null
  nodeClickHandler = null
}

// 统一应用交互策略（只读/锁定/默认）
const applyInteractions = () => {
  if (!graph || !graph.value) return

  // 只读模式：禁用编辑功能，保留查看和事件功能
  if (props.readonly) {
    graph.value.options.interacting = {
      // 节点不允许拖拽移动
      nodeMovable: false,
      // 边不允许操作
      edgeMovable: false,
      edgeLabelMovable: false,
      // 保留节点选择功能（用于查看信息）
      magnetConnectable: false // 禁用连接端口
      // 保留其他查看功能，如缩放、平移等在其他地方控制
    }
    return
  }

  const nodeMovable = (view) => {
    const cell = view.cell
    // 基础可拖拽检查：节点自身显式禁用拖拽则不可移动
    const draggableAllowed = cell.prop('draggable') !== false
    if (!draggableAllowed) return false

    // 分组子元素拖拽开关：当节点有父节点时生效
    try {
      const parent = cell.getParent && cell.getParent()
      if (parent && props.groupChildDraggable === false) {
        return false
      }
    } catch (e) {}

    // 全局锁定或自定义锁定逻辑
    try {
      if (props.locked === true) {
        return false
      }

      if (typeof props.isNodeLocked === 'function') {
        return props.isNodeLocked(cell, view) ? false : true
      }
    } catch (e) {
      // 自定义回调异常时，出于安全默认禁止移动
      return false
    }

    return true
  }

  graph.value.options.interacting = {
    nodeMovable,
    // 禁用边的拖拽移动，避免出现可拖拽但无法移动的选框
    edgeMovable: false,
    edgeLabelMovable: (view) => {
      const cell = view.cell
      return cell.prop('labelDraggable') === true
    },
    // 关键：确保事件可以穿透到 foreignObject 内的 Vue 组件
    magnetConnectable: true
  }

  // 关键修复：启用 interacting 功能，确保事件正常工作
  if (graph.value.options.interacting === false) {
    graph.value.options.interacting = true
  }
}

// 保持原有 API，内部改为调用统一方法
const updateReadonly = () => {
  applyInteractions()
}

// 更新缩放设置
const updateZoom = (zoomable, zoomOptions) => {
  if (!graph || !graph.value) return

  if (zoomable) {
    graph.value.enableMouseWheel()
    graph.value.options.mousewheel = {
      ...Options.defaults.mousewheel,
      ...zoomOptions,
      enabled: true
    }
  } else {
    graph.value.disableMouseWheel()
  }
}

// 更新平移设置
const updatePan = (pannable, panOptions) => {
  if (!graph || !graph.value) return

  if (pannable) {
    graph.value.options.panning = {
      ...Options.defaults.panning,
      enabled: true,
      ...panOptions
    }
    graph.value.enablePanning()
  } else {
    graph.value.disablePanning()
  }
}

// 更新嵌入设置
const updateEmbed = (embedable, embedOptions) => {
  if (!graph || !graph.value) return

  if (embedable) {
    graph.value.options.embedding = {
      ...Options.defaults.embedding,
      enabled: true,
      validate: () => true,
      ...embedOptions
    }
  } else {
    graph.value.options.embedding = { enabled: false, validate: () => false }
  }
}

// 更新限制设置
const updateRestrict = (restrict, restrictOptions) => {
  if (!graph || !graph.value) return

  if (restrict) {
    graph.value.options.translating = {
      restrict: restrictOptions?.bound || restrict
    }
  } else {
    graph.value.options.translating = { restrict: false }
  }
}

// 视图操作
const handleViewOperations = () => {
  if (!graph || !graph.value) return

  nextTick(() => {
    if (props.centerView) {
      graph.value.centerContent(props.centerViewOptions)
    }

    if (props.fitView) {
      graph.value.scaleContentToFit(props.fitViewOptions)
    }
  })
}

// 右键菜单点击处理
const handleContextMenuClick = (item) => {
  // 调用标准交互中的菜单点击处理
  if (standardInteractions?.handleMenuClick) {
    standardInteractions.handleMenuClick(item)
  } else {
    // 降级处理：直接执行菜单项的动作
    console.log('Context menu item clicked:', item)
    if (item && typeof item.action === 'function') {
      item.action()
    }
  }
}

onMounted(async () => {
  console.log('XFlowGraph - onMounted 开始')
  console.log('XFlowGraph - containerRef:', containerRef.value)

  await initGraph()

  console.log('XFlowGraph - initGraph 完成')
  console.log('XFlowGraph - graph.value:', graph?.value)

  handleViewOperations()
  // 注册分组拖拽行为处理
  if (graph && graph.value) {
    const g = graph.value
    const padding = () => Number(props.groupPadding || 0)

    const resizeParentToFitChildren = (parent) => {
      try {
        const children = parent.getChildren ? parent.getChildren() || [] : []
        if (!children.length) return
        let minX = Infinity,
          minY = Infinity,
          maxX = -Infinity,
          maxY = -Infinity
        children.forEach((child) => {
          const b = child.getBBox()
          minX = Math.min(minX, b.x)
          minY = Math.min(minY, b.y)
          maxX = Math.max(maxX, b.x + b.width)
          maxY = Math.max(maxY, b.y + b.height)
        })
        const pad = padding()
        const width = Math.max(0, maxX - minX) + pad * 2
        const height = Math.max(0, maxY - minY) + pad * 2
        parent.position(minX - pad, minY - pad)
        parent.resize(width, height)
      } catch (e) {}
    }

    g.on('node:change:position', ({ node, previous, current }) => {
      // 仅处理子节点（非分组容器）
      if (!node || node.getData?.()?.type === 'group') return
      const parent = node.getParent && node.getParent()
      if (!parent) return

      if (props.groupChildDraggable === false) {
        // 回退到原位置，禁用分组内元素移动
        if (previous && typeof previous.x === 'number' && typeof previous.y === 'number') {
          node.position(previous.x, previous.y)
        }
        return
      }

      const parentBox = parent.getBBox()
      const childBox = node.getBBox()
      const pad = padding()

      if (props.groupAutoResize === true) {
        // 若子节点越界，则自适应扩展父容器
        const childRight = childBox.x + childBox.width
        const childBottom = childBox.y + childBox.height
        let needResize = false
        let minX = parentBox.x,
          minY = parentBox.y,
          maxX = parentBox.x + parentBox.width,
          maxY = parentBox.y + parentBox.height
        if (childBox.x < parentBox.x + pad) {
          minX = Math.min(minX, childBox.x - pad)
          needResize = true
        }
        if (childBox.y < parentBox.y + pad) {
          minY = Math.min(minY, childBox.y - pad)
          needResize = true
        }
        if (childRight > parentBox.x + parentBox.width - pad) {
          maxX = Math.max(maxX, childRight + pad)
          needResize = true
        }
        if (childBottom > parentBox.y + parentBox.height - pad) {
          maxY = Math.max(maxY, childBottom + pad)
          needResize = true
        }
        if (needResize) {
          parent.position(minX, minY)
          parent.resize(maxX - minX, maxY - minY)
        }
        return
      }

      // 不自适应：对子节点进行边界夹紧，禁止拖出
      const minAllowedX = parentBox.x + pad
      const minAllowedY = parentBox.y + pad
      const maxAllowedX = parentBox.x + parentBox.width - pad - childBox.width
      const maxAllowedY = parentBox.y + parentBox.height - pad - childBox.height
      const desiredX = current && typeof current.x === 'number' ? current.x : childBox.x
      const desiredY = current && typeof current.y === 'number' ? current.y : childBox.y
      const clampedX = Math.min(Math.max(desiredX, minAllowedX), maxAllowedX)
      const clampedY = Math.min(Math.max(desiredY, minAllowedY), maxAllowedY)
      if (clampedX !== desiredX || clampedY !== desiredY) {
        node.position(clampedX, clampedY)
      }
    })
  }
})

onUnmounted(() => {
  destroyGraph()
})

// 监听属性变化
watch(() => props.readonly, updateReadonly, { immediate: true })
watch(
  () => [props.locked, props.isNodeLocked],
  () => applyInteractions(),
  { immediate: true }
)
watch(
  () => [props.enableContextMenu, props.readonly],
  ([enabled, readonly]) => {
    if (!standardInteractions || typeof standardInteractions.setContextMenuEnabled !== 'function')
      return
    const shouldEnable =
      props.enableStandardInteractions !== false && enabled !== false && !readonly
    standardInteractions.setContextMenuEnabled(shouldEnable)
  },
  { immediate: true }
)
watch(
  () => props.enableDoubleClickFit,
  (enabled) => {
    if (
      !standardInteractions ||
      typeof standardInteractions.setDoubleClickFitEnabled !== 'function'
    )
      return
    const shouldEnable = props.enableStandardInteractions !== false && enabled !== false
    standardInteractions.setDoubleClickFitEnabled(shouldEnable)
  },
  { immediate: true }
)
watch(
  () => [props.enableStandardInteractions, props.readonly],
  ([enabled, readonly]) => {
    if (!standardInteractions) return
    const menuToggle =
      typeof standardInteractions.setContextMenuEnabled === 'function'
        ? standardInteractions.setContextMenuEnabled
        : null
    const dblClickToggle =
      typeof standardInteractions.setDoubleClickFitEnabled === 'function'
        ? standardInteractions.setDoubleClickFitEnabled
        : null

    const shouldEnableMenu = enabled !== false && props.enableContextMenu !== false && !readonly
    const shouldEnableDoubleClick = enabled !== false && props.enableDoubleClickFit !== false

    menuToggle?.(shouldEnableMenu)
    dblClickToggle?.(shouldEnableDoubleClick)
  },
  { immediate: true }
)
watch(
  () => [props.zoomable, props.zoomOptions],
  ([zoomable, zoomOptions]) => {
    updateZoom(zoomable, zoomOptions)
  },
  { immediate: true }
)
watch(
  () => [props.pannable, props.panOptions],
  ([pannable, panOptions]) => {
    updatePan(pannable, panOptions)
  },
  { immediate: true }
)
watch(
  () => [props.embedable, props.embedOptions],
  ([embedable, embedOptions]) => {
    updateEmbed(embedable, embedOptions)
  },
  { immediate: true }
)
watch(
  () => [props.restrict, props.restrictOptions],
  ([restrict, restrictOptions]) => {
    updateRestrict(restrict, restrictOptions)
  },
  { immediate: true }
)
watch(() => [props.centerView, props.fitView], handleViewOperations)

// 监听选择配置变化 - 由KeyboardManager管理，避免冲突
// watch(
//   () => props.selectOptions,
//   (opts) => {
//     if (!graph || !graph.value) return;
//     if (graph.value.getPlugin('selection')) {
//       graph.value.disposePlugins('selection');
//     }
//     graph.value.use(
//       new Selection({
//         enabled: true,
//         ...(opts || {}),
//       }),
//     );
//   },
//   { deep: true, immediate: false },
// );
</script>

<style scoped>
.xflow-graph {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #fafafa;
}

.xflow-graph-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.xflow-graph-wrapper {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.xflow-graph-wrapper > * {
  pointer-events: auto;
}
</style>
