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
export function getProject(projectId) {
  return request({
    url: '/project/' + projectId,
    method: 'get',
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
