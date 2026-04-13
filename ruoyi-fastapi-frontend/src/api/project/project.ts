import request from '@/utils/request';
import type { AxiosRequestConfig } from 'axios';

// 查询工程列表
export function listProject(query?: Record<string, any>) {
  return request.get('/project/list', { params: query });
}

// 查询工程详细
export function getProject(projectId: number | string, options: AxiosRequestConfig = {}) {
  return Object.keys(options).length
    ? request.get('/project/' + projectId, options)
    : request.get('/project/' + projectId);
}

// 新增工程
export function addProject(data: Record<string, any>) {
  return request.post('/project', data);
}

// 修改工程
export function updateProject(data: Record<string, any>) {
  return request.put('/project', data);
}

// 删除工程
export function delProject(projectId: number | string | Array<number | string>) {
  return request.delete('/project/' + (Array.isArray(projectId) ? projectId.join(',') : projectId));
}

// 导出工程
export function exportProject(projectId: number | string) {
  return request.get('/project/export/' + projectId, { responseType: 'blob' });
}

// 批量导出工程（zip）
export function exportProjectBatch(projectIds: (number | string)[]) {
  return request.post('/project/export/batch', { projectIds }, { responseType: 'blob' });
}

const normalizeImportPayload = (data: FormData | File): FormData => {
  if (data instanceof FormData) {
    return data;
  }
  const formData = new FormData();
  formData.append('file', data);
  return formData;
};

// 导入工程
export function importProject(data: FormData | File) {
  return request.post('/project/import', normalizeImportPayload(data));
}

// 批量导入工程（zip）
export function importProjectBatch(formData: FormData | File) {
  return request.post('/project/import/batch', normalizeImportPayload(formData));
}

// 查询工程拓扑
export function getProjectTopology(projectId: number | string) {
  return request.get(`/project/${projectId}/topology`);
}

// 修改工程拓扑
export function updateProjectTopology(projectId: number | string, data: Record<string, any>) {
  return request.put(`/project/${projectId}/topology`, data);
}
