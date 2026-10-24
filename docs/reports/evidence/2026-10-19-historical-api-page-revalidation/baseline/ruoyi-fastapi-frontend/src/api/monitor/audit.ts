import type { HttpOffsetPage } from '@/types/http-contract';
import type { GetSystemAuditLogListMonitorAuditListGetData } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询审计日志列表
export function list(query?: NonNullable<GetSystemAuditLogListMonitorAuditListGetData['query']>) {
  return request<
    HttpOffsetPage<NonNullable<GetSystemAuditLogListMonitorAuditListGetData['query']>>
  >({
    url: '/monitor/audit/list',
    method: 'get',
    params: query,
  });
}

// 删除审计日志
export function delAuditLog(auditId: number | string) {
  return request<null>({
    url: '/monitor/audit/' + auditId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.audit.delete' },
  });
}

// 清空审计日志
export function cleanAuditLog() {
  return request<null>({
    url: '/monitor/audit/clean',
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.audit.clear' },
  });
}
