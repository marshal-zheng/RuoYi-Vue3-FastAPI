import request from '@/utils/request'

// 查询设备列表
export function listDevice(query) {
  return request({
    url: '/device/list',
    method: 'get',
    params: query
  })
}

// 查询设备详细（包含接口配置）
export function getDevice(deviceId) {
  return request({
    url: '/device/' + deviceId,
    method: 'get'
  })
}

// 新增设备（包含接口）
export function addDevice(data) {
  return request({
    url: '/device',
    method: 'post',
    data: data
  })
}

// 修改设备（包含接口）
export function updateDevice(data) {
  return request({
    url: '/device',
    method: 'put',
    data: data
  })
}

// 删除设备
export function delDevice(deviceId) {
  return request({
    url: '/device/' + deviceId,
    method: 'delete'
  })
}

// 导出设备数据
export function exportDevice(query) {
  return request({
    url: '/device/export',
    method: 'post',
    params: query,
    responseType: 'blob'
  })
}
