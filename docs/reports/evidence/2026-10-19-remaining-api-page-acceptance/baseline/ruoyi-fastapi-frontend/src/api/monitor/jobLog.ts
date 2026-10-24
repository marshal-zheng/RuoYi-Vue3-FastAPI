import type { HttpOffsetPage } from '@/types/http-contract';
import type { JobLogPageQueryModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询调度日志列表
export function listJobLog(query?: JobLogPageQueryModel) {
  return request<HttpOffsetPage<JobLogPageQueryModel>>({
    url: '/monitor/jobLog/list',
    method: 'get',
    params: query,
  });
}

// 删除调度日志
export function delJobLog(jobLogId: number | string) {
  return request<null>({
    url: '/monitor/jobLog/' + jobLogId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.job.delete' },
  });
}

// 清空调度日志
export function cleanJobLog() {
  return request<null>({
    url: '/monitor/jobLog/clean',
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.job-log.clear' },
  });
}
