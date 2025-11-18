import request from '@/utils/request';

// 保存工程拓扑数据
export function saveProjectTopology(data) {
  return request({
    url: '/project/topology/save',
    method: 'post',
    data: data,
  });
}

// 获取工程拓扑数据（可选按版本维度）
export function getProjectTopology(projectId, versionId) {
  return request({
    url: '/project/topology/' + projectId,
    method: 'get',
    params: versionId ? { versionId } : undefined,
  });
}
