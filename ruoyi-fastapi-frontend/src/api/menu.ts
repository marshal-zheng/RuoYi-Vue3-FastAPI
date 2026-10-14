import request from '@/utils/request';
import type { HttpCollection } from '@/types/http-contract';
import type { RouteMeta } from 'vue-router';

export interface BackendRoute {
  path: string;
  name?: string;
  component?: string;
  redirect?: string;
  hidden?: boolean;
  alwaysShow?: boolean;
  query?: string;
  permissions?: string[];
  roles?: string[];
  meta?: RouteMeta;
  children?: BackendRoute[];
}

// 获取路由
export const getRouters = () => {
  return request<HttpCollection<BackendRoute>>({
    url: '/getRouters',
    method: 'get',
    feedback: { mode: 'silent' },
  });
};
