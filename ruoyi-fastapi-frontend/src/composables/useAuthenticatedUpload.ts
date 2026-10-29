import { onScopeDispose, ref, watch } from 'vue';
import type { UploadFile, UploadProgressEvent, UploadRequestOptions } from 'element-plus';
import { AbortError } from '@zxio/http';
import { uploadFileAsset, type AssetDescriptor } from '@/api/fileAssets';
import { queryScope, requireQueryScope, scopeRequestOptions } from '@/queries/context';
import type { FeedbackOptions } from '@/utils/feedback/types';

export interface UploadContext {
  /** Server-registered upload purpose, e.g. `notice.image`. */
  purpose: () => string;
  /** Business id when editing an existing owner; omitted while creating it. */
  ownerId?: () => string | number | null | undefined;
  /** Failure presentation; defaults to the global automatic feedback. */
  feedback?: FeedbackOptions;
}

/**
 * Element Plus owns success/error callbacks; this composable owns transport and cancellation.
 * The session transport retries only an explicit pre-write 401 once; network errors, timeouts,
 * 5xx and lost responses are never resent automatically.
 */
export function useAuthenticatedUpload(context: UploadContext) {
  const requests = new Map<number, AbortController>();
  const pending = ref(0);

  const abort = (file?: Pick<UploadFile, 'uid'>) => {
    for (const [uid, controller] of requests) {
      if (file && file.uid !== uid) continue;
      requests.delete(uid);
      controller.abort();
    }
    pending.value = requests.size;
  };

  const upload = async (
    file: File,
    uid: number,
    onProgress?: (event: UploadProgressEvent) => void
  ): Promise<AssetDescriptor> => {
    const scope = requireQueryScope();
    const controller = new AbortController();
    requests.set(uid, controller);
    pending.value = requests.size;
    const isCurrent = () => requests.get(uid) === controller && queryScope.value === scope;
    const data = new FormData();
    data.append('purpose', context.purpose());
    const ownerId = context.ownerId?.();
    if (ownerId !== undefined && ownerId !== null && ownerId !== '')
      data.append('ownerId', String(ownerId));
    data.append('file', file, file.name);
    try {
      const result = await uploadFileAsset(
        data,
        {
          signal: controller.signal,
          feedback: context.feedback,
          onUploadProgress(event) {
            if (!onProgress || !isCurrent() || controller.signal.aborted) return;
            const total = event.total || 0;
            const progress = new ProgressEvent('progress', {
              loaded: event.loaded,
              total,
              lengthComputable: total > 0,
            }) as UploadProgressEvent;
            progress.percent = total > 0 ? (event.loaded / total) * 100 : 0;
            onProgress(progress);
          },
        },
        scopeRequestOptions(scope)
      );
      // A response for another session or a cancelled row is never written back.
      if (!isCurrent() || controller.signal.aborted)
        throw new AbortError({ message: 'Upload cancelled' });
      return result;
    } finally {
      if (requests.get(uid) === controller) requests.delete(uid);
      pending.value = requests.size;
    }
  };

  const httpRequest = (options: UploadRequestOptions): Promise<AssetDescriptor> =>
    upload(options.file, options.file.uid, options.onProgress);

  watch(queryScope, () => abort(), { flush: 'sync' });
  onScopeDispose(() => abort());
  return { httpRequest, upload, abort, pending };
}
