import { saveAs } from 'file-saver';
import type { AxiosResponse } from 'axios';
import { DownloadOptions } from './types';

export function extractFilenameFromHeaders(
  headers: Headers | Record<string, string>
): string | null {
  const raw =
    headers instanceof Headers
      ? headers.get('content-disposition')
      : headers['content-disposition'];
  if (!raw) return null;
  const match = /filename\\*?=([^;]+)/i.exec(raw);
  if (!match) return null;
  const value = match[1].trim();
  if (value.startsWith("UTF-8''")) {
    return decodeURIComponent(value.slice(7));
  }
  return value.replace(/^\"|\"$/g, '');
}

export async function downloadBlob(
  blob: Blob,
  filename: string,
  options?: DownloadOptions
): Promise<void> {
  const targetName = options?.filename || filename;
  const typedBlob = options?.contentType ? new Blob([blob], { type: options.contentType }) : blob;
  saveAs(typedBlob, targetName);
}

export async function downloadFromResponse(
  response: Response | AxiosResponse | Blob | ArrayBuffer,
  fallbackFilename: string,
  options?: DownloadOptions
): Promise<void> {
  const isAxios = (resp: any): resp is AxiosResponse => !!resp && typeof resp.data !== 'undefined';
  const isFetchResponse = (resp: any): resp is Response =>
    !!resp && typeof (resp as Response).blob === 'function';
  const isBlob = (resp: any): resp is Blob => typeof Blob !== 'undefined' && resp instanceof Blob;
  const isArrayBuffer = (resp: any): resp is ArrayBuffer =>
    typeof ArrayBuffer !== 'undefined' && resp instanceof ArrayBuffer;

  let blob: Blob;
  let headers: Headers | Record<string, string> | undefined;

  if (isAxios(response)) {
    blob = response.data as Blob;
    headers = response.headers as Record<string, string>;
  } else if (isFetchResponse(response)) {
    blob = await response.blob();
    headers = response.headers;
  } else if (isBlob(response)) {
    blob = response;
  } else if (isArrayBuffer(response)) {
    blob = new Blob([response]);
  } else {
    throw new TypeError('Unsupported response type for download');
  }

  const filename =
    extractFilenameFromHeaders(headers || {}) ||
    fallbackFilename ||
    options?.filename ||
    'download';
  const headerContentType = isAxios(response)
    ? response.headers?.['content-type']
    : isFetchResponse(response)
      ? response.headers.get('content-type')
      : null;
  const contentType = headerContentType || options?.contentType || blob.type;

  const wrappedBlob = contentType ? new Blob([blob], { type: contentType }) : blob;
  const finalName = filename;
  saveAs(wrappedBlob, finalName);
}
