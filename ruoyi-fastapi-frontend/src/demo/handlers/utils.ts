import { HttpResponse, type JsonBodyType } from 'msw';

import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthError } from '@/demo/services';

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function normalizeLegacyPageShape(payload: unknown): unknown {
  if (Array.isArray(payload)) {
    return payload.map((item) => normalizeLegacyPageShape(item));
  }

  if (!isRecord(payload)) {
    return payload;
  }

  const normalized: JsonRecord = {};

  Object.entries(payload).forEach(([key, value]) => {
    normalized[key] = normalizeLegacyPageShape(value);
  });

  return normalized;
}

function normalizeLegacySuccessPayload(payload: unknown): unknown {
  if (!isRecord(payload)) {
    return normalizeLegacyPageShape(payload);
  }

  const isLegacyEnvelope =
    payload.type === 'success' &&
    typeof payload.code === 'number' &&
    ('data' in payload || 'msg' in payload);

  if (isLegacyEnvelope) {
    if ('data' in payload) {
      return normalizeLegacyPageShape(payload.data);
    }

    const unwrapped = { ...payload };
    delete unwrapped.code;
    delete unwrapped.msg;
    delete unwrapped.type;
    return normalizeLegacyPageShape(unwrapped);
  }

  return normalizeLegacyPageShape(payload);
}

export function createDemoApiPath(config: RuntimeConfig, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${config.apiPrefix}${normalizedPath}`;
}

export function getDemoRequestToken(request: Request): string | undefined {
  const raw = request.headers.get('authorization');
  if (!raw) {
    return undefined;
  }

  return raw.replace(/^Bearer\s+/i, '');
}

export async function readDemoRequestBody<T extends object>(request: Request): Promise<T> {
  const contentType = request.headers.get('content-type')?.toLowerCase() ?? '';

  if (contentType.includes('application/json')) {
    try {
      return (await request.clone().json()) as T;
    } catch {
      // 交给后续兜底解析处理
    }
  }

  if (
    contentType.includes('application/x-www-form-urlencoded') ||
    contentType.includes('multipart/form-data')
  ) {
    try {
      const formData = await request.clone().formData();
      const entries = Array.from(formData.entries());

      if (entries.length > 0) {
        return Object.fromEntries(entries) as T;
      }
    } catch {
      // 某些运行时下 formData() 不可用时，继续尝试 text() 解析
    }
  }

  const text = await request.clone().text();

  if (!text.trim()) {
    return {} as T;
  }

  const trimmed = text.trim();

  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    return JSON.parse(trimmed) as T;
  }

  if (!trimmed.includes('=') && !trimmed.includes('&')) {
    return {} as T;
  }

  const params = new URLSearchParams(trimmed);
  return Object.fromEntries(params.entries()) as T;
}

export function demoJsonResponse(
  config: RuntimeConfig,
  handlerName: string,
  payload: JsonBodyType,
  status = 200
): Response {
  return HttpResponse.json(normalizeLegacySuccessPayload(payload) as JsonBodyType, {
    status,
    headers: {
      'X-Demo-Runtime': 'demo-offline',
      'X-Demo-Scenario': config.scenarioId,
      'X-Demo-Handler': handlerName,
    },
  });
}

export function demoErrorResponse(
  error: unknown,
  config: RuntimeConfig,
  logger: DemoRuntimeLogger,
  handlerName: string
): Response {
  const authError =
    error instanceof DemoAuthError ? error : new DemoAuthError('demo-offline 请求处理失败', 500);

  logger.warn('demo-offline handler 返回业务错误。', {
    handler: handlerName,
    status: authError.status,
    message: authError.message,
  });

  return demoJsonResponse(
    config,
    handlerName,
    {
      type: 'about:blank',
      title: authError.message,
      status: authError.status,
      detail: authError.message,
      instance: '',
      errorCode: authError.code,
    },
    authError.status
  );
}

export function demoFileResponse(
  config: RuntimeConfig,
  handlerName: string,
  payload: BodyInit | null,
  options: {
    contentType: string;
    filename: string;
    status?: number;
  }
): Response {
  const asciiFallback = options.filename.replace(/[^0-9A-Za-z._-]+/g, '_') || 'download';

  return new Response(payload, {
    status: options.status ?? 200,
    headers: {
      'Content-Type': options.contentType,
      'Content-Disposition': `attachment; filename=${asciiFallback}; filename*=UTF-8''${encodeURIComponent(
        options.filename
      )}`,
      'X-Demo-Runtime': 'demo-offline',
      'X-Demo-Scenario': config.scenarioId,
      'X-Demo-Handler': handlerName,
    },
  });
}
