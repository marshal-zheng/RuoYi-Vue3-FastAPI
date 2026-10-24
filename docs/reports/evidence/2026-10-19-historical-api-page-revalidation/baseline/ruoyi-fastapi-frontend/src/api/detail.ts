import { isQueryRequest } from '@zxio/http';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';
import { isRecord } from '@/types/http-contract';
import { showMessage } from '@/utils/feedback/message';
import { observeFeedback } from '@/utils/feedback/channel';

/** A successful transport did not return the resource the caller requested. */
export class DetailIdentityError extends Error {
  constructor(
    readonly expectedId: number | string,
    readonly receivedId: unknown
  ) {
    super('详情数据与当前编辑目标不一致，请刷新后重试');
    this.name = 'DetailIdentityError';
  }
}

/** Only explicit single-resource reads use this contract; lists and creation options do not. */
export async function requestDetail<T>(
  config: ExtendedAxiosRequestConfig,
  field: string,
  id: number | string,
  select: (payload: T) => unknown = (payload) => payload
): Promise<T> {
  const payload = await request<T>({ feedback: { mode: 'auto' }, ...config });
  const detail = select(payload);
  const receivedId = isRecord(detail) ? detail[field] : undefined;
  const expectedId = typeof id === 'string' && /^\d+$/.test(id) ? Number(id) : id;
  if (
    typeof receivedId === 'number' &&
    Number.isSafeInteger(receivedId) &&
    receivedId > 0 &&
    receivedId === expectedId
  ) {
    return payload;
  }
  const failure = new DetailIdentityError(id, receivedId);
  if (!config.silentError && !isQueryRequest(config.requestOptions)) {
    observeFeedback(() => showMessage({ type: 'error', message: failure.message }));
  }
  throw failure;
}
