import request from '@/utils/request';
import type { AxiosRequestConfig } from 'axios';

// 查询设备列表
export function listDevice(query?: Record<string, any>, options: AxiosRequestConfig = {}) {
  return request({
    url: '/device/list',
    method: 'get',
    params: query,
    ...options,
  });
}

// 查询设备详细（包含接口配置）
export function getDevice(deviceId: number | string) {
  return request({
    url: '/device/' + deviceId,
    method: 'get',
  });
}

// 新增设备（包含接口）
export function addDevice(data: Record<string, any>) {
  return request({
    url: '/device',
    method: 'post',
    data: data,
  });
}

// 修改设备（包含接口）
export function updateDevice(data: Record<string, any>) {
  return request({
    url: '/device',
    method: 'put',
    data: data,
  });
}

// 删除设备
export function delDevice(deviceId: number | string) {
  return request({
    url: '/device/' + deviceId,
    method: 'delete',
  });
}

// 导出设备数据
export function exportDevice(query?: Record<string, any>) {
  return request({
    url: '/device/export',
    method: 'post',
    params: query,
    responseType: 'blob',
  });
}

// 批量导出设备
export function exportDeviceBatch(data: Record<string, any>) {
  return request({
    url: '/device/export/batch',
    method: 'post',
    data,
    responseType: 'blob',
  });
}

// 批量导入设备
export function importDeviceBatch(formData: FormData) {
  return request({
    url: '/device/import/batch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false },
  });
}

// 检查设备名称是否唯一
export function checkDeviceNameUnique(deviceName: string, deviceId?: number | string) {
  return request({
    url: '/device/checkNameUnique',
    method: 'get',
    params: {
      deviceName: deviceName,
      deviceId: deviceId,
    },
  });
}

// 克隆设备
export function cloneDevice(data: Record<string, any>) {
  return request({
    url: '/device/clone',
    method: 'post',
    data: data,
  });
}
