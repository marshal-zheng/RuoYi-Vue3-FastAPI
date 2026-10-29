import { AbortError } from '@zxio/http';
import type { FieldUpload } from '@zxio/schema-form/fields';
import { useAuthenticatedUpload, type UploadContext } from './useAuthenticatedUpload';

/**
 * Schema fields own File handles and pending state; the host owns the registered
 * purpose, session authentication and durable asset DTO. Removing a field value
 * removes its reference only. Never-bound drafts expire through server cleanup.
 * Use only a purpose registered for the generic upload endpoint (e.g. notice.image).
 */
export function useSchemaAttachmentUpload(context: UploadContext): FieldUpload {
  const transport = useAuthenticatedUpload(context);
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
    } finally {
      signal.removeEventListener('abort', abort);
    }
  };
}
