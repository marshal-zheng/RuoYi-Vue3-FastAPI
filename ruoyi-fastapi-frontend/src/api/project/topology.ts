import request from '@/utils/request';
import type { AxiosRequestConfig } from 'axios';

// 保存工程拓扑数据
export function saveProjectTopology(data: Record<string, any>) {
  return request({
    url: '/project/topology/save',
    method: 'post',
    data: data,
  });
}

// 获取工程拓扑数据（可选按版本维度）
export function getProjectTopology(
  projectId: number | string,
  versionId?: number | string,
  options: AxiosRequestConfig = {}
) {
  return request({
    url: '/project/topology/' + projectId,
    method: 'get',
    params: versionId ? { version_id: versionId } : undefined,
    ...options,
  });
}
