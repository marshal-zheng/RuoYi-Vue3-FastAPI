import request from '@/utils/request';

// 查询工程列表
export function listProject(query) {
  return request({
    url: '/project/list',
    method: 'get',
    params: query,
  });
}

// 查询工程详细
export function getProject(projectId, options = {}) {
  return request({
    url: '/project/' + projectId,
    method: 'get',
    ...options,
  });
}

// 新增工程
export function addProject(data) {
  return request({
    url: '/project',
    method: 'post',
    data: data,
  });
}

// 修改工程
export function updateProject(data) {
  return request({
    url: '/project',
    method: 'put',
    data: data,
  });
}

// 删除工程
export function delProject(projectId) {
  return request({
    url: '/project/' + projectId,
    method: 'delete',
  });
}

// 导出工程
export function exportProject(projectId) {
  return request({
    url: '/project/export/' + projectId,
    method: 'get',
    responseType: 'blob',
  });
}

// 批量导出工程（zip）
export function exportProjectBatch(projectIds) {
  return request({
    url: '/project/export/batch',
    method: 'post',
    data: { projectIds },
    responseType: 'blob',
  });
}

// 导入工程
export function importProject(data) {
  return request({
    url: '/project/import',
    method: 'post',
    data: data,
  });
}

// 批量导入工程（zip）
export function importProjectBatch(formData) {
  return request({
    url: '/project/import/batch',
    method: 'post',
    data: formData,
  });
}
