/**
 * 通用类型定义
 * 这些类型用于补充自动生成的类型，或定义前端特有的类型
 */

/**
 * 统一API响应结构
 */
export interface ApiResponse<T = unknown> {
  code: number;
  msg: string;
  data: T;
}

/**
 * 分页请求参数
 */
export interface PageRequest {
  pageNum?: number;
  pageSize?: number;
}

/**
 * 分页响应结构
 */
export interface PageResponse<T> {
  rows: T[];
  total: number;
}

/**
 * 通用查询参数
 */
export interface BaseQueryParams extends PageRequest {
  beginTime?: string;
  endTime?: string;
  orderByColumn?: string;
  isAsc?: 'asc' | 'desc';
}

/**
 * 通用实体基础字段
 */
export interface BaseEntity {
  createBy?: string;
  createTime?: string;
  updateBy?: string;
  updateTime?: string;
  remark?: string;
}

/**
 * 树形结构节点
 */
export interface TreeNode<T = unknown> {
  id: number | string;
  label: string;
  children?: TreeNode<T>[];
  data?: T;
}

/**
 * 操作结果
 */
export type OperationResult = ApiResponse<null>;

/**
 * 批量操作请求
 */
export interface BatchRequest {
  ids: (number | string)[];
}
