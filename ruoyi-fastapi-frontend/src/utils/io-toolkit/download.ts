import { saveAs } from 'file-saver';
import { HttpError, resolveHttpError } from '@zxio/http';
import type { AxiosResponse } from 'axios';
import { DownloadOptions } from './types';
import { isProblemDetails } from '@/types/http-contract';

export function extractFilenameFromHeaders(
  headers: Headers | Record<string, string>
): string | null {
  const raw =
    headers instanceof Headers
      ? headers.get('content-disposition')
      : headers['content-disposition'];
  if (!raw) return null;
  const encoded = /(?:^|;)\s*filename\*\s*=\s*([^;]+)/i.exec(raw);
  const extendedValue = encoded?.[1].trim().replace(/^"|"$/g, '');
  const utf8 = extendedValue && /^UTF-8'[^']*'(.*)$/i.exec(extendedValue);
  if (utf8) {
    try {
      return decodeURIComponent(utf8[1]);
    } catch {
      // A malformed extended name must not prevent downloading with its ASCII fallback.
    }
  }
  const match = /(?:^|;)\s*filename\s*=\s*("(?:[^"\\]|\\.)*"|[^;]+)/i.exec(raw);
  if (!match) return null;
  const value = match[1].trim();
  return value.replace(/^"|"$/g, '');
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
  response: Response | AxiosResponse<unknown> | Blob | ArrayBuffer,
  fallbackFilename: string,
  options?: DownloadOptions
): Promise<void> {
  const isBlob = (value: unknown): value is Blob =>
    typeof Blob !== 'undefined' && value instanceof Blob;
  const isArrayBuffer = (value: unknown): value is ArrayBuffer =>
    typeof ArrayBuffer !== 'undefined' && value instanceof ArrayBuffer;
  const isAxios = (value: unknown): value is AxiosResponse<Blob | ArrayBuffer> =>
    !!value &&
    typeof value === 'object' &&
    'data' in value &&
    (isBlob(value.data) || isArrayBuffer(value.data));
  const isFetchResponse = (value: unknown): value is Response =>
    typeof Response !== 'undefined' && value instanceof Response;

  let blob: Blob;
  let headers: Headers | Record<string, string> | undefined;

  if (isAxios(response)) {
    blob = isBlob(response.data) ? response.data : new Blob([response.data]);
    headers = Object.fromEntries(
      Object.entries(response.headers).filter(
        (entry): entry is [string, string] => typeof entry[1] === 'string'
      )
    );
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

  const serverFilename = extractFilenameFromHeaders(headers || {});
  const filename = serverFilename || fallbackFilename || options?.filename || 'download';
  const headerContentType = isAxios(response)
    ? response.headers?.['content-type']
    : isFetchResponse(response)
      ? response.headers.get('content-type')
      : null;
  const contentType =
    (typeof headerContentType === 'string' && headerContentType) ||
    options?.contentType ||
    blob.type;

  const status = isAxios(response) || isFetchResponse(response) ? response.status : 200;
  const failedStatus = status < 200 || status >= 300;
  const disposition =
    headers instanceof Headers
      ? headers.get('content-disposition')
      : headers?.['content-disposition'];
  const attachment = !!serverFilename || /^attachment(?:;|$)/i.test(disposition || '');
  const json = /^(?:application|text)\/(?:[^;]+\+)?json(?:;|$)/i.test(contentType || '');
  if (failedStatus || (!attachment && json)) {
    const originalBody = isAxios(response) ? response.data : blob;
    const failure = await resolveHttpError(
      new HttpError(
        {
          status,
          message: '下载文件出现错误，请联系管理员！',
          data: originalBody,
          raw: originalBody,
          ...(isFetchResponse(response) ? { cause: response } : {}),
        },
        isAxios(response) ? response : undefined,
        isAxios(response) ? response.config : undefined
      )
    );
    if (
      failedStatus ||
      /^application\/problem\+json(?:;|$)/i.test(contentType || '') ||
      (isProblemDetails(failure.data) && failure.data.status >= 400)
    ) {
      throw failure;
    }
  }

  const wrappedBlob = contentType ? new Blob([blob], { type: contentType }) : blob;
  const finalName = filename;
  saveAs(wrappedBlob, finalName);
}
