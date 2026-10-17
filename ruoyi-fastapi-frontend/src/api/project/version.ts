import { requestDetail } from '@/api/detail';
import request from '@/utils/request';
import type { HttpOffsetPage } from '@/types/http-contract';
export type ProjectVersionRecord = Omit<ProjectVersionModel, 'versionId'> & { versionId: number };
import type {
  ProjectVersionModel,
  CloneProjectVersionModel,
  LockProjectVersionModel,
  ExportProjectVersionModel,
  GetProjectVersionListProjectVersionListGetData,
} from '@/api/_generated/types.gen';

// 查询项目版本列表
export function listProjectVersion(
  query?: GetProjectVersionListProjectVersionListGetData['query']
) {
  return request<HttpOffsetPage<ProjectVersionRecord>>({
    url: '/project/version/list',
    method: 'get',
    params: query,
  });
}

// 查询项目版本详细
export function getProjectVersion(versionId: number | string) {
  return requestDetail<ProjectVersionRecord>(
    {
      url: '/project/version/' + versionId,
      method: 'get',
    },
    'versionId',
    versionId
  );
}

// 新增项目版本
export function addProjectVersion(data: ProjectVersionModel) {
  return request<ProjectVersionRecord>({
    url: '/project/version',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'project.version.create' },
  });
}

// 修改项目版本
export function updateProjectVersion(data: ProjectVersionModel) {
  return request<ProjectVersionRecord>({
    url: '/project/version',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'project.version.update' },
  });
}

// 删除项目版本
export function delProjectVersion(versionId: number | string) {
  return request({
    url: '/project/version/' + versionId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'project.version.delete' },
  });
}

// 克隆项目版本
export function cloneProjectVersion(data: CloneProjectVersionModel) {
  return request<ProjectVersionRecord>({
    url: '/project/version/clone',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'project.version.clone' },
  });
}

// 固化/解除固化项目版本
export function lockProjectVersion(data: LockProjectVersionModel) {
  return request<ProjectVersionRecord>({
    url: '/project/version/lock',
    method: 'put',
    data: data,
    feedback: {
      mode: 'auto',
      key: 'project.version.lock-state',
      successContext: {
        action: data?.isLocked === '1' ? 'lock' : 'unlock',
      },
    },
  });
}

// 批量解除项目下的固化版本
export function unlockProjectVersions(projectId: number | string) {
  return request({
    url: `/project/version/unlock/project/${projectId}`,
    method: 'put',
    feedback: {
      mode: 'auto',
      key: 'project.version.unlock-project',
    },
  });
}

// 导出项目版本为Word文档
export function exportProjectVersion(data: ExportProjectVersionModel) {
  return request<Blob>({
    url: '/project/version/export',
    method: 'post',
    data: data,
    responseType: 'blob',
    // 导出包含拓扑图生成，耗时较长，单独放宽超时时间
    timeout: 120000,
    feedback: { mode: 'silent' },
  });
}

// 导出项目版本附录Excel（ZIP）
export function exportProjectVersionExcel(versionId: number | string) {
  return request<Blob>({
    url: `/project/version/export-excel/${versionId}`,
    method: 'get',
    responseType: 'blob',
    timeout: 120000,
    feedback: { mode: 'silent' },
  });
}

// 导出项目版本为XML
export function exportProjectVersionXml(versionId: number | string) {
  return request<Blob>({
    url: `/project/version/export-xml/${versionId}`,
    method: 'get',
    responseType: 'blob',
    timeout: 120000,
    feedback: { mode: 'silent' },
  });
}
