import { requestDetail } from '@/api/detail';
export type ProtocolRecord = Omit<ProtocolModel, 'protocolId'> & { protocolId: number };
import type { GetProtocolListSystemProtocolListGetData } from '@/api/_generated/types.gen';
export type ProtocolListQuery = NonNullable<GetProtocolListSystemProtocolListGetData['query']>;
export interface ProtocolImportPreview {
  protocolName?: string;
  protocolType: string;
  header: Record<string, unknown>;
  fields: Record<string, unknown>[];
}

import type { HttpOffsetPage, BatchResult } from '@/types/http-contract';
import type { ProtocolModel } from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询协议列表
export function listProtocol(query?: ProtocolListQuery) {
  return request<HttpOffsetPage<ProtocolRecord>>({
    url: '/system/protocol/list',
    method: 'get',
    params: query,
  });
}

// 查询协议详细
export function getProtocol(
  protocolId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError'>
) {
  return requestDetail<ProtocolRecord>(
    {
      ...config,
      url: '/system/protocol/' + protocolId,
      method: 'get',
    },
    'protocolId',
    protocolId
  );
}

// 新增协议
export function addProtocol(data: ProtocolModel) {
  return request<ProtocolRecord>({
    url: '/system/protocol',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'protocol.protocol.create' },
  });
}

// 修改协议
export function updateProtocol(data: ProtocolModel) {
  return request<ProtocolRecord>({
    url: '/system/protocol',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'protocol.protocol.update' },
  });
}

// 删除协议
export function delProtocol(protocolId: number | string) {
  return request<null>({
    url: '/system/protocol/' + protocolId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'protocol.protocol.delete' },
  });
}

// 批量删除协议
export function delProtocolBatch(protocolIds: (number | string)[]) {
  return request<BatchResult>({
    url: '/system/protocol/deleteBatch',
    method: 'post',
    data: { protocolIds },
    feedback: { mode: 'auto', key: 'protocol.protocol.delete-batch' },
  });
}

// 导出协议
export function exportProtocol(data: { protocolId: number }) {
  return request<Blob>({
    url: '/system/protocol/export',
    method: 'post',
    data: new URLSearchParams({ protocolId: String(data.protocolId) }),
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 下载协议导入模板
export function downloadProtocolImportTemplate(params?: { protocolType?: string }) {
  return request<Blob>({
    url: '/system/protocol/importTemplate',
    method: 'get',
    params,
    responseType: 'blob',
    feedback: { mode: 'silent' },
  });
}

// 协议导入预览
export function previewProtocolImport(data: FormData) {
  return request<ProtocolImportPreview>({
    url: '/system/protocol/importPreview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    feedback: { mode: 'silent' },
  });
}

// 导入协议配置（创建新协议）
export function importProtocol(formData: FormData) {
  return request<ProtocolRecord>({
    url: '/system/protocol/import',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    feedback: { mode: 'auto', key: 'protocol.protocol.import' },
  });
}

// 批量导入协议配置（单次请求携带多个文件）
export function importProtocolBatch(formData: FormData) {
  return request<BatchResult>({
    url: '/system/protocol/importBatch',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    feedback: { mode: 'auto', key: 'protocol.protocol.import-batch' },
  });
}
