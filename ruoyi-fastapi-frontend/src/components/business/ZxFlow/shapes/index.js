// XFlow Vue 库的基础图形支持
// 这里只提供通用的图形注册工具和基础形状

import { Graph } from '@antv/x6'
import { register } from '@antv/x6-vue-shape'

/**
 * 基础图形注册工具类
 * 提供给业务层使用的通用注册方法
 */
export class ShapeRegistry {
  static flags = {}

  /**
   * 检查图形是否已注册
   */
  static isRegistered(shapeName) {
    return !!this.flags[shapeName]
  }

  /**
   * 标记图形已注册
   */
  static markRegistered(shapeName) {
    this.flags[shapeName] = true
  }

  /**
   * 安全注册图形（防重复）
   */
  static safeRegister(shapeName, config, callback) {
    if (this.isRegistered(shapeName)) {
      console.warn(`Shape ${shapeName} already registered`)
      return false
    }

    try {
      const result = callback(config)
      this.markRegistered(shapeName)
      console.log(`Shape ${shapeName} registered successfully`)
      return true
    } catch (e) {
      console.warn(`Failed to register shape ${shapeName}:`, e)
      return false
    }
  }

  /**
   * 注册普通节点
   */
  static registerNode(shapeName, config) {
    return this.safeRegister(shapeName, config, (cfg) => {
      Graph.registerNode(shapeName, cfg)
    })
  }

  /**
   * 注册边
   */
  static registerEdge(shapeName, config) {
    return this.safeRegister(shapeName, config, (cfg) => {
      Graph.registerEdge(shapeName, cfg)
    })
  }

  /**
   * 注册 Vue 组件节点
   */
  static registerVueNode(shapeName, config) {
    return this.safeRegister(shapeName, config, (cfg) => {
      register({
        shape: shapeName,
        ...cfg
      })
    })
  }
}

/**
 * 预定义的基础图形样式
 */
export const BaseShapeStyles = {
  // 基础矩形样式
  rect: {
    attrs: {
      body: {
        stroke: '#d9d9d9',
        strokeWidth: 1,
        fill: '#ffffff',
        rx: 4,
        ry: 4
      },
      text: {
        fontSize: 12,
        fill: '#262626',
        textAnchor: 'middle',
        textVerticalAnchor: 'middle',
        fontFamily: 'Arial, sans-serif'
      }
    }
  },

  // 基础圆形样式
  circle: {
    attrs: {
      body: {
        stroke: '#d9d9d9',
        strokeWidth: 1,
        fill: '#ffffff'
      },
      text: {
        fontSize: 12,
        fill: '#262626',
        textAnchor: 'middle',
        textVerticalAnchor: 'middle',
        fontFamily: 'Arial, sans-serif'
      }
    }
  },

  // 基础边样式
  edge: {
    attrs: {
      line: {
        stroke: '#d9d9d9',
        strokeWidth: 1,
        targetMarker: {
          name: 'classic',
          size: 8
        }
      }
    }
  }
}

/**
 * 端口配置预设
 */
export const PortPresets = {
  // 四向端口
  fourWay: {
    groups: {
      default: {
        position: { name: 'boundary' },
        attrs: {
          circle: {
            r: 4,
            magnet: true,
            stroke: '#8c8c8c',
            strokeWidth: 1,
            fill: '#fff'
          }
        }
      }
    },
    items: [
      { id: 'top', group: 'default', args: { angle: 0 } },
      { id: 'right', group: 'default', args: { angle: 90 } },
      { id: 'bottom', group: 'default', args: { angle: 180 } },
      { id: 'left', group: 'default', args: { angle: 270 } }
    ]
  },

  // 输入输出端口
  inputOutput: {
    groups: {
      input: {
        position: 'left',
        attrs: {
          circle: {
            r: 6,
            magnet: true,
            stroke: '#52c41a',
            strokeWidth: 2,
            fill: '#fff'
          }
        }
      },
      output: {
        position: 'right',
        attrs: {
          circle: {
            r: 6,
            magnet: true,
            stroke: '#1890ff',
            strokeWidth: 2,
            fill: '#fff'
          }
        }
      }
    },
    items: [
      { id: 'input', group: 'input' },
      { id: 'output', group: 'output' }
    ]
  }
}

/**
 * 工具函数：创建带端口的节点配置
 */
export function createPortedNodeConfig(baseConfig, portPreset) {
  return {
    ...baseConfig,
    ports: PortPresets[portPreset] || portPreset
  }
}

/**
 * 工具函数：合并样式配置
 */
export function mergeShapeStyles(baseStyle, customStyle) {
  return {
    ...baseStyle,
    attrs: {
      ...baseStyle.attrs,
      ...customStyle.attrs
    }
  }
}

// 导出常用工具
export { register as registerVueShape } from '@antv/x6-vue-shape'
export { Graph } from '@antv/x6'
