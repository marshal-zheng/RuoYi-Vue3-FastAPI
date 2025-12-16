import request from '@/utils/request';

// 查询协议列表
export function listProtocol(query) {
  return request({
    url: '/system/protocol/list',
    method: 'get',
    params: query,
  });
}

// 查询协议详细
export function getProtocol(protocolId) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'get',
  });
}

// 新增协议
export function addProtocol(data) {
  return request({
    url: '/system/protocol',
    method: 'post',
    data: data,
  });
}

// 修改协议
export function updateProtocol(data) {
  return request({
    url: '/system/protocol',
    method: 'put',
    data: data,
  });
}

// 删除协议
export function delProtocol(protocolId) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'delete',
  });
}

// 批量删除协议
export function delProtocolBatch(protocolIds) {
  return request({
    url: '/system/protocol/deleteBatch',
    method: 'post',
    data: { protocolIds },
  });
}

// 已移除固化接口

// 导出协议
export function exportProtocol(query) {
  return request({
    url: '/system/protocol/export',
    method: 'get',
    params: query,
  });
}

// 下载协议导入模板
export function downloadProtocolImportTemplate(params) {
  return request({
    url: '/system/protocol/importTemplate',
    method: 'get',
    params,
    responseType: 'blob',
  });
}

// 协议导入预览
export function previewProtocolImport(data) {
  return request({
    url: '/system/protocol/importPreview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

// 导入协议配置（创建新协议）
export function importProtocol(formData) {
  return request({
    url: '/system/protocol/import',
    method: 'post',
    data: formData,
    // 批量导入需要连续发起多次请求，关闭全局防重复提交校验避免被拦截
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false },
  });
}

// 批量导入协议配置（单次请求携带多个文件）
export function importProtocolBatch(formData) {
  return request({
    url: '/system/protocol/importBatch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false },
  });
}
