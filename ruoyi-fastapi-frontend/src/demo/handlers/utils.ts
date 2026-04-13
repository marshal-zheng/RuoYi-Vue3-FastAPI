import { HttpResponse, type JsonBodyType } from 'msw';

import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthError } from '@/demo/services';

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
  const text = await request.clone().text();

  if (!text.trim()) {
    return {} as T;
  }

  const trimmed = text.trim();

  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    return JSON.parse(trimmed) as T;
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
  return HttpResponse.json(payload, {
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
      code: authError.code,
      msg: authError.message,
      type: 'error',
      data: {
        reason: authError.name,
      },
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
