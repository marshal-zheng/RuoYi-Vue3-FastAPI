import { requestDetail } from '@/api/detail';
export type ConfigRecord = Omit<ConfigDetailReadModel, 'configId'> & { configId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type {
  ConfigModel,
  ConfigDetailReadModel,
  ConfigPageQueryModel,
} from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询参数列表
export function listConfig(query?: ConfigPageQueryModel) {
  return request<HttpOffsetPage<ConfigRecord>>({
    url: '/system/config/list',
    method: 'get',
    params: query,
  });
}

// 查询参数详细
export function getConfig(
  configId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError'>
) {
  return requestDetail<ConfigRecord>(
    {
      ...config,
      url: '/system/config/' + configId,
      method: 'get',
    },
    'configId',
    configId
  );
}

// 根据参数键名查询参数值
export function getConfigKey(configKey: string) {
  return request<{ configKey: string; configValue: string }>({
    url: '/system/config/configKey/' + configKey,
    method: 'get',
  });
}

// 新增参数配置
export function addConfig(data: ConfigModel) {
  return request<ConfigRecord>({
    url: '/system/config',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.config.create' },
  });
}

// 修改参数配置
export function updateConfig(data: ConfigModel) {
  return request<ConfigRecord>({
    url: '/system/config',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.config.update' },
  });
}

// 删除参数配置
export function delConfig(configId: number | string) {
  return request<null>({
    url: '/system/config/' + configId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.config.delete' },
  });
}

// 刷新参数缓存
export function refreshCache() {
  return request<{ status: 'refreshed' }>({
    url: '/system/config/refreshCache',
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.config.update' },
  });
}
