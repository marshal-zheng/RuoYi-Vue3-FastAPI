import { assetIdOfContentUrl, getFileAssetMetadata } from '@/api/fileAssets';
import { queryScope, scopeRequestOptions } from '@/queries/context';

/**
 * `<img>` cannot carry the Bearer header and only reports "error". A failed asset image asks the
 * metadata API through the session transport instead: an expired session is refreshed once by the
 * existing single-flight refresh, and only a still-visible asset is reloaded, at most once.
 * 403/404/503 and storage errors end the attempt, so nothing loops.
 */
const inflight = new Map<string, Promise<boolean>>();

export function recoverAsset(assetId: string): Promise<boolean> {
  const scope = queryScope.value;
  if (!scope) return Promise.resolve(false);
  const key = `${scope.key}:${assetId}`;
  const existing = inflight.get(key);
  if (existing) return existing;
  const attempt = getFileAssetMetadata([assetId], undefined, scopeRequestOptions(scope))
    .then(
      (result) =>
        queryScope.value === scope && result.items.some((item) => item.assetId === assetId)
    )
    .catch(() => false)
    .finally(() => inflight.delete(key));
  inflight.set(key, attempt);
  return attempt;
}

const RETRIED = 'assetRetried';

/** Reload a broken asset image once when the metadata check confirms it is still readable. */
export async function retryAssetImage(image: HTMLImageElement): Promise<boolean> {
  const src = image.getAttribute('src') || '';
  const assetId = assetIdOfContentUrl(src);
  if (!assetId || image.dataset[RETRIED]) return false;
  image.dataset[RETRIED] = '1';
  if (!(await recoverAsset(assetId))) return false;
  // Setting src (even to the same value) re-runs the image fetch with the renewed cookie.
  image.setAttribute('src', src);
  return true;
}

/** Delegated recovery for every asset image inside a container (e.g. rich text). */
export function installAssetImageRecovery(root: HTMLElement): () => void {
  const onError = (event: Event) => {
    const target = event.target;
    if (target instanceof HTMLImageElement) void retryAssetImage(target);
  };
  root.addEventListener('error', onError, true);
  return () => root.removeEventListener('error', onError, true);
}
