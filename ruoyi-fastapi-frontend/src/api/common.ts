import request from '@/utils/request';

/**
 * 获取数据库表名列表
 */
export function getTableNames() {
  return request({
    url: '/common/tables',
    method: 'get',
  });
}
