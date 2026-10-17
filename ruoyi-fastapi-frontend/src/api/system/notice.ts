import { requestDetail } from '@/api/detail';
import type { NoticeModel } from '@/api/_generated/types.gen';
// JSON represents the backend bytes field as UTF-8 text, rather than multipart File.
export type NoticePayload = Omit<NoticeModel, 'noticeContent'> & { noticeContent?: string | null };
export type NoticeRecord = Omit<NoticePayload, 'noticeId'> & { noticeId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type { GetSystemNoticeListSystemNoticeListGetData } from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询公告列表
export function listNotice(
  query?: NonNullable<GetSystemNoticeListSystemNoticeListGetData['query']>
) {
  return request<HttpOffsetPage<NoticeRecord>>({
    url: '/system/notice/list',
    method: 'get',
    params: query,
  });
}

// 查询公告详细
export function getNotice(
  noticeId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError'>
) {
  return requestDetail<NoticeRecord>(
    {
      ...config,
      url: '/system/notice/' + noticeId,
      method: 'get',
      feedback: { mode: 'auto' },
    },
    'noticeId',
    noticeId
  );
}

// 新增公告
export function addNotice(data: NoticePayload) {
  return request<NoticeRecord>({
    url: '/system/notice',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.notice.create' },
  });
}

// 修改公告
export function updateNotice(data: NoticePayload) {
  return request<NoticeRecord>({
    url: '/system/notice',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.notice.update' },
  });
}

// 删除公告
export function delNotice(noticeId: number | string) {
  return request<null>({
    url: '/system/notice/' + noticeId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.notice.delete' },
  });
}
