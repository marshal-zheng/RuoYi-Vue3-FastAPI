/**
 * API 共享模块入口
 * 导出所有共享类型和工具
 */

// 导出通用类型
export type {
  ApiResponse,
  PageRequest,
  PageResponse,
  BaseQueryParams,
  BaseEntity,
  TreeNode,
  OperationResult,
  BatchRequest,
} from './types/common';

export type {
  HttpCollection,
  HttpOffsetPage,
  HttpCursorPage,
  BatchResult,
  BatchResultItem,
  BatchResultItemError,
  BatchResultSummary,
  ProblemDetails,
  ProblemValidationError,
  HttpContractMeta,
  HttpPager,
  HttpListResult,
} from '@/types/http-contract';

// 导出 HTTP 客户端
export { http } from './http-client';
