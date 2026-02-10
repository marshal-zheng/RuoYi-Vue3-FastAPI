import request from '@/utils/request';
import type { AxiosRequestConfig } from 'axios';

// 查询工程列表
export function listProject(query?: Record<string, any>) {
  return request({
    url: '/project/list',
    method: 'get',
    params: query,
  });
}

// 查询工程详细
export function getProject(projectId: number | string, options: AxiosRequestConfig = {}) {
  return request({
    url: '/project/' + projectId,
    method: 'get',
    ...options,
  });
}

// 新增工程
export function addProject(data: Record<string, any>) {
  return request({
    url: '/project',
    method: 'post',
    data: data,
  });
}

// 修改工程
export function updateProject(data: Record<string, any>) {
  return request({
    url: '/project',
    method: 'put',
    data: data,
  });
}

// 删除工程
export function delProject(projectId: number | string) {
  return request({
    url: '/project/' + projectId,
    method: 'delete',
  });
}

// 导出工程
export function exportProject(projectId: number | string) {
  return request({
    url: '/project/export/' + projectId,
    method: 'get',
    responseType: 'blob',
  });
}

// 批量导出工程（zip）
export function exportProjectBatch(projectIds: (number | string)[]) {
  return request({
    url: '/project/export/batch',
    method: 'post',
    data: { projectIds },
    responseType: 'blob',
  });
}

// 导入工程
export function importProject(data: FormData) {
  return request({
    url: '/project/import',
    method: 'post',
    data: data,
  });
}

// 批量导入工程（zip）
export function importProjectBatch(formData: FormData) {
  return request({
    url: '/project/import/batch',
    method: 'post',
    data: formData,
  });
}
