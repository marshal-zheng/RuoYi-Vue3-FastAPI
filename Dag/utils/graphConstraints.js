// DAG 约束相关工具（仅在 dag-vue 范围内使用）

// 判断从 startId 出发是否可以到达 targetId（基于现有图结构）
export function canReach(graph, startId, targetId) {
  if (!graph || !startId || !targetId) return false
  if (startId === targetId) return true
  const visited = new Set()
  const queue = [startId]
  while (queue.length) {
    const cur = queue.shift()
    if (visited.has(cur)) continue
    visited.add(cur)
    if (cur === targetId) return true
    try {
      // 使用 X6 API 获取后继节点
      const successors = graph.getSuccessors(cur) || []
      successors.forEach((node) => {
        if (node && node.id && !visited.has(node.id)) queue.push(node.id)
      })
    } catch (e) {
      // 兜底：通过出边遍历
      const node = graph.getCellById?.(cur)
      const outgoing = node ? graph.getOutgoingEdges(node) || [] : []
      outgoing.forEach((edge) => {
        const id = edge.getTargetCellId?.()
        if (id && !visited.has(id)) queue.push(id)
      })
    }
  }
  return false
}

// 判断新增一条 sourceId -> targetId 是否会造成环
export function willCreateCycle(graph, sourceId, targetId) {
  if (!graph || !sourceId || !targetId) return false
  // 若 target 能到达 source，则新增 edge(source->target) 将产生环
  return canReach(graph, targetId, sourceId)
}

// 全图是否无环（可用于调试/校验）
export function isAcyclic(graph) {
  if (!graph) return true
  const nodes = graph.getNodes?.() || []
  const inDegree = new Map()
  const adj = new Map()

  nodes.forEach((n) => {
    inDegree.set(n.id, 0)
    adj.set(n.id, [])
  })

  const edges = graph.getEdges?.() || []
  edges.forEach((e) => {
    const s = e.getSourceCellId?.()
    const t = e.getTargetCellId?.()
    if (!s || !t) return
    if (!adj.has(s)) adj.set(s, [])
    adj.get(s).push(t)
    inDegree.set(t, (inDegree.get(t) || 0) + 1)
  })

  const queue = []
  inDegree.forEach((deg, id) => {
    if (deg === 0) queue.push(id)
  })
  let count = 0
  while (queue.length) {
    const u = queue.shift()
    count += 1
    const list = adj.get(u) || []
    list.forEach((v) => {
      inDegree.set(v, (inDegree.get(v) || 0) - 1)
      if (inDegree.get(v) === 0) queue.push(v)
    })
  }
  return count === nodes.length
}
