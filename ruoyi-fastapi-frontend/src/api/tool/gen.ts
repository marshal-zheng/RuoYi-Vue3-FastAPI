import request from '@/utils/request';

// 查询生成表数据
export function listTable(query?: Record<string, any>) {
  return request({
    url: '/tool/gen/list',
    method: 'get',
    params: query,
  });
}

// 查询db数据库列表
export function listDbTable(query?: Record<string, any>) {
  return request({
    url: '/tool/gen/db/list',
    method: 'get',
    params: query,
  });
}

// 查询表详细信息
export function getGenTable(tableId: number | string) {
  return request({
    url: '/tool/gen/' + tableId,
    method: 'get',
  });
}

// 修改代码生成信息
export function updateGenTable(data: Record<string, any>) {
  return request({
    url: '/tool/gen',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'tool.gen.update' },
  });
}

// 导入表
export function importTable(data: Record<string, any>) {
  return request({
    url: '/tool/gen/importTable',
    method: 'post',
    params: data,
    feedback: { mode: 'auto', key: 'tool.gen.import-table' },
  });
}

// 创建表
export function createTable(data: Record<string, any>) {
  return request({
    url: '/tool/gen/createTable',
    method: 'post',
    params: data,
    feedback: { mode: 'auto', key: 'tool.gen.create-table' },
  });
}

// 预览生成代码
export function previewTable(tableId: number | string) {
  return request({
    url: '/tool/gen/preview/' + tableId,
    method: 'get',
  });
}

// 删除表数据
export function delTable(tableId: number | string) {
  return request({
    url: '/tool/gen/' + tableId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'tool.gen.delete' },
  });
}

// 生成代码（自定义路径）
export function genCode(tableName: string) {
  return request({
    url: '/tool/gen/genCode/' + tableName,
    method: 'get',
    feedback: { mode: 'silent' },
  });
}

// 同步数据库
export function synchDb(tableName: string) {
  return request({
    url: '/tool/gen/synchDb/' + tableName,
    method: 'get',
    feedback: { mode: 'auto', key: 'tool.gen.sync-db' },
  });
}
