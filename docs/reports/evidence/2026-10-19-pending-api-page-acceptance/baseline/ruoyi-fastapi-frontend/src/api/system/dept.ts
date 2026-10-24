import { requestDetail } from '@/api/detail';
import type { RequestOptions } from '@zxio/http';
export type DeptRecord = Omit<DeptModel, 'deptId'> & { deptId: number };
import type { HttpCollection } from '@/types/http-contract';
import type {
  DeptCreateModel,
  DeptModel,
  DeptQueryModel,
  DeptUpdateModel,
} from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询部门列表
export function listDept(
  query?: DeptQueryModel,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return request<HttpCollection<DeptRecord>>({
    ...config,
    url: '/system/dept/list',
    method: 'get',
    params: query,
  });
}

// 查询部门列表（排除节点）
export function listDeptExcludeChild(
  deptId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return request<HttpCollection<DeptRecord>>({
    ...config,
    url: '/system/dept/list/exclude/' + deptId,
    method: 'get',
  });
}

// 查询部门详细
export function getDept(
  deptId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return requestDetail<DeptRecord>(
    {
      ...config,
      url: '/system/dept/' + deptId,
      method: 'get',
      feedback: { mode: 'auto' },
    },
    'deptId',
    deptId
  );
}

// 新增部门
export function addDept(data: DeptCreateModel, options?: RequestOptions) {
  return request<DeptRecord>(
    {
      url: '/system/dept',
      method: 'post',
      data: data,
      feedback: { mode: 'auto', key: 'system.dept.create' },
    },
    options
  );
}

// 修改部门
export function updateDept(data: DeptUpdateModel, options?: RequestOptions) {
  return request<DeptRecord>(
    {
      url: '/system/dept',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.dept.update' },
    },
    options
  );
}

// 删除部门
export function delDept(deptId: number | string, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/dept/' + deptId,
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.dept.delete' },
    },
    options
  );
}
