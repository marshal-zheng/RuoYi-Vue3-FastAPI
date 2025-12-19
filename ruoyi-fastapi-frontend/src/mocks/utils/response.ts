// @ts-nocheck
export type Recordable<T = any> = Record<string, T>

export interface ResultOptions {
  msg?: string
}

export interface ErrorOptions<T = null> {
  code?: number
  data?: T
}

export function resultSuccess<T = Recordable>(
  data: T,
  { msg = '操作成功' }: ResultOptions = {}
) {
  return {
    code: 200,
    data,
    msg,
    type: 'success'
  }
}

export function resultError<T = null>(
  msg = '请求失败',
  { code = 500, data = null as T }: ErrorOptions<T> = {}
) {
  return {
    code,
    data,
    msg,
    type: 'error'
  }
}

export function resultPageSuccess<T = any>(
  page: number,
  pageSize: number,
  list: T[],
  { msg = '操作成功' }: ResultOptions = {}
) {
  const pageData = pagination(page, pageSize, list)
  return {
    ...resultSuccess({
      records: pageData,
      total: list.length,
      size: pageSize,
      current: page,
      pages: Math.ceil(list.length / pageSize)
    }),
    msg
  }
}

export function pagination<T = any>(
  pageNo: number,
  pageSize: number,
  array: T[]
): T[] {
  const offset = (pageNo - 1) * Number(pageSize)
  const size = Number(pageSize)
  return offset + size >= array.length
    ? array.slice(offset, array.length)
    : array.slice(offset, offset + size)
}
