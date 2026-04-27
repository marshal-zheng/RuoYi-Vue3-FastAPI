import request from '@/utils/request';

// 查询操作日志列表
export function list(query?: Record<string, any>) {
  return request({
    url: '/monitor/operlog/list',
    method: 'get',
    params: query,
  });
}

// 删除操作日志
export function delOperlog(operId: number | string) {
  return request({
    url: '/monitor/operlog/' + operId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.operlog.delete' },
  });
}

// 清空操作日志
export function cleanOperlog() {
  return request({
    url: '/monitor/operlog/clean',
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.operlog.clear' },
  });
}
