export type JobRecord = Omit<JobModel, 'jobId'> & { jobId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type { EditJobModel, JobModel, JobPageQueryModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询定时任务调度列表
export function listJob(query?: JobPageQueryModel) {
  return request<HttpOffsetPage<JobRecord>>({
    url: '/monitor/job/list',
    method: 'get',
    params: query,
  });
}

// 查询定时任务调度详细
export function getJob(jobId: number | string) {
  return request<JobRecord>({
    url: '/monitor/job/' + jobId,
    method: 'get',
  });
}

// 新增定时任务调度
export function addJob(data: JobModel) {
  return request<JobRecord>({
    url: '/monitor/job',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'monitor.job.create' },
  });
}

// 修改定时任务调度
export function updateJob(data: EditJobModel) {
  return request<JobRecord>({
    url: '/monitor/job',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'monitor.job.update' },
  });
}

// 删除定时任务调度
export function delJob(jobId: number | string) {
  return request<null>({
    url: '/monitor/job/' + jobId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.job.delete' },
  });
}

// 任务状态修改
export function changeJobStatus(jobId: number | string, status: string) {
  const data = {
    jobId,
    status,
  };
  return request<JobRecord>({
    url: '/monitor/job/changeStatus',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'monitor.job.change-status' },
  });
}

// 定时任务立即执行一次
export function runJob(jobId: number | string, jobGroup: string) {
  const data = {
    jobId,
    jobGroup,
  };
  return request<{ jobId: number; jobGroup: string; status: 'accepted' }>({
    url: '/monitor/job/run',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'monitor.job.run' },
  });
}
