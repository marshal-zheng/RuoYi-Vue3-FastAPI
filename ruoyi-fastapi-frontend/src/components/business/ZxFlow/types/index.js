// 导出类型定义（JS 版本不需要类型，但保持结构一致性）

// 节点选项
export const createNodeOptions = (options = {}) => ({
  selected: false,
  draggable: true,
  ...options
})

// 边选项
export const createEdgeOptions = (options = {}) => ({
  selected: false,
  draggable: true,
  labelDraggable: false,
  animated: false,
  ...options
})

// 图模型
export const createGraphModel = (nodes = [], edges = []) => ({
  nodes,
  edges
})

// 高亮选项
export const createHighlightOptions = (options = {}) => ({
  name: 'stroke',
  args: {
    attrs: {
      body: {
        stroke: '#1890ff',
        strokeWidth: 2
      }
    }
  },
  ...options
})

// 连接选项
export const createConnectionOptions = (options = {}) => ({
  snap: true,
  allowBlank: false,
  allowLoop: false,
  allowNode: false,
  allowEdge: false,
  allowPort: true,
  highlight: true,
  ...options
})

// 选择选项
export const createSelectionOptions = (options = {}) => ({
  enabled: true,
  multiple: true,
  rubberband: true,
  movable: true,
  showNodeSelectionBox: true,
  ...options
})

// 键盘选项
export const createKeyboardOptions = (options = {}) => ({
  enabled: true,
  global: false,
  ...options
})

// 滚动选项
export const createScrollerOptions = (options = {}) => ({
  enabled: true,
  pannable: true,
  pageVisible: false,
  pageBreak: false,
  ...options
})
