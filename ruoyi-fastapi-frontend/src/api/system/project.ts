export type ProjectRecord = Omit<ProjectModel, 'projectId'> & { projectId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type {
  GetSystemProjectListProjectListGetData,
  ProjectModel,
} from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询工程列表
export function listProject(query?: NonNullable<GetSystemProjectListProjectListGetData['query']>) {
  return request<HttpOffsetPage<ProjectRecord>>({
    url: '/project/list',
    method: 'get',
    params: query,
  });
}

// 查询工程详细
export function getProject(projectId: number | string) {
  return request<ProjectRecord>({
    url: '/project/' + projectId,
    method: 'get',
    feedback: { mode: 'auto' },
  });
}

// 新增工程
export function addProject(data: ProjectModel) {
  return request<ProjectRecord>({
    url: '/project',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'project.project.create' },
  });
}

// 修改工程
export function updateProject(data: ProjectModel) {
  return request<ProjectRecord>({
    url: '/project',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'project.project.update' },
  });
}

// 删除工程
export function delProject(projectId: number | string) {
  return request<null>({
    url: '/project/' + projectId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'project.project.delete' },
  });
}
