/**
 * DAG 端口配置
 * 统一管理连接桩的样式、透明度等配置
 */

// ============================================
// 端口配置
// ============================================
export const DEFAULT_PORT_TYPE = 'STANDARD';

export const DAG_PORT_CONFIG = {
  /**
   * 端口半径
   */
  radius: 8,

  /**
   * 端口边框宽度
   */
  strokeWidth: 2,

  /**
   * 端口边框颜色
   */
  strokeColor: '#31d0c6',

  /**
   * 端口填充颜色
   */
  fillColor: '#fff',

  /**
   * 默认透明度（隐藏状态）
   */
  defaultOpacity: 0,

  /**
   * 激活时透明度（显示状态）
   */
  activeOpacity: 1
}

// 向后兼容
export const PORT_CONFIG = DAG_PORT_CONFIG

// ============================================
// 端口组配置
// ============================================
export const PORT_GROUPS = {
  top: {
    position: {
      name: 'top',
      args: {
        x: '50%',
        y: 0
      }
    },
    attrs: {
      circle: {
        r: DAG_PORT_CONFIG.radius,
        magnet: 'passive',
        stroke: DAG_PORT_CONFIG.strokeColor,
        strokeWidth: DAG_PORT_CONFIG.strokeWidth,
        fill: DAG_PORT_CONFIG.fillColor,
        opacity: DAG_PORT_CONFIG.defaultOpacity,
        'data-port-type': DEFAULT_PORT_TYPE
      }
    }
  },
  bottom: {
    position: {
      name: 'bottom',
      args: {
        x: '50%',
        y: 0
      }
    },
    attrs: {
      circle: {
        r: DAG_PORT_CONFIG.radius,
        magnet: true,
        stroke: DAG_PORT_CONFIG.strokeColor,
        strokeWidth: DAG_PORT_CONFIG.strokeWidth,
        fill: DAG_PORT_CONFIG.fillColor,
        opacity: DAG_PORT_CONFIG.defaultOpacity,
        'data-port-type': DEFAULT_PORT_TYPE
      }
    }
  },
  left: {
    position: {
      name: 'left',
      args: {
        x: 0,
        y: '50%'
      }
    },
    attrs: {
      circle: {
        r: DAG_PORT_CONFIG.radius,
        magnet: true,
        stroke: DAG_PORT_CONFIG.strokeColor,
        strokeWidth: DAG_PORT_CONFIG.strokeWidth,
        fill: DAG_PORT_CONFIG.fillColor,
        opacity: DAG_PORT_CONFIG.defaultOpacity,
        'data-port-type': DEFAULT_PORT_TYPE
      }
    }
  },
  right: {
    position: {
      name: 'right',
      args: {
        x: 0,
        y: '50%'
      }
    },
    attrs: {
      circle: {
        r: DAG_PORT_CONFIG.radius,
        magnet: true,
        stroke: DAG_PORT_CONFIG.strokeColor,
        strokeWidth: DAG_PORT_CONFIG.strokeWidth,
        fill: DAG_PORT_CONFIG.fillColor,
        opacity: DAG_PORT_CONFIG.defaultOpacity,
        'data-port-type': DEFAULT_PORT_TYPE
      }
    }
  }
}

// ============================================
// 工具函数
// ============================================

/**
 * 生成节点端口配置
 * @param {string} nodeType - 节点类型
 * @returns {Array} 端口配置数组
 */
export const generateNodePorts = (nodeType) => {
  const ports = []

  // 为所有节点类型生成标准端口，但根据类型控制可见性
  const portConfigs = [
    {
      id: 't',
      group: 'top',
      attrs: {
        circle: {
          r: DAG_PORT_CONFIG.radius,
          magnet: 'passive',
          stroke: DAG_PORT_CONFIG.strokeColor,
          strokeWidth: DAG_PORT_CONFIG.strokeWidth,
          fill: DAG_PORT_CONFIG.fillColor,
          'data-port-type': DEFAULT_PORT_TYPE,
          style: {
            visibility: nodeType !== 'root-node' ? 'visible' : 'hidden'
          }
        }
      },
      position: { name: 'top' }
    },
    {
      id: 'b',
      group: 'bottom',
      attrs: {
        circle: {
          r: DAG_PORT_CONFIG.radius,
          magnet: true,
          stroke: DAG_PORT_CONFIG.strokeColor,
          strokeWidth: DAG_PORT_CONFIG.strokeWidth,
          fill: DAG_PORT_CONFIG.fillColor,
          'data-port-type': DEFAULT_PORT_TYPE,
          style: {
            // 所有节点都可以有底部连接桩，包括叶子节点
            visibility: 'visible'
          }
        }
      },
      position: { name: 'bottom' }
    }
  ]

  return portConfigs.map((config) => ({
    ...config,
    data: {
      portType: DEFAULT_PORT_TYPE
    }
  }))
}

// ============================================
// 默认导出
// ============================================
export default DAG_PORT_CONFIG
