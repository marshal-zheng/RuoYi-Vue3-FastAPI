/**
 * DAG 布局配置
 * 统一管理布局算法的间距、方向等配置
 */

// ============================================
// 布局配置
// ============================================
export const DAG_LAYOUT_CONFIG = {
  /**
   * 层级间距（ranksep）
   * 控制不同层级节点之间的距离
   * 适用于横向（LR）和纵向（TB）布局
   */
  ranksep: 220,

  /**
   * 同层节点间距（nodesep）
   * 控制同一层级内节点之间的距离
   */
  nodesep: 100,

  /**
   * 默认布局方向
   * @type {'LR' | 'TB'}
   * LR: 从左到右（横向）
   * TB: 从上到下（纵向）
   */
  defaultDirection: 'TB',
};

// ============================================
// 工具函数
// ============================================

/**
 * 获取完整的布局配置
 * @param {Object} overrides - 覆盖的配置项
 * @returns {Object}
 */
export function getLayoutConfig(overrides = {}) {
  return {
    ...DAG_LAYOUT_CONFIG,
    ...overrides,
  };
}

// ============================================
// 默认导出
// ============================================
export default DAG_LAYOUT_CONFIG;
