import { AbortError, isAbortError, type HttpError } from '@zxio/http';
import { FieldUploadError, type FieldUpload } from '@zxio/schema-form/fields';
import { useAuthenticatedUpload, type UploadContext } from './useAuthenticatedUpload';
import { presentRequestError } from '@/utils/http';
import type { ProblemDetails } from '@/types/http-contract';

/**
 * A business rejection (4xx with an error code, e.g. type, size or quota) carries a
 * user-facing problem detail. Transport, server and session failures stay generic.
 */
function fieldUploadError(error: unknown): FieldUploadError | undefined {
  const problem = (error as { problem?: ProblemDetails } | null)?.problem;
  if (!problem || problem.errorCode === undefined) return undefined;
  if (problem.status < 400 || problem.status >= 500 || problem.status === 401) return undefined;
  const reason = problem.detail || problem.title;
  return reason ? new FieldUploadError(reason, { cause: error }) : undefined;
}

/**
 * Schema fields own File handles and pending state; the host owns the registered
 * purpose, session authentication and durable asset DTO. Removing a field value
 * removes its reference only. Never-bound drafts expire through server cleanup.
 * Use only a purpose registered for the generic upload endpoint (e.g. notice.image).
 * A business rejection appears only as the field's failure reason. Server and
 * transport failures keep the global message with its tracking ID, while the field
 * shows its generic text; cancellations stay silent.
 */
export function useSchemaAttachmentUpload(context: UploadContext): FieldUpload {
  const transport = useAuthenticatedUpload({ ...context, feedback: { mode: 'silent' } });
  let sequence = 0;
  return async (file, { signal }) => {
    if (signal.aborted) throw new AbortError({ message: 'Upload cancelled' });
    const uid = ++sequence;
    const abort = () => transport.abort({ uid });
    signal.addEventListener('abort', abort, { once: true });
    try {
      const asset = await transport.upload(file, uid);
      if (signal.aborted) throw new AbortError({ message: 'Upload cancelled' });
      return {
        id: asset.assetId,
        name: asset.name,
        url: asset.contentUrl,
        metadata: { mediaType: asset.mediaType, size: asset.size },
      };
    } catch (error) {
      const rejection = fieldUploadError(error);
      if (rejection) throw rejection;
      if (!isAbortError(error))
        presentRequestError(error as HttpError, { silentError: false, feedback: { mode: 'auto' } });
      throw error;
    } finally {
      signal.removeEventListener('abort', abort);
    }
  };
}
