/**
 * DAG 节点配置
 * 统一管理节点的尺寸、样式等配置
 */

// ============================================
// 节点配置
// ============================================
export const DAG_NODE_CONFIG = {
  /**
   * 节点尺寸配置
   * 根据布局方向（横向/纵向）使用不同的尺寸
   */
  size: {
    horizontal: {
      width: 200,
      height: 38
    },
    vertical: {
      width: 45,
      height: 200
    }
  },

  /**
   * 节点默认形状名称
   */
  shape: 'dag-node'
}

// ============================================
// 工具函数
// ============================================

/**
 * 根据布局方向获取节点尺寸
 * @param {'LR'|'TB'|'horizontal'|'vertical'} direction - 布局方向
 * @returns {{width: number, height: number}}
 */
export function getNodeSize(direction) {
  const isVertical = direction === 'TB' || direction === 'vertical'
  return isVertical 
    ? DAG_NODE_CONFIG.size.vertical 
    : DAG_NODE_CONFIG.size.horizontal
}

// ============================================
// 默认导出
// ============================================
export default DAG_NODE_CONFIG

