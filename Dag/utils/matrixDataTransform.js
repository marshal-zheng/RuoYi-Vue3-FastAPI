/**
 * 图数据与矩阵表格数据的转换工具
 * 支持树形结构的双向转换
 */

/**
 * 将图数据转换为树形表格数据
 * @param {Object} graphData - 图数据 {nodes: [], edges: []}
 * @param {Function} nodeRenderer - 节点数据渲染函数
 * @returns {Array} 树形表格数据
 */
export function transformGraphToMatrix(graphData, nodeRenderer = null) {
  if (!graphData || !graphData.nodes || !Array.isArray(graphData.nodes)) {
    return []
  }

  const { nodes, edges } = graphData

  // 构建父子关系映射
  const childrenMap = new Map()
  const parentMap = new Map()

  // 初始化所有节点的子节点集合
  nodes.forEach((node) => {
    childrenMap.set(node.id, [])
  })

  // 构建父子关系
  ;(edges || []).forEach((edge) => {
    const { sourceNodeId, targetNodeId } = edge
    if (sourceNodeId && targetNodeId) {
      if (!childrenMap.has(sourceNodeId)) {
        childrenMap.set(sourceNodeId, [])
      }
      childrenMap.get(sourceNodeId).push(targetNodeId)
      parentMap.set(targetNodeId, sourceNodeId)
    }
  })

  // 找到根节点（没有父节点的节点）
  const rootNodes = nodes.filter((node) => !parentMap.has(node.id))

  // 递归构建树形结构
  const buildTreeNode = (node, level = 1, parentId = null) => {
    const children = childrenMap.get(node.id) || []
    const childNodes = children
      .map((childId) => {
        const childNode = nodes.find((n) => n.id === childId)
        return childNode ? buildTreeNode(childNode, level + 1, node.id) : null
      })
      .filter(Boolean)

    // 基础树形节点结构
    const treeNode = {
      id: node.id,
      level,
      parentId,
      hasChildren: childNodes.length > 0,
      children: childNodes,
      // 原始节点数据
      originalNode: node,
      // 基础属性
      type: node.type || 'leaf-node',
      properties: node.properties || {},
      // 位置信息（用于同步回图）
      position: {
        x: node.x || 0,
        y: node.y || 0
      }
    }

    // 如果提供了自定义渲染器，使用它来扩展节点数据
    if (typeof nodeRenderer === 'function') {
      const renderedData = nodeRenderer(node, treeNode)
      Object.assign(treeNode, renderedData)
    }

    return treeNode
  }

  // 构建完整的树形结构
  const matrixData = rootNodes.map((rootNode) => buildTreeNode(rootNode))

  return matrixData
}

/**
 * 将树形表格数据转换为图数据
 * @param {Array} matrixData - 树形表格数据
 * @param {Function} nodeTransformer - 节点数据转换函数
 * @returns {Object} 图数据 {nodes: [], edges: []}
 */
export function transformMatrixToGraph(matrixData, nodeTransformer = null) {
  if (!Array.isArray(matrixData)) {
    return { nodes: [], edges: [] }
  }

  const nodes = []
  const edges = []

  // 递归遍历树形数据
  const traverseTreeNode = (treeNode, parentId = null) => {
    // 构建节点数据
    let nodeData = {
      id: treeNode.id,
      type: treeNode.type || 'leaf-node',
      x: treeNode.position?.x || 0,
      y: treeNode.position?.y || 0,
      properties: treeNode.properties || {}
    }

    // 如果提供了自定义转换器，使用它来转换节点数据
    if (typeof nodeTransformer === 'function') {
      const transformedData = nodeTransformer(treeNode, nodeData)
      nodeData = { ...nodeData, ...transformedData }
    }

    nodes.push(nodeData)

    // 如果有父节点，创建边
    if (parentId) {
      edges.push({
        id: `edge_${parentId}_${treeNode.id}`,
        type: 'mindmap-edge',
        sourceNodeId: parentId,
        targetNodeId: treeNode.id,
        startPoint: { x: 0, y: 0 }, // 这些会在布局时重新计算
        endPoint: { x: 0, y: 0 },
        properties: {},
        pointsList: []
      })
    }

    // 递归处理子节点
    if (treeNode.children && Array.isArray(treeNode.children)) {
      treeNode.children.forEach((child) => {
        traverseTreeNode(child, treeNode.id)
      })
    }
  }

  // 遍历所有根节点
  matrixData.forEach((rootNode) => {
    traverseTreeNode(rootNode)
  })

  return { nodes, edges }
}

/**
 * 将树形数据扁平化为表格行数据（保持层级信息）
 * @param {Array} treeData - 树形数据
 * @param {Boolean} expandAll - 是否展开所有节点
 * @returns {Array} 扁平化的表格行数据
 */
export function flattenTreeForTable(treeData, expandAll = true) {
  const result = []

  const traverse = (nodes, parentExpanded = true) => {
    if (!Array.isArray(nodes)) return

    nodes.forEach((node) => {
      // 添加当前节点到结果中（只有在父节点展开时才显示）
      if (parentExpanded) {
        result.push({
          ...node,
          // 添加表格展示需要的属性
          _expanded: expandAll || node._expanded || false,
          _visible: true,
          _rowKey: node.id
        })
      }

      // 递归处理子节点
      if (node.children && node.children.length > 0) {
        const shouldExpandChildren = parentExpanded && (expandAll || node._expanded)
        traverse(node.children, shouldExpandChildren)
      }
    })
  }

  traverse(treeData)
  return result
}

/**
 * 更新树形数据中的节点
 * @param {Array} treeData - 树形数据
 * @param {String} nodeId - 节点ID
 * @param {Object} updates - 更新数据
 * @returns {Array} 更新后的树形数据
 */
export function updateTreeNode(treeData, nodeId, updates) {
  const updateNode = (nodes) => {
    return nodes.map((node) => {
      if (node.id === nodeId) {
        return { ...node, ...updates }
      }
      if (node.children && node.children.length > 0) {
        return {
          ...node,
          children: updateNode(node.children)
        }
      }
      return node
    })
  }

  return updateNode(treeData)
}

/**
 * 在树形数据中添加新节点
 * @param {Array} treeData - 树形数据
 * @param {String} parentId - 父节点ID，null表示添加根节点
 * @param {Object} newNode - 新节点数据
 * @returns {Array} 更新后的树形数据
 */
export function addTreeNode(treeData, parentId, newNode) {
  if (!parentId) {
    // 添加根节点
    return [...treeData, newNode]
  }

  const addToParent = (nodes) => {
    return nodes.map((node) => {
      if (node.id === parentId) {
        const children = node.children || []
        return {
          ...node,
          children: [...children, newNode],
          hasChildren: true
        }
      }
      if (node.children && node.children.length > 0) {
        return {
          ...node,
          children: addToParent(node.children)
        }
      }
      return node
    })
  }

  return addToParent(treeData)
}

/**
 * 从树形数据中删除节点
 * @param {Array} treeData - 树形数据
 * @param {String} nodeId - 要删除的节点ID
 * @returns {Array} 更新后的树形数据
 */
export function removeTreeNode(treeData, nodeId) {
  const removeNode = (nodes) => {
    const filtered = nodes.filter((node) => node.id !== nodeId)
    return filtered.map((node) => {
      if (node.children && node.children.length > 0) {
        const updatedChildren = removeNode(node.children)
        return {
          ...node,
          children: updatedChildren,
          hasChildren: updatedChildren.length > 0
        }
      }
      return node
    })
  }

  return removeNode(treeData)
}

/**
 * 计算节点在树中的路径
 * @param {Array} treeData - 树形数据
 * @param {String} nodeId - 节点ID
 * @returns {Array} 从根到该节点的路径ID数组
 */
export function getNodePath(treeData, nodeId) {
  const findPath = (nodes, targetId, path = []) => {
    for (const node of nodes) {
      const currentPath = [...path, node.id]

      if (node.id === targetId) {
        return currentPath
      }

      if (node.children && node.children.length > 0) {
        const childPath = findPath(node.children, targetId, currentPath)
        if (childPath) {
          return childPath
        }
      }
    }
    return null
  }

  return findPath(treeData, nodeId) || []
}
