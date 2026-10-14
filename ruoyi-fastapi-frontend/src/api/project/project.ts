import request from '@/utils/request';
import type { HttpOffsetPage } from '@/types/http-contract';
export type ProjectRecord = Omit<ProjectModel, 'projectId'> & { projectId: number };
import type { AxiosRequestConfig } from 'axios';
import type {
  ProjectModel,
  GetSystemProjectListProjectListGetData,
} from '@/api/_generated/types.gen';

// 查询工程列表
export function listProject(query?: GetSystemProjectListProjectListGetData['query']) {
  return request.get<HttpOffsetPage<ProjectRecord>>('/project/list', { params: query });
}

// 查询工程详细
export function getProject(projectId: number | string, options: AxiosRequestConfig = {}) {
  return request.get<ProjectRecord>('/project/' + projectId, {
    feedback: { mode: 'auto' },
    ...options,
  });
}

// 新增工程
export function addProject(data: ProjectModel) {
  return request.post<ProjectRecord>('/project', data, {
    feedback: { mode: 'auto', key: 'project.project.create' },
  });
}

// 修改工程
export function updateProject(data: ProjectModel) {
  return request.put<ProjectRecord>('/project', data, {
    feedback: { mode: 'auto', key: 'project.project.update' },
  });
}

// 删除工程
export function delProject(projectId: number | string | Array<number | string>) {
  return request.delete(
    '/project/' + (Array.isArray(projectId) ? projectId.join(',') : projectId),
    {
      feedback: { mode: 'auto', key: 'project.project.delete' },
    }
  );
}

// 导出工程
export function exportProject(projectId: number | string) {
  return request.get<Blob>('/project/export/' + projectId, {
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 批量导出工程（zip）
export function exportProjectBatch(projectIds: (number | string)[]) {
  return request.post<Blob>(
    '/project/export/batch',
    { projectIds },
    {
      responseType: 'blob',
      feedback: { mode: 'silent' },
    }
  );
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
  return request.post('/project/import', normalizeImportPayload(data), {
    feedback: { mode: 'auto', key: 'project.project.import' },
  });
}

// 批量导入工程（zip）
export function importProjectBatch(formData: FormData | File) {
  return request.post('/project/import/batch', normalizeImportPayload(formData), {
    feedback: { mode: 'auto', key: 'project.project.import-batch' },
  });
}
