import { requestDetail } from '@/api/detail';
export type DeviceCategoryRecord = Omit<DeviceCategoryModel, 'deviceCategoryId'> & {
  deviceCategoryId: number;
};
export type DeviceCategoryQuery = Partial<Pick<DeviceCategoryModel, 'name' | 'status'>> & {
  beginTime?: string;
  endTime?: string;
  page?: number;
  pageSize?: number;
};
import type { HttpCollection, HttpOffsetPage } from '@/types/http-contract';
import type { DeviceCategoryModel, DeviceCategoryOptionModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询设备分类列表
export function listDeviceCategory(query?: DeviceCategoryQuery) {
  return request<HttpOffsetPage<DeviceCategoryRecord>>({
    url: '/device/category/list',
    method: 'get',
    params: query,
  });
}

// 查询设备分类详细
export function getDeviceCategory(categoryId: number | string) {
  return requestDetail<DeviceCategoryRecord>(
    {
      url: '/device/category/' + categoryId,
      method: 'get',
    },
    'deviceCategoryId',
    categoryId
  );
}

// 新增设备分类
export function addDeviceCategory(data: DeviceCategoryModel) {
  return request<DeviceCategoryRecord>({
    url: '/device/category',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'device.category.create' },
  });
}

// 修改设备分类
export function updateDeviceCategory(data: DeviceCategoryModel) {
  return request<DeviceCategoryRecord>({
    url: '/device/category',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'device.category.update' },
  });
}

// 删除设备分类
export function delDeviceCategory(categoryId: number | string) {
  return request<null>({
    url: '/device/category/' + categoryId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'device.category.delete' },
  });
}

// 导出设备分类数据
export function exportDeviceCategory(query?: DeviceCategoryQuery) {
  return request<Blob>({
    url: '/device/category/export',
    method: 'post',
    params: query,
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 获取设备分类选项(用于下拉选择)
export type DeviceCategoryOption = DeviceCategoryOptionModel;
export function getDeviceCategoryOptions() {
  return request<HttpCollection<DeviceCategoryOption>>({
    url: '/device/category/options',
    method: 'get',
  });
}

// 检查分类名称是否唯一
export function checkCategoryNameUnique(name: string, categoryId?: number | string) {
  return request<boolean>({
    url: '/device/category/checkNameUnique',
    method: 'get',
    params: {
      name: name,
      category_id: categoryId,
    },
  });
}
