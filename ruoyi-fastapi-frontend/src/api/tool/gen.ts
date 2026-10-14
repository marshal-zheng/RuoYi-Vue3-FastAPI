export interface GenTableDetail {
  info: GenTableModel;
  columns: GenTableColumnModel[];
  tables: GenTableModel[];
}
import type { HttpOffsetPage } from '@/types/http-contract';
import type {
  EditGenTableModel,
  GenTableColumnModel,
  GenTableModel,
  GetGenDbTableListToolGenDbListGetData,
  GetGenTableListToolGenListGetData,
} from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询生成表数据
export function listTable(query?: NonNullable<GetGenTableListToolGenListGetData['query']>) {
  return request<HttpOffsetPage<GenTableModel>>({
    url: '/tool/gen/list',
    method: 'get',
    params: query,
  });
}

// 查询db数据库列表
export function listDbTable(query?: NonNullable<GetGenDbTableListToolGenDbListGetData['query']>) {
  return request<HttpOffsetPage<GenTableModel>>({
    url: '/tool/gen/db/list',
    method: 'get',
    params: query,
  });
}

// 查询表详细信息
export function getGenTable(tableId: number | string) {
  return request<GenTableDetail>({
    url: '/tool/gen/' + tableId,
    method: 'get',
  });
}

// 修改代码生成信息
export function updateGenTable(data: EditGenTableModel) {
  return request<GenTableDetail>({
    url: '/tool/gen',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'tool.gen.update' },
  });
}

// 导入表
export function importTable(data: { tables: string }) {
  return request<{ tableNames: string[]; importedCount: number }>({
    url: '/tool/gen/importTable',
    method: 'post',
    params: data,
    feedback: { mode: 'auto', key: 'tool.gen.import-table' },
  });
}

// 创建表
export function createTable(data: { sql: string }) {
  return request<{ tableNames: string[]; createdCount: number }>({
    url: '/tool/gen/createTable',
    method: 'post',
    params: data,
    feedback: { mode: 'auto', key: 'tool.gen.create-table' },
  });
}

// 预览生成代码
export function previewTable(tableId: number | string) {
  return request<Record<string, string>>({
    url: '/tool/gen/preview/' + tableId,
    method: 'get',
  });
}

// 删除表数据
export function delTable(tableId: number | string) {
  return request<null>({
    url: '/tool/gen/' + tableId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'tool.gen.delete' },
  });
}

// 生成代码（自定义路径）
export function genCode(tableName: string) {
  return request<{ tableName: string; status: 'generated' }>({
    url: '/tool/gen/genCode/' + tableName,
    method: 'get',
    feedback: { mode: 'silent' },
  });
}

// 同步数据库
export function synchDb(tableName: string) {
  return request<GenTableDetail | { tableName: string; status: 'synced' }>({
    url: '/tool/gen/synchDb/' + tableName,
    method: 'get',
    feedback: { mode: 'auto', key: 'tool.gen.sync-db' },
  });
}
