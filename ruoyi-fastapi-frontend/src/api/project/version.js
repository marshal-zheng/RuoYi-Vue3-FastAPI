import request from '@/utils/request';

// 查询项目版本列表
export function listProjectVersion(query) {
  return request({
    url: '/project/version/list',
    method: 'get',
    params: query,
  });
}

// 查询项目版本详细
export function getProjectVersion(versionId) {
  return request({
    url: '/project/version/' + versionId,
    method: 'get',
  });
}

// 新增项目版本
export function addProjectVersion(data) {
  return request({
    url: '/project/version',
    method: 'post',
    data: data,
  });
}

// 修改项目版本
export function updateProjectVersion(data) {
  return request({
    url: '/project/version',
    method: 'put',
    data: data,
  });
}

// 删除项目版本
export function delProjectVersion(versionId) {
  return request({
    url: '/project/version/' + versionId,
    method: 'delete',
  });
}

// 克隆项目版本
export function cloneProjectVersion(data) {
  return request({
    url: '/project/version/clone',
    method: 'post',
    data: data,
  });
}

// 固化/解除固化项目版本
export function lockProjectVersion(data) {
  return request({
    url: '/project/version/lock',
    method: 'put',
    data: data,
  });
}

// 批量解除项目下的固化版本
export function unlockProjectVersions(projectId) {
  return request({
    url: `/project/version/unlock/project/${projectId}`,
    method: 'put',
  });
}
