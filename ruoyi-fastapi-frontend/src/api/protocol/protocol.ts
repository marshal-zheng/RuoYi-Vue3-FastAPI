import request from '@/utils/request';

// 查询协议列表
export function listProtocol(query?: Record<string, any>) {
  return request({
    url: '/system/protocol/list',
    method: 'get',
    params: query,
  });
}

// 查询协议详细
export function getProtocol(protocolId: number | string) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'get',
  });
}

// 新增协议
export function addProtocol(data: Record<string, any>) {
  return request({
    url: '/system/protocol',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'protocol.protocol.create' },
  });
}

// 修改协议
export function updateProtocol(data: Record<string, any>) {
  return request({
    url: '/system/protocol',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'protocol.protocol.update' },
  });
}

// 删除协议
export function delProtocol(protocolId: number | string) {
  return request({
    url: '/system/protocol/' + protocolId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'protocol.protocol.delete' },
  });
}

// 批量删除协议
export function delProtocolBatch(protocolIds: (number | string)[]) {
  return request({
    url: '/system/protocol/deleteBatch',
    method: 'post',
    data: { protocolIds },
    feedback: { mode: 'auto', key: 'protocol.protocol.delete-batch' },
  });
}

// 导出协议
export function exportProtocol(query?: Record<string, any>) {
  return request({
    url: '/system/protocol/export',
    method: 'get',
    params: query,
    feedback: { mode: 'silent' },
  });
}

// 下载协议导入模板
export function downloadProtocolImportTemplate(params?: Record<string, any>) {
  return request({
    url: '/system/protocol/importTemplate',
    method: 'get',
    params,
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 协议导入预览
export function previewProtocolImport(data: FormData) {
  return request({
    url: '/system/protocol/importPreview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    feedback: { mode: 'silent' },
  });
}

// 导入协议配置（创建新协议）
export function importProtocol(formData: FormData) {
  return request({
    url: '/system/protocol/import',
    method: 'post',
    data: formData,
    // 批量导入需要连续发起多次请求，关闭全局防重复提交校验避免被拦截
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false },
    feedback: { mode: 'auto', key: 'protocol.protocol.import' },
  });
}

// 批量导入协议配置（单次请求携带多个文件）
export function importProtocolBatch(formData: FormData) {
  return request({
    url: '/system/protocol/importBatch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false },
    feedback: { mode: 'auto', key: 'protocol.protocol.import-batch' },
  });
}
