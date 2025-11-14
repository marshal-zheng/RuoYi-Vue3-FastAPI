/**
 * 标准交互管理器
 * 集成企业级标准的图编辑器交互功能
 */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useContextMenu } from './useContextMenu.js'
import { useDeviceSupport } from './useDeviceSupport.js'

export function useStandardInteractions(graph, options = {}) {
  const { isMacOs, isCtrlKeyPressed } = useDeviceSupport()

  // 默认配置
  const defaultOptions = {
    enableContextMenu: true,
    enableDoubleClickFit: true,
    enableStandardSelection: true,
    enableKeyboardShortcuts: true,
    contextMenuOptions: {},
    // 是否允许边被选择/框选
    allowEdgeSelection: false
  }

  const config = { ...defaultOptions, ...options }

  // 初始化右键菜单
  const contextMenuComposable = config.enableContextMenu
    ? useContextMenu(graph, config.contextMenuOptions)
    : null

  const blankDblclickHandler = () => {
    const g = getGraphInstance()
    g?.scaleContentToFit({ padding: 20 })
  }

  const updateDoubleClickFitListener = (graphInstance = null) => {
    const g = graphInstance || getGraphInstance()
    if (!g || typeof g.on !== 'function') return
    g.off('blank:dblclick', blankDblclickHandler)
    if (config.enableDoubleClickFit) {
      g.on('blank:dblclick', blankDblclickHandler)
    }
  }

  // 选择状态
  const selectedCells = ref([])
  // 框选模式状态（Shift+拖拽时为 true）
  const isRubberbandMode = ref(false)
  // Shift 键按压状态，用于在框选模式下禁用画布拖拽
  const isShiftPressed = ref(false)
  // 避免橡皮筋结束后被 blank:click 立即清除选择
  const skipNextBlankClick = ref(false)
  let wasPannableBeforeShift = null

  const getGraphInstance = () => graph?.value || graph

  const handleShiftKeyDown = (event) => {
    if (event.key !== 'Shift' || event.repeat || event.metaKey || event.ctrlKey || event.altKey) {
      return
    }
    isShiftPressed.value = true
    const g = getGraphInstance()
    if (!g || typeof g.disablePanning !== 'function') return
    wasPannableBeforeShift = g.isPannable?.() ?? null
    if (wasPannableBeforeShift) {
      g.disablePanning()
    }
  }

  const handleShiftKeyUp = (event) => {
    if (event.key !== 'Shift') return
    isShiftPressed.value = false
    const g = getGraphInstance()
    if (g && wasPannableBeforeShift) {
      g.enablePanning?.()
    }
    wasPannableBeforeShift = null
  }

  onMounted(() => {
    window.addEventListener('keydown', handleShiftKeyDown, true)
    window.addEventListener('keyup', handleShiftKeyUp, true)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleShiftKeyDown, true)
    window.removeEventListener('keyup', handleShiftKeyUp, true)
    if (isShiftPressed.value) {
      const g = getGraphInstance()
      if (g && wasPannableBeforeShift) {
        g.enablePanning?.()
      }
    }
    isShiftPressed.value = false
    wasPannableBeforeShift = null
  })

  // 设置标准交互事件
  const setupStandardEvents = (graphInstance = null) => {
    const g = graphInstance || getGraphInstance()
    if (!g || typeof g.on !== 'function') {
      console.warn('Graph instance is not ready for event setup')
      return
    }

    if (isShiftPressed.value && typeof g.disablePanning === 'function') {
      if (wasPannableBeforeShift == null) {
        wasPannableBeforeShift = g.isPannable?.() ?? null
      }
      if (wasPannableBeforeShift) {
        g.disablePanning()
      }
    }

    // 选择变化监听
    g.on('selection:changed', ({ selected }) => {
      // 按照新逻辑：
      // 1. 框选模式（Shift+拖拽）：允许选择所有元素
      // 2. 正常模式：只允许选择节点，但 Cmd/Ctrl + 点击边例外
      // 3. 不过滤已经通过 Cmd/Ctrl + 点击选中的边
      selectedCells.value = selected
    })

    // 双击空白区域适应画布
    updateDoubleClickFitListener(g)

    // 标准选择交互
    if (config.enableStandardSelection) {
      setupSelectionInteractions(g)
    }

    // 右键菜单事件已在 useContextMenu 中处理
    if (contextMenuComposable) {
      contextMenuComposable.setupGraphEvents(g)
    }
  }

  // 设置选择交互
  const setupSelectionInteractions = (graphInstance = null) => {
    const g = graphInstance || graph?.value || graph
    if (!g || typeof g.on !== 'function') return

    // 监听框选开始和结束
    g.on('selection:rubberband:start', ({ e }) => {
      // 只有按住 Shift 键才进入框选模式
      if (e.shiftKey) {
        isRubberbandMode.value = true
      }
    })

    g.on('selection:rubberband:end', () => {
      isRubberbandMode.value = false
      skipNextBlankClick.value = true
    })

    // 点击空白区域：在未按住修饰键时清除选择
    g.on('blank:click', ({ e }) => {
      if (skipNextBlankClick.value) {
        skipNextBlankClick.value = false
        return
      }
      if (e.shiftKey || isRubberbandMode.value) {
        return
      }
      if (!isCtrlKeyPressed(e)) {
        g.cleanSelection()
      }
    })

    // 节点点击选择逻辑
    g.on('node:click', ({ e, node }) => {
      console.log('useStandardInteractions - node:click 被触发:', node?.id)
      // X6 在 detail >= 2 时代表同一节点连续点击；保持节点已有选中状态并提前返回，
      // 避免再次执行 cleanSelection/select 导致节点重新渲染，从而丢失 dblclick 判定。
      if (e?.detail >= 2) {
        console.log('useStandardInteractions - 检测到双击，跳过重选逻辑')
        return
      }
      if (isCtrlKeyPressed(e)) {
        // 交给 Selection 插件处理多选/反选逻辑
        console.log('useStandardInteractions - Ctrl键被按下，交给Selection插件')
        return
      }
      // 普通点击：单选
      console.log('useStandardInteractions - 普通点击，执行单选')
      g.cleanSelection()
      g.select(node)
    })

    // 边点击选择逻辑 - 按照新需求：正常模式下边不可被点击选中，但 Cmd/Ctrl + 点击可以选中
    g.on('edge:click', ({ e, edge }) => {
      if (isCtrlKeyPressed(e)) {
        // Cmd/Ctrl + 点击边：允许选中并显示选择框
        if (g.isSelected(edge)) {
          g.unselect(edge)
        } else {
          // 增量加入当前选择集合，避免覆盖已有选中
          if (typeof g.addToSelection === 'function') {
            g.addToSelection(edge)
          } else {
            // 兜底：获取已选 + 当次边，重新设置选择
            const current = (g.getSelectedCells && g.getSelectedCells()) || []
            g.select([...current, edge], { silent: false })
          }
        }
        return
      }

      // 正常点击：只有在明确允许边选择时才能选中
      if (!config.allowEdgeSelection) {
        return // 边有hover态但不被选中
      }

      // 普通点击：单选
      g.cleanSelection()
      g.select(edge)
    })
  }

  // 选择操作方法
  const selectAll = () => {
    const g = graph?.value || graph
    if (g) {
      // X6 无内置 selectAll 方法，需要手动选择所有元素
      const cells = config.allowEdgeSelection
        ? g.getCells
          ? g.getCells()
          : []
        : g.getNodes
          ? g.getNodes()
          : []
      if (cells && cells.length > 0) {
        g.select(cells)
      }
    }
  }

  const clearSelection = () => {
    const g = graph?.value || graph
    if (g) {
      g.cleanSelection()
    }
  }

  const deleteSelected = () => {
    const g = graph?.value || graph
    if (g && selectedCells.value.length > 0) {
      g.removeCells(selectedCells.value)
    }
  }

  // 视图操作方法
  const zoomToFit = () => {
    const g = graph?.value || graph
    if (g) {
      g.scaleContentToFit({ padding: 20 })
    }
  }

  const zoomToActual = () => {
    const g = graph?.value || graph
    if (g) {
      g.scale(1)
      g.centerContent()
    }
  }

  const centerContent = () => {
    const g = graph?.value || graph
    if (g) {
      g.centerContent()
    }
  }

  // 设置处理器给右键菜单
  const setupHandlers = (clipboardActions, historyActions) => {
    if (contextMenuComposable) {
      // 设置剪贴板处理器
      contextMenuComposable.setClipboardHandler(clipboardActions)

      // 设置历史处理器
      contextMenuComposable.setHistoryHandler(historyActions)

      // 设置选择处理器
      contextMenuComposable.setSelectionHandler({
        selectAll,
        clearSelection,
        deleteSelected
      })
    }
  }

  // 获取当前选择的处理器
  const getSelectionHandler = () => ({
    selectedCells: selectedCells.value,
    selectAll,
    clearSelection,
    deleteSelected
  })

  // 获取视图操作处理器
  const getViewHandler = () => ({
    zoomToFit,
    zoomToActual,
    centerContent
  })

  // 初始化将由外部调用

  return {
    // 状态
    selectedCells,

    // 右键菜单
    contextMenu: contextMenuComposable?.contextMenu,
    handleMenuClick: contextMenuComposable?.handleMenuClick,

    // 操作方法
    selectAll,
    clearSelection,
    deleteSelected,
    zoomToFit,
    zoomToActual,
    centerContent,

    // 处理器设置
    setupHandlers,
    getSelectionHandler,
    getViewHandler,

    // 事件设置
    setupStandardEvents,
    setContextMenuEnabled: contextMenuComposable?.setEnabled,
    setDoubleClickFitEnabled: (enabled) => {
      config.enableDoubleClickFit = !!enabled
      updateDoubleClickFitListener()
    }
  }
}
