import { getNodeSizeByDirection } from './nodeGeometry.js'

// 简单的 dagre 风格布局实现，避免 @antv/layout 的兼容性问题
// direction: 'TB' | 'LR' (只支持竖向和横向)
export async function dagreLayout(graph, direction = 'TB', ranksep = 150, nodesep = 60) {
  if (!graph) return
  const g = graph?.value ?? graph
  if (!g) return

  const nodes = (g.getNodes?.() || []).filter((node) => node?.isVisible?.() !== false)
  const edges = (g.getEdges?.() || []).filter((edge) => edge?.isVisible?.() !== false)

  if (nodes.length === 0) return

  const isVerticalLayout = direction !== 'LR'
  const targetOrientation = isVerticalLayout ? 'vertical' : 'horizontal'
  const sizeConfig = getNodeSizeByDirection(direction)

  // 构建图的拓扑结构
  const nodeMap = new Map()
  const inDegree = new Map()
  const outEdges = new Map()

  // 初始化节点信息
  nodes.forEach((node) => {
    const id = node.id
    nodeMap.set(id, node)
    inDegree.set(id, 0)
    outEdges.set(id, [])
  })

  // 构建邻接表和入度统计
  edges.forEach((edge) => {
    const sourceId = edge.getSourceCellId()
    const targetId = edge.getTargetCellId()
    if (sourceId && targetId && nodeMap.has(sourceId) && nodeMap.has(targetId)) {
      outEdges.get(sourceId).push(targetId)
      inDegree.set(targetId, inDegree.get(targetId) + 1)
    }
  })

  // 拓扑排序分层
  const levels = []
  const queue = []
  const processed = new Set()

  // 找到所有入度为0的节点作为第一层
  inDegree.forEach((degree, nodeId) => {
    if (degree === 0) {
      queue.push(nodeId)
    }
  })

  while (queue.length > 0) {
    const currentLevel = []
    const levelSize = queue.length

    for (let i = 0; i < levelSize; i++) {
      const nodeId = queue.shift()
      currentLevel.push(nodeId)
      processed.add(nodeId)

      // 更新后继节点的入度
      outEdges.get(nodeId).forEach((targetId) => {
        if (!processed.has(targetId)) {
          inDegree.set(targetId, inDegree.get(targetId) - 1)
          if (inDegree.get(targetId) === 0) {
            queue.push(targetId)
          }
        }
      })
    }

    if (currentLevel.length > 0) {
      levels.push(currentLevel)
    }
  }

  // 处理剩余的节点（可能存在环）
  const remaining = nodes.filter((node) => !processed.has(node.id))
  if (remaining.length > 0) {
    levels.push(remaining.map((node) => node.id))
  }

  // 应用节点尺寸与布局方向，并计算布局位置
  g.batchUpdate?.(() => {
    nodes.forEach((node) => {
      const prevData = node.getData?.() || {}
      if (prevData.layoutDirection !== targetOrientation) {
        node.setData({
          ...prevData,
          layoutDirection: targetOrientation
        })
      }

      const currentSize = node.getSize()
      if (currentSize.width !== sizeConfig.width || currentSize.height !== sizeConfig.height) {
        node.resize(sizeConfig.width, sizeConfig.height)
      }
    })

    const positions = calculatePositions(levels, nodeMap, direction, ranksep, nodesep)

    positions.forEach((pos, nodeId) => {
      const node = nodeMap.get(nodeId)
      if (!node) return

      // 设置节点位置（X6 的 position 是左上角坐标）
      node.position(pos.x, pos.y)
      // 确保四向端口存在
      ensureSidePorts(node)
      // 智能端口管理：去重 + 按方向显隐
      smartPortManagement(node, direction)
    })
  })

  // 智能边重绑：优先保持现有连接，必要时重绑到合适端口
  edges.forEach((edge) => {
    try {
      const sourceId = edge.getSourceCellId()
      const targetId = edge.getTargetCellId()
      if (!sourceId || !targetId) return

      const sourceNode = g.getCellById(sourceId)
      const targetNode = g.getCellById(targetId)
      if (!sourceNode || !targetNode) return

      // 清除手动顶点
      edge.setVertices([])

      const currentSource = edge.getSource()
      const currentTarget = edge.getTarget()

      // 检查当前端口是否适合当前布局方向
      const allowedGroups = direction === 'LR' ? ['left', 'right'] : ['top', 'bottom']

      let needUpdateSource = false
      let needUpdateTarget = false

      // 检查源端口
      if (currentSource && currentSource.port) {
        const sourceGroup = sourceNode.getPortProp?.(currentSource.port, 'group')
        const sourceVisible =
          sourceNode.getPortProp?.(currentSource.port, 'attrs/circle/style/display') !== 'none'
        if (!allowedGroups.includes(sourceGroup) || !sourceVisible) {
          needUpdateSource = true
        }
      } else {
        needUpdateSource = true
      }

      // 检查目标端口
      if (currentTarget && currentTarget.port) {
        const targetGroup = targetNode.getPortProp?.(currentTarget.port, 'group')
        const targetVisible =
          targetNode.getPortProp?.(currentTarget.port, 'attrs/circle/style/display') !== 'none'
        if (!allowedGroups.includes(targetGroup) || !targetVisible) {
          needUpdateTarget = true
        }
      } else {
        needUpdateTarget = true
      }

      // 重绑源端口
      if (needUpdateSource) {
        const sourcePort = direction === 'LR' ? 'r' : 'b'
        const sourcePorts = sourceNode.getPorts?.() || []
        const sourcePortExists = sourcePorts.some((p) => p.id === sourcePort)
        if (sourcePortExists) {
          edge.setSource({ cell: sourceId, port: sourcePort })
        }
      }

      // 重绑目标端口
      if (needUpdateTarget) {
        const targetPort = direction === 'LR' ? 'l' : 't'
        const targetPorts = targetNode.getPorts?.() || []
        const targetPortExists = targetPorts.some((p) => p.id === targetPort)
        if (targetPortExists) {
          edge.setTarget({ cell: targetId, port: targetPort })
        }
      }

      // 保持使用贝塞尔曲线连接器（DAG_CONNECTOR）
      // 不设置 router 和 connector，让边使用注册时的默认配置
    } catch (e) {
      console.warn('Failed to update edge:', e)
    }
  })
}

// 计算各层节点的位置
function calculatePositions(levels, nodeMap, direction, ranksep, nodesep) {
  const positions = new Map()

  if (levels.length === 0) return positions

  // 根据方向确定主轴和交叉轴
  const isVertical = direction === 'TB'
  const isReverse = false // 不支持反向布局

  let currentMainPos = 0

  levels.forEach((level, levelIndex) => {
    // 计算当前层的总宽度/高度
    let totalCrossSize = 0
    const nodeSizes = level.map((nodeId) => {
      const node = nodeMap.get(nodeId)
      const size = node.getSize()
      return isVertical ? size.width : size.height
    })

    totalCrossSize = nodeSizes.reduce((sum, size) => sum + size, 0) + (level.length - 1) * nodesep

    // 计算起始位置（居中对齐）
    let currentCrossPos = -totalCrossSize / 2

    // 计算当前层的主轴位置
    const levelMainPos = isReverse ? -currentMainPos : currentMainPos

    level.forEach((nodeId, nodeIndex) => {
      const node = nodeMap.get(nodeId)
      const size = node.getSize()
      const nodeSize = nodeSizes[nodeIndex]

      // 计算节点中心位置，然后转换为左上角位置
      let x, y

      if (isVertical) {
        x = currentCrossPos + nodeSize / 2 - size.width / 2
        y = levelMainPos - size.height / 2
        currentCrossPos += nodeSize + nodesep
      } else {
        x = levelMainPos - size.width / 2
        y = currentCrossPos + nodeSize / 2 - size.height / 2
        currentCrossPos += nodeSize + nodesep
      }

      positions.set(nodeId, { x, y })
    })

    // 计算下一层的位置
    if (levelIndex < levels.length - 1) {
      // 找到当前层节点的最大尺寸
      const maxMainSize = level.reduce((max, nodeId) => {
        const node = nodeMap.get(nodeId)
        const size = node.getSize()
        const mainSize = isVertical ? size.height : size.width
        return Math.max(max, mainSize)
      }, 0)

      currentMainPos += maxMainSize + ranksep
    }
  })

  return positions
}

// 保障每个节点具备上下左右四向端口（id 固定：t/b/l/r）
function ensureSidePorts(node) {
  const list = (node.getPorts?.() || []).map((p) => p.id)
  const need = [
    { id: 't', group: 'top' },
    { id: 'b', group: 'bottom' },
    { id: 'l', group: 'left' },
    { id: 'r', group: 'right' }
  ]
  need.forEach(({ id, group }) => {
    if (!list.includes(id)) {
      node.addPort({ id, group })
    } else if (node.setPortProp) {
      node.setPortProp(id, 'group', group)
    }
  })
}

// 智能端口管理：统一处理端口去重和按方向显隐
function smartPortManagement(node, direction) {
  const ports = node.getPorts?.() || []
  const standardPorts = new Set(['t', 'b', 'l', 'r'])
  const showGroups = direction === 'LR' ? ['left', 'right'] : ['top', 'bottom']
  const inputGroup = direction === 'LR' ? 'left' : 'top'

  // 获取所有连接到此节点的边
  const connectedEdges = node.getEdges?.() || []
  const usedPorts = new Set()

  // 收集正在使用的端口ID
  connectedEdges.forEach((edge) => {
    const source = edge.getSource()
    const target = edge.getTarget()
    if (source && source.cell === node.id && source.port) {
      usedPorts.add(source.port)
    }
    if (target && target.cell === node.id && target.port) {
      usedPorts.add(target.port)
    }
  })

  // 对于每个group的多个端口，选择一个显示的端口
  const groupVisiblePort = new Map() // group -> 显示的端口ID
  const groupPorts = new Map() // group -> 该组所有端口列表

  // 按group分组端口
  ports.forEach((p) => {
    const group = p.group || node.getPortProp?.(p.id, 'group')
    if (!group) return

    if (!groupPorts.has(group)) {
      groupPorts.set(group, [])
    }
    groupPorts.get(group).push(p)
  })

  // 为每个group选择要显示的端口
  groupPorts.forEach((portList, group) => {
    // 优先选择标准端口ID
    const standardPort = portList.find((p) => standardPorts.has(p.id))
    if (standardPort) {
      groupVisiblePort.set(group, standardPort.id)
      return
    }

    // 其次选择正在被使用的端口
    const usedPort = portList.find((p) => usedPorts.has(p.id))
    if (usedPort) {
      groupVisiblePort.set(group, usedPort.id)
      return
    }

    // 最后选择第一个端口
    if (portList.length > 0) {
      groupVisiblePort.set(group, portList[0].id)
    }
  })

  // 统一处理所有端口的显隐和可连接性
  ports.forEach((p) => {
    const group = p.group || node.getPortProp?.(p.id, 'group')

    // 是否为该组的代表端口
    const isGroupRepresentative = groupVisiblePort.get(group) === p.id

    // 是否应该根据布局方向显示
    const shouldShowByDirection = showGroups.includes(group)

    // 最终是否显示：必须是组代表 且 符合布局方向
    const shouldShow = isGroupRepresentative && shouldShowByDirection

    // 设置显示和可连接性
    node.setPortProp?.(p.id, 'attrs/circle/style/display', shouldShow ? '' : 'none')
    const isInput = group === inputGroup
    const magnetValue = shouldShow ? (isInput ? 'passive' : true) : false
    node.setPortProp?.(p.id, 'attrs/circle/magnet', magnetValue)

    // 强制重置端口位置，确保居中对齐
    if (shouldShow && isGroupRepresentative) {
      const positionConfig = getPortPositionConfig(group)
      if (positionConfig) {
        node.setPortProp?.(p.id, 'position', positionConfig)
      }
    }
  })
}

// 获取端口位置配置
function getPortPositionConfig(group) {
  const configs = {
    top: {
      name: 'top',
      args: { x: '50%', y: 0 }
    },
    bottom: {
      name: 'bottom',
      args: { x: '50%', y: 0 }
    },
    left: {
      name: 'left',
      args: { x: 0, y: '50%' }
    },
    right: {
      name: 'right',
      args: { x: 0, y: '50%' }
    }
  }
  return configs[group] || null
}
