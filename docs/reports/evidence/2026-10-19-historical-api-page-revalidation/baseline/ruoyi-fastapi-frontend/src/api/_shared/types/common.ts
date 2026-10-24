/**
 * 通用类型定义
 * 这些类型用于补充自动生成的类型，或定义前端特有的类型
 */

import type { HttpOffsetPage, ProblemDetails } from '@/types/http-contract';

/**
 * 资源导向成功响应
 */
export type ApiResponse<T = unknown> = T;

/**
 * 分页请求参数
 */
export interface PageRequest {
  page?: number;
  pageSize?: number;
}

/**
 * 分页响应结构
 */
export type PageResponse<T> = HttpOffsetPage<T>;

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
export type OperationResult = null;

/**
 * 标准错误响应
 */
export type ErrorResponse = ProblemDetails;

/**
 * 批量操作请求
 */
export interface BatchRequest {
  ids: (number | string)[];
}
