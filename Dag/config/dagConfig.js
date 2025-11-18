/**
 * DAG 配置中心 - 向后兼容导出
 * 
 * @deprecated 建议直接从 './config' 或具体的配置文件导入
 * @example
 * // 推荐方式
 * import { DAG_NODE_CONFIG } from '@/components/business/Dag/config'
 * import { DAG_EDGE_CONFIG } from '@/components/business/Dag/config/edgeConfig'
 */

// 从统一入口重新导出（向后兼容）
export * from './index.js'
export { default } from './index.js'


