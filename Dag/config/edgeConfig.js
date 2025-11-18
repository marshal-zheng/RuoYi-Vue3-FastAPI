/**
 * DAG 边配置
 * 统一管理边的样式、标签等配置
 */

// ============================================
// 边配置
// ============================================
export const DAG_EDGE_CONFIG = {
  /**
   * 边的默认形状名称
   */
  shape: 'dag-edge',

  /**
   * 边的样式配置
   */
  style: {
    // 默认状态
    normal: {
      stroke: '#C2C8D5',
      strokeWidth: 4
    },
    // 悬停状态
    hover: {
      stroke: '#66b1ff',
      strokeWidth: 5
    },
    // 选中状态
    selected: {
      stroke: '#409eff',
      strokeWidth: 6,
      shadow: {
        dx: 0,
        dy: 0,
        blur: 6,
        color: 'rgba(24, 144, 255, 0.4)'
      }
    }
  },

  /**
   * 边标签配置
   */
  label: {
    // 权重标签样式
    weight: {
      fill: '#409eff',
      fontSize: 13,
      fontWeight: 600,
      textAnchor: 'middle',
      textVerticalAnchor: 'middle',
      cursor: 'pointer'
    },
    // 标签背景样式（设置为透明，不显示背景）
    rect: {
      fill: 'transparent',
      stroke: 'transparent',
      strokeWidth: 0,
      rx: 0,
      ry: 0
    },
    // 标签位置
    position: {
      distance: 0.75, // 在边的偏下方位置（0-1之间，0.5为中点，值越大越靠近终点）
      offset: { x: 0, y: 0 }
    }
  }
}

// ============================================
// 工具函数
// ============================================

/**
 * 获取边的样式（根据状态）
 * @param {'normal'|'hover'|'selected'} state - 边的状态
 * @returns {Object}
 */
export function getEdgeStyle(state = 'normal') {
  return DAG_EDGE_CONFIG.style[state] || DAG_EDGE_CONFIG.style.normal
}

/**
 * 创建边标签配置
 * @param {string|number} text - 标签文本（通常是权重值）
 * @returns {Object} 边标签配置对象
 */
export function createEdgeLabel(text) {
  return {
    attrs: {
      text: {
        text: String(text),
        ...DAG_EDGE_CONFIG.label.weight
      },
      rect: {
        ...DAG_EDGE_CONFIG.label.rect
      }
    },
    position: DAG_EDGE_CONFIG.label.position
  }
}

// ============================================
// 默认导出
// ============================================
export default DAG_EDGE_CONFIG

