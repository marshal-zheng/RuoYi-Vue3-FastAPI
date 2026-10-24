import { requestDetail } from '@/api/detail';
export type DeviceRecord = Omit<DeviceModel, 'deviceId'> & { deviceId: number };
export type DeviceQuery = Partial<Pick<DeviceModel, 'deviceName' | 'busType'>> & {
  beginTime?: string;
  endTime?: string;
  page?: number;
  pageSize?: number;
};
import type { HttpOffsetPage, BatchResult } from '@/types/http-contract';
import type {
  BatchDeviceIdsModel,
  CloneDeviceModel,
  DeviceModel,
} from '@/api/_generated/types.gen';
import request from '@/utils/request';
import type { AxiosRequestConfig } from 'axios';

// 查询设备列表
export function listDevice(query?: DeviceQuery, options: AxiosRequestConfig = {}) {
  return request<HttpOffsetPage<DeviceRecord>>({
    url: '/device/list',
    method: 'get',
    params: query,
    ...options,
  });
}

// 查询设备详细（包含接口配置）
export function getDevice(deviceId: number | string) {
  return requestDetail<DeviceRecord>(
    {
      url: '/device/' + deviceId,
      method: 'get',
    },
    'deviceId',
    deviceId
  );
}

// 新增设备（包含接口）
export function addDevice(data: DeviceModel) {
  return request<DeviceRecord>({
    url: '/device',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'device.device.create' },
  });
}

// 修改设备（包含接口）
export function updateDevice(data: DeviceModel) {
  return request<DeviceRecord>({
    url: '/device',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'device.device.update' },
  });
}

// 删除设备
export function delDevice(deviceId: number | string) {
  return request<null>({
    url: '/device/' + deviceId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'device.device.delete' },
  });
}

// 导出设备数据
export function exportDevice(query?: DeviceQuery) {
  return request<Blob>({
    url: '/device/export',
    method: 'post',
    params: query,
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 批量导出设备
export function exportDeviceBatch(data: BatchDeviceIdsModel) {
  return request<Blob>({
    url: '/device/export/batch',
    method: 'post',
    data,
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 批量导入设备
export function importDeviceBatch(formData: FormData) {
  return request<BatchResult>({
    url: '/device/import/batch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    feedback: { mode: 'auto', key: 'device.device.import-batch' },
  });
}

// 检查设备名称是否唯一
export function checkDeviceNameUnique(deviceName: string, deviceId?: number | string) {
  return request<boolean>({
    url: '/device/checkNameUnique',
    method: 'get',
    params: {
      deviceName: deviceName,
      deviceId: deviceId,
    },
  });
}

// 克隆设备
export function cloneDevice(data: CloneDeviceModel) {
  return request<DeviceRecord>({
    url: '/device/clone',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'device.device.clone' },
  });
}
