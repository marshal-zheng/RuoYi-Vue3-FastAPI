/**
 * DAG 交互配置
 * 统一管理用户交互相关的配置（对齐线、缩放等）
 */

// ============================================
// 交互配置
// ============================================
export const DAG_INTERACTION_CONFIG = {
  /**
   * 对齐线配置
   */
  snapline: {
    enabled: true,
    tolerance: 15,
    sharp: false,
  },

  /**
   * 缩放配置
   */
  zoom: {
    factor: 1.05,
    minScale: 0.1,
    maxScale: 3,
  },
};

// ============================================
// 默认导出
// ============================================
export default DAG_INTERACTION_CONFIG;
