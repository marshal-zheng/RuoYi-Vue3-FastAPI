import request from '@/utils/request';

export function listDataSource(query?: Record<string, any>) {
  return request({
    url: '/datasource/list',
    method: 'get',
    params: query,
  });
}

export function getDataSource(id: number | string) {
  return request({
    url: '/datasource/' + id,
    method: 'get',
  });
}

export function addDataSource(data: Record<string, any>) {
  return request({
    url: '/datasource',
    method: 'post',
    data: data,
  });
}

export function updateDataSource(data: Record<string, any>) {
  return request({
    url: '/datasource',
    method: 'put',
    data: data,
  });
}

export function delDataSource(ids: number | string) {
  return request({
    url: '/datasource/' + ids,
    method: 'delete',
  });
}

export function testDataSourceConnection(data: Record<string, any>) {
  return request({
    url: '/datasource/test-connection',
    method: 'post',
    data: data,
  });
}

export function testSavedDataSource(id: number | string) {
  return request({
    url: '/datasource/' + id + '/test',
    method: 'post',
  });
}
