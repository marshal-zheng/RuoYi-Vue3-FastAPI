/**
 * DAG 配置中心 - 统一入口
 * 
 * @description
 * 这是 DAG 图形配置的统一入口文件
 * 从各个独立的配置模块中导入并重新导出，方便统一管理
 * 
 * @example
 * // 方式 1: 导入特定配置
 * import { DAG_NODE_CONFIG, DAG_EDGE_CONFIG } from '@/components/business/Dag/config'
 * 
 * // 方式 2: 导入所有配置
 * import dagConfig from '@/components/business/Dag/config'
 * const nodeSize = dagConfig.node.size.horizontal
 */

// 导入各个配置模块
import { DAG_NODE_CONFIG, getNodeSize } from './nodeConfig.js'
import { DAG_EDGE_CONFIG, getEdgeStyle, createEdgeLabel } from './edgeConfig.js'
import { DAG_LAYOUT_CONFIG, getLayoutConfig } from './layoutConfig.js'
import { DAG_CONNECTOR_CONFIG } from './connectorConfig.js'
import { DAG_PORT_CONFIG, PORT_CONFIG, PORT_GROUPS, generateNodePorts } from './portConfig.js'
import { DAG_INTERACTION_CONFIG } from './interactionConfig.js'

// ============================================
// 重新导出所有配置
// ============================================
export {
  // 配置对象
  DAG_NODE_CONFIG,
  DAG_EDGE_CONFIG,
  DAG_LAYOUT_CONFIG,
  DAG_CONNECTOR_CONFIG,
  DAG_PORT_CONFIG,
  DAG_INTERACTION_CONFIG,
  
  // 端口相关
  PORT_CONFIG,
  PORT_GROUPS,
  generateNodePorts,
  
  // 工具函数
  getNodeSize,
  getEdgeStyle,
  createEdgeLabel,
  getLayoutConfig
}

// ============================================
// 默认导出（包含所有配置的对象）
// ============================================
export default {
  // 配置对象
  node: DAG_NODE_CONFIG,
  edge: DAG_EDGE_CONFIG,
  layout: DAG_LAYOUT_CONFIG,
  connector: DAG_CONNECTOR_CONFIG,
  port: DAG_PORT_CONFIG,
  interaction: DAG_INTERACTION_CONFIG,
  
  // 端口相关
  PORT_GROUPS,
  generateNodePorts,
  
  // 工具函数
  getNodeSize,
  getEdgeStyle,
  createEdgeLabel,
  getLayoutConfig
}

