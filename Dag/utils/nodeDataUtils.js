// 节点数据处理工具函数

/**
 * 生成节点ID（不包含 - 符号）
 */
export function generateNodeId() {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9).replace(/-/g, '')
}

/**
 * 生成内容ID（不包含 - 符号）
 */
export function generateContentId() {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9).replace(/-/g, '')
}

/**
 * 根据节点在图中的位置确定节点类型和层级
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 * @returns {Object} - 包含 type 和 level 的对象
 */
export function determineNodeTypeAndLevel(graph, nodeId) {
  if (!graph || !nodeId) {
    return { type: 'root-node', level: 1 }
  }

  const node = graph.getCellById(nodeId)
  if (!node) {
    return { type: 'root-node', level: 1 }
  }

  // 获取入边和出边
  const incomingEdges = graph.getIncomingEdges(node) || []
  const outgoingEdges = graph.getOutgoingEdges(node) || []

  // 根节点：没有入边
  if (incomingEdges.length === 0) {
    return { type: 'root-node', level: 1 }
  }

  // 叶子节点：有入边但没有出边
  if (incomingEdges.length > 0 && outgoingEdges.length === 0) {
    // 计算层级：通过遍历父节点计算
    const level = calculateNodeLevel(graph, nodeId)
    return { type: 'leaf-node', level }
  }

  // 子节点：既有入边又有出边
  if (incomingEdges.length > 0 && outgoingEdges.length > 0) {
    const level = calculateNodeLevel(graph, nodeId)
    return { type: 'sub-node', level }
  }

  // 默认情况
  return { type: 'sub-node', level: 2 }
}

/**
 * 计算节点层级
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 * @returns {number} - 节点层级
 */
function calculateNodeLevel(graph, nodeId) {
  if (!graph || !nodeId) return 1

  const node = graph.getCellById(nodeId)
  if (!node) return 1

  const incomingEdges = graph.getIncomingEdges(node) || []

  // 如果没有入边，是根节点，层级为1
  if (incomingEdges.length === 0) {
    return 1
  }

  // 计算所有父节点的最大层级，然后加1
  let maxParentLevel = 0
  for (const edge of incomingEdges) {
    const sourceId = edge.getSourceCellId()
    if (sourceId && sourceId !== nodeId) {
      // 避免循环引用
      const sourceNode = graph.getCellById(sourceId)
      if (sourceNode) {
        const sourceData = sourceNode.getData() || {}
        // 优先从properties.level获取，兼容顶层level字段
        const sourceLevel =
          sourceData.properties?.level || sourceData.level || calculateNodeLevel(graph, sourceId)
        maxParentLevel = Math.max(maxParentLevel, sourceLevel)
      }
    }
  }

  return maxParentLevel + 1
}

/**
 * 创建标准的节点数据结构
 * @param {Object} options - 节点配置选项
 * @returns {Object} - 标准的节点数据结构
 */
export function createNodeData(options = {}) {
  const {
    id = generateNodeId(),
    type = 'leaf-node',
    x = 0,
    y = 0,
    label = '新节点',
    level = 1,
    parentNodeId = null,
    weight = 50,
    otherData = {},
    customType = '',
    customProperties = '',
    unit = '',
    priority = '',
    defaultValue = '',
    notes = ''
  } = options

  return {
    id,
    type,
    x,
    y,
    properties: {
      content: {
        id: generateContentId(),
        label
      },
      weight,
      otherData,
      parentNodeId,
      customType,
      customProperties,
      unit,
      priority,
      defaultValue,
      notes,
      level
    }
  }
}

/**
 * 更新节点的类型和层级信息
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 */
export function updateNodeTypeAndLevel(graph, nodeId) {
  if (!graph || !nodeId) return

  const node = graph.getCellById(nodeId)
  if (!node) return

  const { type, level } = determineNodeTypeAndLevel(graph, nodeId)
  const currentData = node.getData() || {}
  const properties = currentData.properties || {}

  // 更新节点数据
  node.setData({
    ...currentData,
    type,
    level,
    // 同时更新properties中的level，确保数据同步
    properties: {
      ...properties,
      level
    },
    // 如果节点变成非叶子节点，清除计算模型数据
    ...(type !== 'leaf-node'
      ? {
          otherData: {},
          customType: '',
          customProperties: '',
          unit: '',
          priority: '',
          defaultValue: '',
          notes: ''
        }
      : {})
  })
}

/**
 * 批量更新所有节点的类型和层级
 * @param {Object} graph - X6 图实例
 */
export function updateAllNodesTypeAndLevel(graph) {
  if (!graph) return

  const nodes = graph.getNodes()
  nodes.forEach((node) => {
    updateNodeTypeAndLevel(graph, node.id)
  })
}

/**
 * 获取节点的父节点ID
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 * @returns {string|null} - 父节点ID
 */
export function getParentNodeId(graph, nodeId) {
  if (!graph || !nodeId) return null

  const node = graph.getCellById(nodeId)
  if (!node) return null

  const incomingEdges = graph.getIncomingEdges(node) || []
  if (incomingEdges.length === 0) return null

  // 返回第一个父节点的ID（通常一个节点只有一个直接父节点）
  const firstEdge = incomingEdges[0]
  return firstEdge.getSourceCellId() || null
}

/**
 * 检查节点是否有计算模型
 * @param {Object} nodeData - 节点数据
 * @returns {boolean} - 是否有计算模型
 */
export function hasComputeModel(nodeData) {
  if (!nodeData) return false
  // 兼容两种存储位置：顶层与 properties.otherData
  const otherData = nodeData.otherData ?? nodeData.properties?.otherData
  return !!(otherData && Object.keys(otherData).length > 0)
}

/**
 * 清除节点的计算模型数据
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 */
export function clearNodeComputeModel(graph, nodeId) {
  if (!graph || !nodeId) return

  const node = graph.getCellById(nodeId)
  if (!node) return

  const currentData = node.getData() || {}
  const properties = currentData.properties || {}
  node.setData({
    ...currentData,
    otherData: {},
    customType: '',
    customProperties: '',
    unit: '',
    priority: '',
    defaultValue: '',
    notes: '',
    // 同步清空 properties 内的同名字段（若存在），但保留level
    properties: {
      ...properties,
      otherData: {},
      customType: '',
      customProperties: '',
      unit: '',
      priority: '',
      defaultValue: '',
      notes: properties.notes ?? ''
      // level保持不变
    }
  })
}

/**
 * 设置节点的计算模型数据
 * @param {Object} graph - X6 图实例
 * @param {string} nodeId - 节点ID
 * @param {Object} modelData - 计算模型数据
 * @param {Object} formData - 表单数据
 */
export function setNodeComputeModel(graph, nodeId, modelData, formData = {}) {
  if (!graph || !nodeId) return

  const node = graph.getCellById(nodeId)
  if (!node) return

  const currentData = node.getData() || {}
  const properties = currentData.properties || {}
  node.setData({
    ...currentData,
    otherData: modelData,
    customType: formData.customType || '',
    customProperties: formData.customProperties || '',
    unit: formData.unit || '',
    priority: formData.priority || '',
    defaultValue: formData.defaultValue || '',
    notes: formData.notes || '',
    // 同步写入 properties 内的同名字段，保持兼容，但保留level
    properties: {
      ...properties,
      otherData: modelData,
      customType: formData.customType || '',
      customProperties: formData.customProperties || '',
      unit: formData.unit || '',
      priority: formData.priority || '',
      defaultValue: formData.defaultValue || '',
      notes: formData.notes || ''
      // level保持不变
    }
  })
}
