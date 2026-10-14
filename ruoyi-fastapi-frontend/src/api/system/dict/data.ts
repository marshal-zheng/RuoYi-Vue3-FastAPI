export type DataRecord = Omit<DictDataModel, 'dictCode'> & { dictCode: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type { DictDataModel, DictDataPageQueryModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';
import type { HttpCollection } from '@/types/http-contract';

export interface DictData {
  dictLabel: string;
  dictValue: string;
  dictType?: string;
  listClass?: string;
  cssClass?: string;
  status?: string;
}

// 查询字典数据列表
export function listData(query?: DictDataPageQueryModel) {
  return request<HttpOffsetPage<DataRecord>>({
    url: '/system/dict/data/list',
    method: 'get',
    params: query,
  });
}

// 查询字典数据详细
export function getData(dictCode: number | string) {
  return request<DataRecord>({
    url: '/system/dict/data/' + dictCode,
    method: 'get',
  });
}

// Hook、选择器等消费者共用正在进行的请求，避免 HTTP 客户端取消同类型的前一个请求。
// 仅合并 in-flight 请求；完成或失败后仍可重新加载最新字典。
const pendingDictionaryRequests = new Map<string, Promise<HttpCollection<DictData>>>();

// 根据字典类型查询字典数据信息
export function getDicts(dictType: string) {
  const pending = pendingDictionaryRequests.get(dictType);
  if (pending) return pending;

  const response = request<HttpCollection<DictData>>({
    url: '/system/dict/data/type/' + dictType,
    method: 'get',
  }).finally(() => {
    pendingDictionaryRequests.delete(dictType);
  });
  pendingDictionaryRequests.set(dictType, response);
  return response;
}

// 新增字典数据
export function addData(data: DictDataModel) {
  return request<DataRecord>({
    url: '/system/dict/data',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.dict-data.create' },
  });
}

// 修改字典数据
export function updateData(data: DictDataModel) {
  return request<DataRecord>({
    url: '/system/dict/data',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.dict-data.update' },
  });
}

// 删除字典数据
export function delData(dictCode: number | string) {
  return request<null>({
    url: '/system/dict/data/' + dictCode,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.dict-data.delete' },
  });
}
