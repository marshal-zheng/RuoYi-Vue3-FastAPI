import type { HttpOffsetPage } from '@/types/http-contract';
import type { LoginLogPageQueryModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询登录日志列表
export function list(query?: LoginLogPageQueryModel) {
  return request<HttpOffsetPage<LoginLogPageQueryModel>>({
    url: '/monitor/logininfor/list',
    method: 'get',
    params: query,
  });
}

// 删除登录日志
export function delLogininfor(infoId: number | string) {
  return request<null>({
    url: '/monitor/logininfor/' + infoId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.logininfor.clear' },
  });
}

// 解锁用户登录状态
export function unlockLogininfor(userName: string) {
  return request<null>({
    url: '/monitor/logininfor/unlock/' + userName,
    method: 'get',
    feedback: { mode: 'auto', key: 'monitor.logininfor.unlock' },
  });
}

// 清空登录日志
export function cleanLogininfor() {
  return request<null>({
    url: '/monitor/logininfor/clean',
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.logininfor.clear' },
  });
}
