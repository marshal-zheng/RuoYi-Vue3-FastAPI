/** Flatten the GridList logical input into the existing RuoYi wire contract. */
export function normalizeGridParams(params: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = { ...params };
  const query = result.query;
  if (query && typeof query === 'object' && !Array.isArray(query)) Object.assign(result, query);
  delete result.query;
  const pager = result.pager as { page?: unknown; size?: unknown } | undefined;
  if (pager && typeof pager === 'object') {
    if (pager.page !== null && pager.page !== undefined) result.page = pager.page;
    if (pager.size !== null && pager.size !== undefined) result.pageSize = pager.size;
  }
  delete result.pager;
  if (Object.prototype.hasOwnProperty.call(params, 'sort')) {
    delete result.orderByColumn;
    delete result.isAsc;
    const first = Array.isArray(params.sort) ? params.sort[0] : undefined;
    if (first && typeof first.field === 'string' && ['asc', 'desc'].includes(first.order)) {
      result.orderByColumn = first.field;
      result.isAsc = first.order;
    }
  }
  delete result.sort;
  return result;
}
