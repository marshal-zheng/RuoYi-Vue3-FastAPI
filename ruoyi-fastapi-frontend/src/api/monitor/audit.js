import request from '@/utils/request';

// 查询审计日志列表
export function list(query) {
  return request({
    url: '/monitor/audit/list',
    method: 'get',
    params: query,
  });
}

// 删除审计日志
export function delAuditLog(auditId) {
  return request({
    url: '/monitor/audit/' + auditId,
    method: 'delete',
  });
}

// 清空审计日志
export function cleanAuditLog() {
  return request({
    url: '/monitor/audit/clean',
    method: 'delete',
  });
}
