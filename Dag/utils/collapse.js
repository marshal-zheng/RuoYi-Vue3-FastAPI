/**
 * Collapse/expand utilities for DAG nodes.
 * Nodes keep a `collapsed` flag in their data; descendants inherit visibility.
 */

const isGraphLike = (graph) => {
  if (!graph) return false
  const g = graph?.value ?? graph
  return g && typeof g.getNodes === 'function'
}

const getGraph = (graph) => {
  if (!isGraphLike(graph)) {
    return null
  }
  return graph?.value ?? graph
}

export const isNodeCollapsed = (node) => {
  if (!node) return false
  const data = node.getData?.() || {}
  return data.collapsed === true
}

const setNodeCollapsedData = (node, collapsed) => {
  if (!node) return
  const data = node.getData?.() || {}
  if (data.collapsed === collapsed) return
  node.setData({
    ...data,
    collapsed
  })
}

const hasCollapsedAncestor = (graph, node, visited = new Set()) => {
  if (!graph || !node) return false
  const nodeId = node.id
  if (!nodeId || visited.has(nodeId)) return false
  visited.add(nodeId)

  const incoming = graph.getIncomingEdges?.(node) || []
  for (const edge of incoming) {
    const parentId = edge.getSourceCellId?.()
    if (!parentId) continue
    const parentNode = graph.getCellById(parentId)
    if (!parentNode) continue
    if (isNodeCollapsed(parentNode)) return true
    if (hasCollapsedAncestor(graph, parentNode, visited)) return true
  }

  return false
}

export const applyCollapseState = (graph) => {
  const g = getGraph(graph)
  if (!g) return

  const nodes = g.getNodes?.() || []
  const edges = g.getEdges?.() || []

  const childMap = new Map()
  edges.forEach((edge) => {
    const sourceId = edge?.getSourceCellId?.()
    const targetId = edge?.getTargetCellId?.()
    if (!sourceId || !targetId) return
    if (!childMap.has(sourceId)) {
      childMap.set(sourceId, new Set())
    }
    childMap.get(sourceId).add(targetId)
  })

  nodes.forEach((node) => {
    if (!node) return
    const prevData = node.getData?.() || {}
    const hasChildren = (childMap.get(node.id)?.size || 0) > 0
    if (prevData.hasChildren !== hasChildren) {
      node.setData({
        ...prevData,
        hasChildren
      })
    }
  })

  nodes.forEach((node) => {
    if (!node) return
    const shouldHide = hasCollapsedAncestor(g, node)
    if (shouldHide) {
      node.hide?.()
    } else {
      node.show?.()
    }
  })

  edges.forEach((edge) => {
    if (!edge) return
    const sourceId = edge.getSourceCellId?.()
    const targetId = edge.getTargetCellId?.()
    if (!sourceId || !targetId) {
      edge.hide?.()
      return
    }
    const sourceNode = g.getCellById(sourceId)
    const targetNode = g.getCellById(targetId)
    const sourceVisible = sourceNode?.isVisible?.() !== false
    const targetVisible = targetNode?.isVisible?.() !== false
    const sourceCollapsed = isNodeCollapsed(sourceNode)
    if (sourceVisible && targetVisible && !sourceCollapsed) {
      edge.show?.()
    } else {
      edge.hide?.()
    }
  })
}

export const toggleNodeCollapse = (graph, nodeId) => {
  const g = getGraph(graph)
  if (!g || !nodeId) return
  const node = g.getCellById(nodeId)
  if (!node) return
  const collapsed = isNodeCollapsed(node)
  setNodeCollapsedData(node, !collapsed)
  applyCollapseState(g)
}

export const setNodeCollapseState = (graph, nodeId, collapsed) => {
  const g = getGraph(graph)
  if (!g || !nodeId) return
  const node = g.getCellById(nodeId)
  if (!node) return
  setNodeCollapsedData(node, collapsed)
  applyCollapseState(g)
}

export const refreshCollapseState = (graph) => {
  applyCollapseState(graph)
}
