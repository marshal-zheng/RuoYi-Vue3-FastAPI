import { requestDetail } from '@/api/detail';
export type PostRecord = Omit<PostModel, 'postId'> & { postId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type { PostModel, PostPageQueryModel } from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询岗位列表
export function listPost(query?: PostPageQueryModel) {
  return request<HttpOffsetPage<PostRecord>>({
    url: '/system/post/list',
    method: 'get',
    params: query,
  });
}

// 查询岗位详细
export function getPost(
  postId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError'>
) {
  return requestDetail<PostRecord>(
    {
      ...config,
      url: '/system/post/' + postId,
      method: 'get',
    },
    'postId',
    postId
  );
}

// 新增岗位
export function addPost(data: PostModel) {
  return request<PostRecord>({
    url: '/system/post',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.post.create' },
  });
}

// 修改岗位
export function updatePost(data: PostModel) {
  return request<PostRecord>({
    url: '/system/post',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.post.update' },
  });
}

// 删除岗位
export function delPost(postId: number | string) {
  return request<null>({
    url: '/system/post/' + postId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.post.delete' },
  });
}
