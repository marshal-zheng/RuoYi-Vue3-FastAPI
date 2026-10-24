import type { HttpCollection } from '@/types/http-contract';
import type { GetMonitorOnlineListMonitorOnlineListGetData } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询在线用户列表
export function list(query?: NonNullable<GetMonitorOnlineListMonitorOnlineListGetData['query']>) {
  return request<
    HttpCollection<NonNullable<GetMonitorOnlineListMonitorOnlineListGetData['query']>>
  >({
    url: '/monitor/online/list',
    method: 'get',
    params: query,
  });
}

// 强退用户
export function forceLogout(tokenId: string) {
  return request<null>({
    url: '/monitor/online/' + tokenId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.online.force-logout' },
  });
}
