import { DAG_NODE_CONFIG, getNodeSize } from '../config/nodeConfig.js'

// 向后兼容：导出原有的常量名
export const DAG_NODE_SIZE = DAG_NODE_CONFIG.size

/**
 * 根据布局方向（LR/TB）获取节点尺寸
 * @param {'LR'|'TB'} direction
 */
export const getNodeSizeByDirection = (direction) => {
  return getNodeSize(direction)
}

/**
 * 根据布局方向（horizontal/vertical）获取节点尺寸
 * @param {'horizontal'|'vertical'} layout
 */
export const getNodeSizeByLayout = (layout) => {
  return getNodeSize(layout)
}
