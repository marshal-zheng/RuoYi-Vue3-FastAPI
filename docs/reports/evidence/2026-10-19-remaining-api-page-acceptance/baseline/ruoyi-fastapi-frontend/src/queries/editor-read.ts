import { isCancelledError } from '@tanstack/vue-query';
import { AbortError } from '@zxio/http';
import { assertRequestScope, scopeRequestOptions, type QueryScope } from './context';

/** End one opening's wait without cancelling a native read shared by other subscribers. */
export async function readEditorResource<T>(
  scope: QueryScope,
  read: () => Promise<T>,
  openingSignal?: AbortSignal
): Promise<T> {
  const ended = () => new AbortError({ message: '编辑读取已结束' });
  if (openingSignal?.aborted) throw ended();
  let removeAbortListener: (() => void) | undefined;
  const openingEnded = openingSignal
    ? new Promise<never>((_, reject) => {
        const abort = () => reject(ended());
        openingSignal.addEventListener('abort', abort, { once: true });
        removeAbortListener = () => openingSignal.removeEventListener('abort', abort);
      })
    : undefined;
  try {
    while (true) {
      if (openingSignal?.aborted) throw ended();
      assertRequestScope(scopeRequestOptions(scope));
      try {
        const reading = read();
        return await (openingEnded ? Promise.race([reading, openingEnded]) : reading);
      } catch (error) {
        if (!isCancelledError(error)) throw error;
        // A successful write may cancel a snapshot. Rejoin only while this opening is current.
      }
    }
  } finally {
    removeAbortListener?.();
  }
}
