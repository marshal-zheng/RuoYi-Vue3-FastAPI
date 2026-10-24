import request from '@/utils/request';
import type { HttpCollection } from '@/types/http-contract';

interface CacheInfo {
  cacheName: string;
  cacheKey: string;
  cacheValue: string;
  remark?: string;
}

// 查询缓存详细
export function getCache() {
  return request({
    url: '/monitor/cache',
    method: 'get',
  });
}

// 查询缓存名称列表
export function listCacheName() {
  return request<HttpCollection<CacheInfo>>({
    url: '/monitor/cache/getNames',
    method: 'get',
  });
}

// 查询缓存键名列表
export function listCacheKey(cacheName: string) {
  return request<HttpCollection<string>>({
    url: '/monitor/cache/getKeys/' + cacheName,
    method: 'get',
  });
}

// 查询缓存内容
export function getCacheValue(cacheName: string, cacheKey: string) {
  return request<CacheInfo>({
    url: '/monitor/cache/getValue/' + cacheName + '/' + cacheKey,
    method: 'get',
  });
}

// 清理指定名称缓存
export function clearCacheName(cacheName: string) {
  return request({
    url: '/monitor/cache/clearCacheName/' + cacheName,
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.cache.clear' },
  });
}

// 清理指定键名缓存
export function clearCacheKey(cacheName: string, cacheKey: string) {
  return request({
    url: '/monitor/cache/clearCacheKey/' + encodeURIComponent(`${cacheName}:${cacheKey}`),
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.cache.clear' },
  });
}

// 清理全部缓存
export function clearCacheAll() {
  return request({
    url: '/monitor/cache/clearCacheAll',
    method: 'delete',
    feedback: { mode: 'auto', key: 'monitor.cache.clear' },
  });
}
