// 工具函数

// 深度合并对象
export function apply(target, source) {
  if (!source) return target

  Object.keys(source).forEach((key) => {
    if (source[key] !== null && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      if (!target[key] || typeof target[key] !== 'object') {
        target[key] = {}
      }
      apply(target[key], source[key])
    } else {
      target[key] = source[key]
    }
  })

  return target
}

// 算法相关
export function getLayoutDirection(source, target) {
  const dx = target.x - source.x
  const dy = target.y - source.y

  if (Math.abs(dx) > Math.abs(dy)) {
    return dx > 0 ? 'right' : 'left'
  } else {
    return dy > 0 ? 'bottom' : 'top'
  }
}

// 计算两点距离
export function getDistance(point1, point2) {
  const dx = point1.x - point2.x
  const dy = point1.y - point2.y
  return Math.sqrt(dx * dx + dy * dy)
}

// 获取节点中心点
export function getNodeCenter(node) {
  const bbox = node.getBBox()
  return {
    x: bbox.x + bbox.width / 2,
    y: bbox.y + bbox.height / 2
  }
}

// 获取边的路径点
export function getEdgePathPoints(edge) {
  const sourceNode = edge.getSourceNode()
  const targetNode = edge.getTargetNode()

  if (!sourceNode || !targetNode) {
    return []
  }

  const sourceCenter = getNodeCenter(sourceNode)
  const targetCenter = getNodeCenter(targetNode)

  return [sourceCenter, targetCenter]
}

// 防抖函数
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 节流函数
export function throttle(func, limit) {
  let inThrottle
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// 生成随机颜色
export function getRandomColor() {
  const colors = [
    '#1890ff',
    '#52c41a',
    '#faad14',
    '#f5222d',
    '#722ed1',
    '#fa8c16',
    '#13c2c2',
    '#eb2f96',
    '#a0d911',
    '#fadb14'
  ]
  return colors[Math.floor(Math.random() * colors.length)]
}

// 格式化文件大小
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 下载文件
export function downloadFile(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
