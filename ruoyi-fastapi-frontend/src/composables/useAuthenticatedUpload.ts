import { onScopeDispose, ref, watch } from 'vue';
import type { UploadFile, UploadProgressEvent, UploadRequestOptions } from 'element-plus';
import { AbortError } from '@zxio/http';
import request from '@/utils/request';
import { queryScope, requireQueryScope, scopeRequestOptions } from '@/queries/context';

export interface UploadedResource {
  fileName: string;
  originalFilename?: string;
  url?: string;
}

/** Element Plus owns success/error callbacks; this composable owns transport and cancellation. */
export function useAuthenticatedUpload() {
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

  const httpRequest = async (options: UploadRequestOptions): Promise<UploadedResource> => {
    const scope = requireQueryScope();
    const controller = new AbortController();
    const uid = options.file.uid;
    requests.set(uid, controller);
    pending.value = requests.size;
    const isCurrent = () => requests.get(uid) === controller && queryScope.value === scope;
    const data = new FormData();
    data.append(options.filename, options.file, options.file.name);
    try {
      const result = await request<UploadedResource>(
        {
          url: '/common/upload',
          method: 'post',
          data,
          signal: controller.signal,
          timeout: 0,
          silentSuccess: true,
          feedback: { mode: 'auto' },
          onUploadProgress(event) {
            if (!isCurrent() || controller.signal.aborted) return;
            const total = event.total || 0;
            const progress = new ProgressEvent('progress', {
              loaded: event.loaded,
              total,
              lengthComputable: total > 0,
            }) as UploadProgressEvent;
            progress.percent = total > 0 ? (event.loaded / total) * 100 : 0;
            options.onProgress(progress);
          },
        },
        scopeRequestOptions(scope)
      );
      if (!isCurrent() || controller.signal.aborted)
        throw new AbortError({ message: 'Upload cancelled' });
      return result;
    } finally {
      if (requests.get(uid) === controller) requests.delete(uid);
      pending.value = requests.size;
    }
  };

  watch(queryScope, () => abort(), { flush: 'sync' });
  onScopeDispose(() => abort());
  return { httpRequest, abort, pending };
}
