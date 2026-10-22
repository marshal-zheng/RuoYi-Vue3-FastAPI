import { requestDetail } from '@/api/detail';
export type TypeRecord = Omit<DictTypeDetailReadModel, 'dictId'> & { dictId: number };
import type { HttpCollection, HttpOffsetPage } from '@/types/http-contract';
import type {
  DictTypeModel,
  DictTypeDetailReadModel,
  DictTypePageQueryModel,
} from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';
import type { RequestOptions, QueryRequestContext } from '@zxio/http';

// 查询字典类型列表
export function listType(query?: DictTypePageQueryModel, options?: RequestOptions) {
  return request<HttpOffsetPage<TypeRecord>>(
    {
      url: '/system/dict/type/list',
      method: 'get',
      params: query,
    },
    options
  );
}

// 查询字典类型详细
export function getType(
  dictId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return requestDetail<TypeRecord>(
    {
      ...config,
      url: '/system/dict/type/' + dictId,
      method: 'get',
    },
    'dictId',
    dictId
  );
}

// 新增字典类型
export function addType(data: DictTypeModel, options?: RequestOptions) {
  return request<TypeRecord>(
    {
      url: '/system/dict/type',
      method: 'post',
      data: data,
      feedback: { mode: 'auto', key: 'system.dict-type.create' },
    },
    options
  );
}

// 修改字典类型
export function updateType(data: DictTypeModel, options?: RequestOptions) {
  return request<TypeRecord>(
    {
      url: '/system/dict/type',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.dict-type.update' },
    },
    options
  );
}

// 删除字典类型
export function delType(dictId: number | string, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/dict/type/' + dictId,
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.dict-type.delete' },
    },
    options
  );
}

// 刷新字典缓存
export function refreshCache(options?: RequestOptions) {
  return request<{ status: 'refreshed' }>(
    {
      url: '/system/dict/type/refreshCache',
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.dict-type.refresh-cache' },
    },
    options
  );
}

// 获取字典选择框列表
export function optionselect(context?: QueryRequestContext) {
  return request<HttpCollection<DictTypeDetailReadModel>>(
    {
      url: '/system/dict/type/optionselect',
      method: 'get',
      signal: context?.signal,
    },
    context?.options
  );
}
