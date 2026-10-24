import { http, HttpResponse } from 'msw';

import { createApiPath } from '../constants';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import { pagination, resultSuccess } from '../utils/response';
import { withBackendFallback } from '../utils/with-backend-fallback';

export function createMonitorHandlers(strategy: MockStrategy): MockRuntimeHandler[] {
  return [
    // 服务器监控信息
    http.get(createApiPath('/monitor/server'), ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              cpu: {
                cpuNum: 8,
                total: 100,
                sys: 12.5,
                used: 25.3,
                wait: 0.5,
                free: 61.7,
              },
              mem: {
                total: 16.0,
                used: 8.5,
                free: 7.5,
                usage: 53.1,
              },
              jvm: {
                total: 512,
                max: 1024,
                free: 256,
                version: '17.0.1',
                home: '/usr/lib/jvm/java-17',
                name: 'Java HotSpot(TM) 64-Bit Server VM',
                startTime: '2024-01-01 08:00:00',
                runTime: '10天 5小时 30分钟',
                usage: 50.0,
              },
              sys: {
                computerName: 'mock-server',
                computerIp: '192.168.1.100',
                userDir: '/home/app',
                osName: 'Linux',
                osArch: 'amd64',
              },
              sysFiles: [
                {
                  dirName: '/',
                  sysTypeName: 'ext4',
                  typeName: '本地磁盘',
                  total: '500 GB',
                  free: '300 GB',
                  used: '200 GB',
                  usage: 40.0,
                },
              ],
            })
          ),
        { strategy, tag: 'monitor:server' }
      )
    ),

    // 缓存监控信息
    http.get(createApiPath('/monitor/cache'), ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              info: {
                redis_version: '7.0.0',
                redis_mode: 'standalone',
                tcp_port: 6379,
                connected_clients: 10,
                uptime_in_days: 30,
                used_memory_human: '128.5M',
                used_memory_peak_human: '256M',
                maxmemory_human: '512M',
                aof_enabled: '0',
                rdb_last_bgsave_status: 'ok',
              },
              dbSize: 1024,
              commandStats: [
                { name: 'get', value: 50000 },
                { name: 'set', value: 30000 },
                { name: 'del', value: 5000 },
                { name: 'keys', value: 1000 },
              ],
            })
          ),
        { strategy, tag: 'monitor:cache' }
      )
    ),

    // 在线用户列表
    http.get(createApiPath('/monitor/online/list'), ({ request }) =>
      withBackendFallback(
        request,
        () => {
          const searchParams = new URL(request.url).searchParams;
          const page = Number(searchParams.get('page') ?? 1);
          const pageSize = Number(searchParams.get('pageSize') ?? 10);
          const items = pagination(page, pageSize, [
            {
              tokenId: 'mock-token-001',
              userName: 'admin',
              ipaddr: '192.168.1.1',
              loginLocation: '内网IP',
              browser: 'Chrome 120',
              os: 'Windows 10',
              loginTime: new Date().toISOString(),
            },
            {
              tokenId: 'mock-token-002',
              userName: 'test',
              ipaddr: '192.168.1.2',
              loginLocation: '内网IP',
              browser: 'Firefox 121',
              os: 'macOS',
              loginTime: new Date(Date.now() - 3600000).toISOString(),
            },
          ]);
          return HttpResponse.json(
            resultSuccess({
              items,
              total: 2,
              page,
              pageSize,
            })
          );
        },
        { strategy, tag: 'monitor:online' }
      )
    ),
  ];
}
