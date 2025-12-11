import request from '@/utils/request';

// 查询设备列表
export function listDevice(query) {
  return request({
    url: '/device/list',
    method: 'get',
    params: query,
  });
}

// 查询设备详细（包含接口配置）
export function getDevice(deviceId) {
  return request({
    url: '/device/' + deviceId,
    method: 'get',
  });
}

// 新增设备（包含接口）
export function addDevice(data) {
  return request({
    url: '/device',
    method: 'post',
    data: data,
  });
}

// 修改设备（包含接口）
export function updateDevice(data) {
  return request({
    url: '/device',
    method: 'put',
    data: data,
  });
}

// 删除设备
export function delDevice(deviceId) {
  return request({
    url: '/device/' + deviceId,
    method: 'delete',
  });
}

// 导出设备数据
export function exportDevice(query) {
  return request({
    url: '/device/export',
    method: 'post',
    params: query,
    responseType: 'blob',
  });
}

// 批量导出设备
export function exportDeviceBatch(data) {
  return request({
    url: '/device/export/batch',
    method: 'post',
    data,
    responseType: 'blob',
  });
}

// 批量导入设备
export function importDeviceBatch(formData) {
  return request({
    url: '/device/import/batch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

// 检查设备名称是否唯一
export function checkDeviceNameUnique(deviceName, deviceId) {
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
export function cloneDevice(data) {
  return request({
    url: '/device/clone',
    method: 'post',
    data: data,
  });
}
