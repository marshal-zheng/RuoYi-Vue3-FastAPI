import type { RequestOptions } from '@zxio/http';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

/** Stable, same-origin asset description; `contentUrl` is persisted and authorized on every use. */
export interface AssetDescriptor {
  assetId: string;
  name: string;
  mediaType: string;
  size: number;
  contentUrl: string;
}

export interface AssetMetadataBatch {
  items: AssetDescriptor[];
  unavailableIds: string[];
}

const CONTENT_PATH =
  /^\/file-assets\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/content$/;

/** Content addresses never carry the API base prefix, an origin or a storage host. */
export const assetContentUrl = (assetId: string): string => `/file-assets/${assetId}/content`;

export const assetIdOfContentUrl = (url: string | null | undefined): string | undefined =>
  url ? CONTENT_PATH.exec(url)?.[1] : undefined;

export const assetDownloadUrl = (assetId: string): string =>
  `${assetContentUrl(assetId)}?download=true`;

type UploadConfig = Pick<ExtendedAxiosRequestConfig, 'signal' | 'onUploadProgress'>;

/** Upload one file as a READY draft; saving the business form binds it in the business transaction. */
export function uploadFileAsset(form: FormData, config: UploadConfig, options?: RequestOptions) {
  return request<AssetDescriptor>(
    {
      ...config,
      url: '/file-assets/uploads',
      method: 'post',
      data: form,
      // Uploads are bounded by the server; no client-side request timeout.
      timeout: 0,
      silentSuccess: true,
      feedback: { mode: 'auto' },
    },
    options
  );
}

export function getFileAssetMetadata(
  assetIds: string[],
  config?: Pick<ExtendedAxiosRequestConfig, 'signal'>,
  options?: RequestOptions
) {
  return request<AssetMetadataBatch>(
    {
      ...config,
      url: '/file-assets/metadata:batch',
      method: 'post',
      data: { assetIds },
      silentSuccess: true,
      feedback: { mode: 'silent' },
    },
    options
  );
}

/** Best-effort discard of the caller's own never-bound draft; repeatable, bound assets answer 409. */
export function discardFileAsset(assetId: string, options?: RequestOptions) {
  return request<null>(
    {
      url: `/file-assets/${assetId}`,
      method: 'delete',
      silentSuccess: true,
      silentError: true,
      feedback: { mode: 'silent' },
    },
    options
  );
}
