import request from '@/utils/request';

// 查询工程列表
export function listProject(query?: Record<string, any>) {
  return request({
    url: '/project/list',
    method: 'get',
    params: query,
  });
}

// 查询工程详细
export function getProject(projectId: number | string) {
  return request({
    url: '/project/' + projectId,
    method: 'get',
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
