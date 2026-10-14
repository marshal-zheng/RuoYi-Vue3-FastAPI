export type TypeRecord = Omit<DictTypeModel, 'dictId'> & { dictId: number };
import type { HttpCollection, HttpOffsetPage } from '@/types/http-contract';
import type { DictTypeModel, DictTypePageQueryModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询字典类型列表
export function listType(query?: DictTypePageQueryModel) {
  return request<HttpOffsetPage<TypeRecord>>({
    url: '/system/dict/type/list',
    method: 'get',
    params: query,
  });
}

// 查询字典类型详细
export function getType(dictId: number | string) {
  return request<TypeRecord>({
    url: '/system/dict/type/' + dictId,
    method: 'get',
  });
}

// 新增字典类型
export function addType(data: DictTypeModel) {
  return request<TypeRecord>({
    url: '/system/dict/type',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.dict-type.create' },
  });
}

// 修改字典类型
export function updateType(data: DictTypeModel) {
  return request<TypeRecord>({
    url: '/system/dict/type',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.dict-type.update' },
  });
}

// 删除字典类型
export function delType(dictId: number | string) {
  return request<null>({
    url: '/system/dict/type/' + dictId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.dict-type.delete' },
  });
}

// 刷新字典缓存
export function refreshCache() {
  return request<{ status: 'refreshed' }>({
    url: '/system/dict/type/refreshCache',
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.dict-type.refresh-cache' },
  });
}

// 获取字典选择框列表
export function optionselect() {
  return request<HttpCollection<DictTypeModel>>({
    url: '/system/dict/type/optionselect',
    method: 'get',
  });
}
