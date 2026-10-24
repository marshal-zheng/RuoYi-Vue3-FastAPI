import { requestDetail } from '@/api/detail';
export type DataRecord = Omit<DictDataModel, 'dictCode'> & { dictCode: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type { DictDataModel, DictDataPageQueryModel } from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';
import type { HttpCollection } from '@/types/http-contract';
import type { RequestOptions } from '@zxio/http';

export interface DictData {
  dictLabel: string;
  dictValue: string;
  dictType?: string;
  listClass?: string;
  cssClass?: string;
  status?: string;
}

// 查询字典数据列表
export function listData(query?: DictDataPageQueryModel, options?: RequestOptions) {
  return request<HttpOffsetPage<DataRecord>>(
    {
      url: '/system/dict/data/list',
      method: 'get',
      params: query,
    },
    options
  );
}

// 查询字典数据详细
export function getData(
  dictCode: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError'>
) {
  return requestDetail<DataRecord>(
    {
      ...config,
      url: '/system/dict/data/' + dictCode,
      method: 'get',
    },
    'dictCode',
    dictCode
  );
}

// 根据字典类型查询字典数据信息
export function getDicts(
  dictType: string,
  context?: { signal: AbortSignal; options: RequestOptions }
) {
  return request<HttpCollection<DictData>>(
    {
      url: '/system/dict/data/type/' + encodeURIComponent(dictType),
      method: 'get',
      signal: context?.signal,
    },
    context?.options
  );
}

// 新增字典数据
export function addData(data: DictDataModel, options?: RequestOptions) {
  return request<DataRecord>(
    {
      url: '/system/dict/data',
      method: 'post',
      data: data,
      feedback: { mode: 'auto', key: 'system.dict-data.create' },
    },
    options
  );
}

// 修改字典数据
export function updateData(data: DictDataModel, options?: RequestOptions) {
  return request<DataRecord>(
    {
      url: '/system/dict/data',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.dict-data.update' },
    },
    options
  );
}

// 删除字典数据
export function delData(dictCode: number | string, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/dict/data/' + dictCode,
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.dict-data.delete' },
    },
    options
  );
}
