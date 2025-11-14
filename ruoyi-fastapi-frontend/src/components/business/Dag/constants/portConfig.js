/**
 * DAG 图形连接桩配置
 * 统一管理连接桩的大小、样式等配置
 */

// 连接桩基础配置
export const PORT_CONFIG = {
  // 连接桩半径
  radius: 8,
  // 连接桩边框宽度
  strokeWidth: 2,
  // 连接桩边框颜色
  strokeColor: '#31d0c6',
  // 连接桩填充颜色
  fillColor: '#fff',
  // 默认透明度
  defaultOpacity: 0,
  // 激活时透明度
  activeOpacity: 1
}

// 连接桩组配置
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
        r: PORT_CONFIG.radius,
        magnet: 'passive',
        stroke: PORT_CONFIG.strokeColor,
        strokeWidth: PORT_CONFIG.strokeWidth,
        fill: PORT_CONFIG.fillColor,
        opacity: PORT_CONFIG.defaultOpacity
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
        r: PORT_CONFIG.radius,
        magnet: true,
        stroke: PORT_CONFIG.strokeColor,
        strokeWidth: PORT_CONFIG.strokeWidth,
        fill: PORT_CONFIG.fillColor,
        opacity: PORT_CONFIG.defaultOpacity
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
        r: PORT_CONFIG.radius,
        magnet: true,
        stroke: PORT_CONFIG.strokeColor,
        strokeWidth: PORT_CONFIG.strokeWidth,
        fill: PORT_CONFIG.fillColor,
        opacity: PORT_CONFIG.defaultOpacity
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
        r: PORT_CONFIG.radius,
        magnet: true,
        stroke: PORT_CONFIG.strokeColor,
        strokeWidth: PORT_CONFIG.strokeWidth,
        fill: PORT_CONFIG.fillColor,
        opacity: PORT_CONFIG.defaultOpacity
      }
    }
  }
}

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
          r: PORT_CONFIG.radius,
          magnet: 'passive',
          stroke: PORT_CONFIG.strokeColor,
          strokeWidth: PORT_CONFIG.strokeWidth,
          fill: PORT_CONFIG.fillColor,
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
          r: PORT_CONFIG.radius,
          magnet: true,
          stroke: PORT_CONFIG.strokeColor,
          strokeWidth: PORT_CONFIG.strokeWidth,
          fill: PORT_CONFIG.fillColor,
          style: {
            // 所有节点都可以有底部连接桩，包括叶子节点
            visibility: 'visible'
          }
        }
      },
      position: { name: 'bottom' }
    }
  ]

  return portConfigs
}
