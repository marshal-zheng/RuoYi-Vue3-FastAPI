import request from '@/utils/request'

// 查询协议列表
export function listProtocol(query) {
  return request({
    url: '/system/protocol/list',
    method: 'get',
    params: query
  })
}

// 查询协议详细
export function getProtocol(protocolId) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'get'
  })
}

// 新增协议
export function addProtocol(data) {
  return request({
    url: '/system/protocol',
    method: 'post',
    data: data
  })
}

// 修改协议
export function updateProtocol(data) {
  return request({
    url: '/system/protocol',
    method: 'put',
    data: data
  })
}

// 删除协议
export function delProtocol(protocolId) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'delete'
  })
}

// 固化/解除固化协议
export function lockProtocol(data) {
  return request({
    url: '/system/protocol/lock',
    method: 'put',
    data: data
  })
}

// 导出协议
export function exportProtocol(query) {
  return request({
    url: '/system/protocol/export',
    method: 'get',
    params: query
  })
}
