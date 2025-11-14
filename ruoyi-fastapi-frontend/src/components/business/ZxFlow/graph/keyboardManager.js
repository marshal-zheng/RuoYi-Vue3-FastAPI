/**
 * 键盘管理器 - 基于 X6 Keyboard 插件的企业级键盘事件管理
 * 参考 Figma/Sketch/Adobe XD 的交互设计
 */

import { Keyboard } from '@antv/x6-plugin-keyboard'
import { Selection } from '@antv/x6-plugin-selection'
import { useDeviceSupport } from '../composables/useDeviceSupport.js'

// 生成基于设备的快捷键配置
export function createKeyboardConfig() {
  const { isMacOs } = useDeviceSupport()
  const ctrlKey = isMacOs ? 'meta' : 'ctrl'

  return {
    // 选择操作
    [`${ctrlKey}+a`]: 'select-all',

    // 历史操作
    [`${ctrlKey}+z`]: 'undo',
    [`${ctrlKey}+shift+z`]: 'redo',
    ...(isMacOs ? {} : { 'ctrl+y': 'redo' }), // Windows额外支持Ctrl+Y

    // 剪贴板操作
    [`${ctrlKey}+c`]: 'copy',
    [`${ctrlKey}+v`]: 'paste',
    [`${ctrlKey}+x`]: 'cut',

    // 删除操作
    delete: 'delete-selected',
    backspace: 'delete-selected',

    // 取消当前操作 / 清除选择
    esc: 'clear-selection',

    // 视图操作
    [`${ctrlKey}+0`]: 'zoom-to-fit',
    [`${ctrlKey}+1`]: 'zoom-to-actual',

    // 临时拖拽（空格键）
    space: 'temp-pan-start'
  }
}

// 默认配置（向后兼容）
export const DEFAULT_KEYBOARD_CONFIG = createKeyboardConfig()

// 交互模式定义
export const INTERACTION_MODES = {
  PAN: 'pan', // 画布拖拽模式
  SELECT: 'select', // 框选模式
  CONNECT: 'connect', // 连接模式
  EDIT: 'edit' // 编辑模式
}

/**
 * 键盘管理器类
 */
export class KeyboardManager {
  constructor(graph, options = {}) {
    this.graph = graph
    this.deviceSupport = useDeviceSupport()
    this.options = {
      keyboardConfig: createKeyboardConfig(),
      globalKeys: ['space'], // 需要全局监听的键
      enableStandardInteractions: true, // 启用标准交互
      enableContextMenu: true, // 启用右键菜单
      // 是否允许边被选择/框选（与图层配置保持一致）
      allowEdgeSelection: false,
      ...options
    }

    this.keyboardPlugin = null
    this.currentMode = INTERACTION_MODES.PAN
    this.spacePressed = false
    this.originalPannable = true

    this.actionHandlers = new Map()
    this.globalKeyListeners = new Map()
    this.selectionOptions = {
      enabled: true,
      multiple: true,
      rubberband: true,
      modifiers: ['shift'],
      multipleSelectionModifiers: ['ctrl', 'meta'],
      showNodeSelectionBox: true,
      showEdgeSelectionBox: this.options.allowEdgeSelection === true,
      selectEdgeOnMoveEdge: false,
      strict: false
    }

    this.init()
  }

  /**
   * 初始化键盘管理器
   */
  init() {
    this.setupKeyboardPlugin()
    this.setupGlobalKeys()
    this.registerDefaultActions()
    // 初始化Selection插件，使用默认的PAN模式配置
    this.setInteractionMode(this.currentMode)
  }

  /**
   * 设置 X6 键盘插件
   */
  setupKeyboardPlugin() {
    // 移除现有插件
    if (this.graph.getPlugin('keyboard')) {
      this.graph.disposePlugins('keyboard')
    }

    // 添加键盘插件
    this.keyboardPlugin = new Keyboard({
      enabled: true,
      global: false // 不使用全局模式，避免冲突
    })

    this.graph.use(this.keyboardPlugin)

    // 绑定快捷键
    Object.entries(this.options.keyboardConfig).forEach(([key, action]) => {
      if (!this.options.globalKeys.includes(key.split('+').pop())) {
        this.graph.bindKey(key, (e) => this.handleAction(action, e))
      }
    })
  }

  /**
   * 设置全局键盘监听（仅限必要的键）
   */
  setupGlobalKeys() {
    this.options.globalKeys.forEach((key) => {
      const keydownHandler = (e) => {
        if (e.code === 'Space' && e.target === document.body) {
          this.handleSpaceDown(e)
        }
      }

      const keyupHandler = (e) => {
        if (e.code === 'Space') {
          this.handleSpaceUp(e)
        }
      }

      document.addEventListener('keydown', keydownHandler)
      document.addEventListener('keyup', keyupHandler)

      // 保存引用用于清理
      this.globalKeyListeners.set(key, { keydownHandler, keyupHandler })
    })
  }

  /**
   * 注册默认动作处理器
   */
  registerDefaultActions() {
    // 选择操作
    this.registerAction('select-all', () => this.selectAll())
    this.registerAction('clear-selection', () => this.clearSelection())

    // 删除操作
    this.registerAction('delete-selected', () => this.deleteSelected())

    // 视图操作
    this.registerAction('zoom-to-fit', () => this.zoomToFit())
    this.registerAction('zoom-to-actual', () => this.zoomToActual())

    // 剪贴板操作需要外部注入
    this.registerAction('copy', () => this.handleClipboard('copy'))
    this.registerAction('paste', () => this.handleClipboard('paste'))
    this.registerAction('cut', () => this.handleClipboard('cut'))

    // 历史操作需要外部注入
    this.registerAction('undo', () => this.handleHistory('undo'))
    this.registerAction('redo', () => this.handleHistory('redo'))
  }

  /**
   * 选择所有元素
   */
  selectAll() {
    if (this.graph) {
      // X6 无内置 selectAll 方法；这里按配置选择节点（可选边）
      const cells = this.options.allowEdgeSelection
        ? this.graph.getCells
          ? this.graph.getCells()
          : []
        : this.graph.getNodes
          ? this.graph.getNodes()
          : []
      if (cells && cells.length > 0) {
        this.graph.select(cells)
      }
    }
  }

  /**
   * 清除选择
   */
  clearSelection() {
    if (this.graph) {
      this.graph.cleanSelection()
    }
  }

  /**
   * 适应画布
   */
  zoomToFit() {
    if (this.graph) {
      this.graph.scaleContentToFit({ padding: 20 })
    }
  }

  /**
   * 实际大小
   */
  zoomToActual() {
    if (this.graph) {
      this.graph.scale(1)
      this.graph.centerContent()
    }
  }

  /**
   * 注册动作处理器
   */
  registerAction(action, handler) {
    this.actionHandlers.set(action, handler)
  }

  /**
   * 执行动作
   */
  handleAction(action, event) {
    const handler = this.actionHandlers.get(action)
    if (handler) {
      event?.preventDefault()
      handler(event)
    }
  }

  /**
   * 设置交互模式
   */
  setInteractionMode(mode) {
    this.currentMode = mode

    switch (mode) {
      case INTERACTION_MODES.PAN:
        this.graph.enablePanning()
        this.updateSelectionPlugin({
          rubberband: true,
          modifiers: ['shift'],
          multiple: true
        })
        break

      case INTERACTION_MODES.SELECT:
        this.graph.disablePanning()
        this.updateSelectionPlugin({
          rubberband: true,
          modifiers: null,
          multiple: true
        })
        break

      // 可扩展其他模式
    }
  }

  /**
   * 更新选择插件配置
   */
  updateSelectionPlugin(options) {
    // 移除现有插件
    if (this.graph.getPlugin('selection')) {
      this.graph.disposePlugins('selection')
    }

    this.selectionOptions = {
      ...this.selectionOptions,
      showEdgeSelectionBox: this.options.allowEdgeSelection === true,
      ...options
    }

    // 重新添加插件，使用新配置
    this.graph.use(
      new Selection({
        ...this.selectionOptions
      })
    )
  }

  /**
   * 处理空格键按下
   */
  handleSpaceDown(e) {
    if (this.spacePressed) return

    this.spacePressed = true
    this.originalPannable = this.graph.options.panning?.enabled !== false

    // 临时启用拖拽
    this.graph.enablePanning()
    e.preventDefault()
  }

  /**
   * 处理空格键释放
   */
  handleSpaceUp(e) {
    if (!this.spacePressed) return

    this.spacePressed = false

    // 恢复原来的拖拽状态
    if (this.currentMode === INTERACTION_MODES.SELECT) {
      this.graph.disablePanning()
    }

    e.preventDefault()
  }

  /**
   * 删除选中元素
   */
  deleteSelected() {
    const selectedCells = this.graph.getSelectedCells()
    if (selectedCells.length > 0) {
      this.graph.removeCells(selectedCells)
    }
  }

  /**
   * 处理剪贴板操作（需要外部注入处理器）
   */
  handleClipboard(action) {
    if (this.clipboardHandler) {
      this.clipboardHandler(action)
    }
  }

  /**
   * 处理历史操作（需要外部注入处理器）
   */
  handleHistory(action) {
    if (this.historyHandler) {
      this.historyHandler(action)
    }
  }

  /**
   * 注入剪贴板处理器
   */
  setClipboardHandler(handler) {
    this.clipboardHandler = handler
  }

  /**
   * 注入历史处理器
   */
  setHistoryHandler(handler) {
    this.historyHandler = handler
  }

  /**
   * 销毁管理器
   */
  destroy() {
    // 清理全局事件监听
    this.globalKeyListeners.forEach(({ keydownHandler, keyupHandler }, key) => {
      document.removeEventListener('keydown', keydownHandler)
      document.removeEventListener('keyup', keyupHandler)
    })

    this.globalKeyListeners.clear()
    this.actionHandlers.clear()

    // X6 插件会在 graph.dispose() 时自动清理
  }
}

/**
 * 创建键盘管理器的工厂函数
 */
export function createKeyboardManager(graph, options = {}) {
  return new KeyboardManager(graph, options)
}
