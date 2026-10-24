import type {
  HttpClientConfig,
  HttpError,
  ResolvedRequestOptions,
  RequestOptions,
} from '@zxio/http';
import { AxiosHeaders, AxiosError, type AxiosResponse } from 'axios';
import type { ExtendedAxiosRequestConfig } from './request';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const createHttpClient = vi.fn((config: HttpClientConfig) => ({
  __config: config,
  request: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));
const createGridListPlugin = vi.fn(
  (config: Parameters<(typeof import('@zxio/http'))['createGridListPlugin']>[0]) => config
);
const presentSuccessFeedback = vi.fn();
const presentProblemFeedback = vi.fn();
const elMessageClose = vi.fn();
const ElMessage = Object.assign(
  vi.fn<(options: unknown) => { close: () => void }>(() => ({
    close: elMessageClose,
  })),
  {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    closeAll: vi.fn(),
  }
);

vi.mock('@zxio/http', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@zxio/http')>()),
  createHttpClient,
  createGridListPlugin,
}));

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: {
    alert: vi.fn(),
  },
}));

vi.mock('@/utils/feedback/message', () => ({
  showMessage: async (options: unknown) => ({
    ok: true,
    value: ElMessage(options),
  }),
}));

vi.mock('vue', async (importOriginal) => ({
  ...(await importOriginal<typeof import('vue')>()),
  h: vi.fn(() => 'mock-vnode'),
}));

vi.mock('@/utils/auth', () => ({
  getCsrfToken: vi.fn(() => 'csrf-token'),
  getToken: vi.fn(() => 'access-token'),
}));

vi.mock('@/plugins/cache', () => ({
  default: {
    session: {
      getJSON: vi.fn(() => null),
      setJSON: vi.fn(),
    },
  },
}));

vi.mock('@/router/history', () => ({
  isHashRouteMode: vi.fn(() => false),
}));

vi.mock('@/store/modules/user', () => ({
  default: vi.fn(() => ({
    logOut: vi.fn(() => Promise.resolve()),
  })),
}));

vi.mock('@/utils/feedback/presenter', () => ({
  presentSuccessFeedback,
  presentProblemFeedback,
  resolveFeedbackOptions: vi.fn((feedback) => ({
    mode: feedback?.mode ?? 'silent',
    key: feedback?.key,
    successContext: feedback?.successContext ?? {},
    validationTarget: feedback?.validationTarget,
  })),
}));

const expiredAuthError = {
  config: {
    method: 'get',
  },
  response: {
    status: 401,
    data: {
      type: 'about:blank',
      title: '登录状态已过期',
      status: 401,
      detail: '登录状态已过期，请重新登录',
      instance: '',
      errorCode: 20002,
    },
    headers: {},
  },
};

describe('http contract client', () => {
  it('leaves repeated writes to the business operation and never records a time fingerprint', async () => {
    const cache = (await import('@/plugins/cache')).default;
    const { http } = await import('@/utils/http');
    const config = createHttpClient.mock.calls[0][0];
    const beforeRequest = config.transforms?.[0]?.beforeRequest;
    const request = {
      url: '/system/config',
      method: 'post',
      data: { configKey: 'same' },
      headers: {},
    };
    if (!beforeRequest) throw new Error('Missing request transform');
    await beforeRequest({ ...request }, {} as ResolvedRequestOptions, {
      client: http,
      axiosInstance: http.axiosInstance,
      notifier: { notify: vi.fn() },
    });
    expect(cache.session.setJSON).not.toHaveBeenCalled();
  });

  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    window.history.pushState({}, '', '/index');
    createHttpClient.mockImplementation((config: HttpClientConfig) => ({
      __config: config,
      request: vi.fn(),
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }));
  });

  const loadModule = async () => {
    const { resolveHttpError } = await import('@zxio/http');
    const { http } = await import('@/utils/http');
    const config = createHttpClient.mock.calls[0][0];
    const grid = createGridListPlugin.mock.calls[0][0];
    const policy = config.transforms?.[1];
    const resolver = config.successResolver;
    const afterResponse = policy?.afterResponse;
    const onError = policy?.onError;
    if (!resolver || !afterResponse || !onError || !grid?.resolveList || !grid.resolveTotal) {
      throw new Error('The HTTP contract hooks were not configured');
    }
    const options: ResolvedRequestOptions = {
      joinParamsToUrl: false,
      joinTime: false,
      withToken: false,
      isTransformResponse: false,
      isReturnNativeResponse: false,
      successMessageMode: 'none',
      showSuccessMessage: false,
      errorMessageMode: 'none',
      showErrorMessage: false,
    };
    const context = {
      client: http,
      axiosInstance: http.axiosInstance,
      notifier: { notify: vi.fn() },
    };
    type ResponseFixture = Pick<AxiosResponse<unknown>, 'status' | 'data'> & {
      headers?: AxiosResponse['headers'];
      config?: ExtendedAxiosRequestConfig;
    };
    const responseOf = (response: ResponseFixture): AxiosResponse<unknown> =>
      Object.assign(response, {
        statusText: '',
        headers: response.headers ?? {},
        config: {
          ...response.config,
          headers: Object.assign(new AxiosHeaders(), response.config?.headers),
        },
      });
    type ErrorFixture = {
      config: ExtendedAxiosRequestConfig;
      response?: ResponseFixture;
    };
    return {
      rawOnError: async (error: unknown, overrides?: RequestOptions): Promise<never> => {
        await onError(await resolveHttpError(error), { ...options, ...overrides }, context);
        throw new Error('Expected the business error hook to reject');
      },
      clientConfig: {
        ...config,
        successResolver: ({ response }: { response: ResponseFixture }) =>
          resolver({ response: responseOf(response), options }),
        transforms: [
          {},
          {
            afterResponse: (response: ResponseFixture) =>
              afterResponse(responseOf(response), options, context),
            onError: async (fixture: ErrorFixture) => {
              const error: AxiosError = {
                name: 'AxiosError',
                message: 'request failed',
                isAxiosError: true,
                toJSON: () => ({}),
                config: {
                  ...fixture.config,
                  headers: Object.assign(new AxiosHeaders(), fixture.config.headers),
                },
                ...(fixture.response ? { response: responseOf(fixture.response) } : {}),
              };
              return onError(await resolveHttpError(error), options, context);
            },
          },
        ] as const,
      },
      gridConfig: {
        ...grid,
        resolveList: grid.resolveList,
        resolveTotal: grid.resolveTotal,
      },
    };
  };

  it.each([false, true])(
    'preserves preparation failure detail and request feedback context (silentError=%s)',
    async (silentError) => {
      const { rawOnError } = await loadModule();
      const { RequestPreparationError } = await import('@zxio/http');
      const original = Object.freeze(new Error('请求签名准备失败'));
      const config = {
        url: '/system/config',
        silentError,
        feedback: { mode: 'auto' as const, key: 'system.config.create' },
      };
      const failure = new RequestPreparationError(original, config);
      const result = await rawOnError(failure).catch((error) => error);
      expect(result).toBe(failure);
      expect(result.cause).toBe(original);
      expect(result.config).toBe(config);
      expect(result.message).toBe(original.message);
      expect(result.problem.detail).toBe(original.message);
      expect(presentProblemFeedback).toHaveBeenCalledTimes(silentError ? 0 : 1);
      if (!silentError) {
        expect(presentProblemFeedback).toHaveBeenCalledWith(
          expect.objectContaining({
            feedback: expect.objectContaining({ mode: 'auto', key: 'system.config.create' }),
          })
        );
      }
    }
  );

  it('keeps cancellation recognizable and suppresses all business failure feedback', async () => {
    const { rawOnError } = await loadModule();
    const original = new AxiosError('cancelled', 'ERR_CANCELED', {
      headers: new AxiosHeaders(),
    });
    await expect(rawOnError(original)).rejects.toMatchObject({
      name: 'AbortError',
      code: 'ERR_CANCELED',
      cause: original,
    });
    expect(presentProblemFeedback).not.toHaveBeenCalled();
    expect(ElMessage).not.toHaveBeenCalled();
  });

  it('adds business problem metadata while preserving the original failure context', async () => {
    const { rawOnError } = await loadModule();
    const config = { headers: new AxiosHeaders(), url: '/project/1' };
    const response: AxiosResponse = {
      config,
      status: 503,
      statusText: 'Unavailable',
      headers: { 'x-request-id': 'req-original' },
      data: {
        type: 'about:blank',
        title: '服务繁忙',
        status: 503,
        detail: '稍后重试',
        instance: '/project/1',
      },
    };
    const original = new AxiosError('HTTP 503', 'ERR_BAD_RESPONSE', config, undefined, response);
    await expect(rawOnError(original)).rejects.toMatchObject({
      name: 'ServerError',
      code: 'ERR_BAD_RESPONSE',
      cause: original,
      response,
      config,
      problem: response.data,
      meta: { requestId: 'req-original' },
    });
  });

  it('reads binary problem details without replacing the original response body', async () => {
    const { rawOnError } = await loadModule();
    const problem = {
      type: 'about:blank',
      title: '导出失败',
      status: 422,
      detail: '版本不存在',
      instance: '/export',
    };
    const body = new Blob([JSON.stringify(problem)], {
      type: 'application/problem+json',
    });
    const config = {
      headers: new AxiosHeaders(),
      url: '/export',
      responseType: 'blob' as const,
    };
    const response: AxiosResponse = {
      config,
      data: body,
      status: 422,
      statusText: 'Invalid',
      headers: { 'x-request-id': 'binary-problem' },
    };
    const original = new AxiosError('HTTP 422', 'ERR_BAD_REQUEST', config, undefined, response);
    await expect(rawOnError(original)).rejects.toMatchObject({
      cause: original,
      response,
      raw: body,
      data: problem,
      problem,
      message: '版本不存在',
      meta: { requestId: 'binary-problem' },
    });
    expect(response.data).toBe(body);
  });

  it.each(['text', 'message', 'msg'])('retains the decoded %s failure message', async (format) => {
    const { rawOnError } = await loadModule();
    const message = '导出服务暂不可用';
    const body = new Blob([format === 'text' ? message : JSON.stringify({ [format]: message })], {
      type: format === 'text' ? 'text/plain' : 'application/json',
    });
    const config = { headers: new AxiosHeaders(), url: '/export' };
    const response: AxiosResponse = {
      config,
      data: body,
      status: 503,
      statusText: 'Unavailable',
      headers: {},
    };
    const original = new AxiosError('HTTP 503', 'ERR_BAD_RESPONSE', config, undefined, response);
    await expect(rawOnError(original)).rejects.toMatchObject({
      message,
      problem: { detail: message },
      raw: body,
      response,
      cause: original,
    });
  });

  it('configures multi-status success handling and items-based grid paging', async () => {
    const { clientConfig, gridConfig } = await loadModule();

    expect(clientConfig.successCodes).toEqual([200, 201, 202, 204]);
    expect(gridConfig.pageField).toBe('page');
    expect(gridConfig.sizeField).toBe('pageSize');
    expect(gridConfig.totalField).toBe('total');
    expect(gridConfig.listField).toBe('items');
    expect(gridConfig.resolveList({ items: [{ id: 1 }] })).toEqual([{ id: 1 }]);
    expect(gridConfig.resolveTotal({ total: 3 })).toBe(3);
  });

  it('treats 201, 202 and 204 as successful contract responses', async () => {
    const { clientConfig } = await loadModule();

    expect(
      clientConfig.successResolver({
        response: { status: 201, data: { id: 1 } },
      })
    ).toEqual({
      ok: true,
      data: { id: 1 },
      code: 201,
      raw: { id: 1 },
    });
    expect(
      clientConfig.successResolver({
        response: { status: 202, data: { jobId: 1 } },
      })
    ).toEqual({
      ok: true,
      data: { jobId: 1 },
      code: 202,
      raw: { jobId: 1 },
    });
    expect(
      clientConfig.successResolver({
        response: { status: 204, data: undefined },
      })
    ).toEqual({
      ok: true,
      data: null,
      code: 204,
      raw: undefined,
    });
  });

  it('attaches response headers and offset pager metadata for auto mutation feedback', async () => {
    const { clientConfig } = await loadModule();
    const afterResponse = clientConfig.transforms[1].afterResponse;
    const payload: Record<string, unknown> = {
      items: [{ id: 1 }],
      total: 12,
      page: 2,
      pageSize: 20,
    };
    const response = {
      status: 201,
      data: payload,
      headers: {
        'x-request-id': 'req-1',
        'x-trace-id': 'trace-1',
        location: 'https://api.example.test/system/user/1',
      },
      config: {
        method: 'post',
        feedback: { mode: 'auto' as const, key: 'system.user.create' },
      },
    };

    const result = await afterResponse(response);

    expect(result).toBe(response);
    expect(Object.getOwnPropertyDescriptor(payload, '__httpMeta')?.value).toEqual({
      status: 201,
      requestId: 'req-1',
      traceId: 'trace-1',
      location: 'https://api.example.test/system/user/1',
      retryAfter: undefined,
      rateLimitLimit: undefined,
      rateLimitRemaining: undefined,
      rateLimitReset: undefined,
    });
    expect(payload.pager).toEqual({
      mode: 'offset',
      page: 2,
      size: 20,
      total: 12,
    });
    expect(presentSuccessFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 201,
        payload,
        feedback: expect.objectContaining({
          mode: 'auto' as const,
          key: 'system.user.create',
        }),
      })
    );
  });

  it('detects pure collection and cursor paging shapes without forcing query success toasts', async () => {
    const { clientConfig } = await loadModule();
    const afterResponse = clientConfig.transforms[1].afterResponse;

    const collectionPayload: Record<string, unknown> = {
      items: [{ id: 1 }, { id: 2 }],
    };
    await afterResponse({
      status: 200,
      data: collectionPayload,
      headers: {},
      config: {
        method: 'get',
      },
    });
    expect(collectionPayload.pager).toEqual({
      mode: 'collection',
      total: 2,
    });

    const cursorPayload: Record<string, unknown> = {
      items: [{ id: 1 }],
      pageSize: 50,
      nextCursor: 'cursor-2',
    };
    await afterResponse({
      status: 200,
      data: cursorPayload,
      headers: {},
      config: {
        method: 'get',
        feedback: { mode: 'auto' as const, key: 'system.user.create' },
      },
    });
    expect(cursorPayload.pager).toEqual({
      mode: 'cursor',
      size: 50,
      nextCursor: 'cursor-2',
    });
  });

  it('does not show expired-session feedback when already on the login page', async () => {
    window.history.pushState({}, '', '/login?redirect=/index');
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;

    await expect(onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
      problem: expect.objectContaining({
        detail: '登录状态已过期，请重新登录',
      }),
    });

    expect(ElMessage).not.toHaveBeenCalled();
    expect(presentProblemFeedback).not.toHaveBeenCalled();
  });

  it('prompts relogin when a protected page receives an expired session', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;

    await expect(onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
    });

    expect(ElMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'warning',
      })
    );
    expect(presentProblemFeedback).not.toHaveBeenCalled();
  });

  it('does not prompt relogin for silent session restore failures', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;

    await expect(
      onError({
        ...expiredAuthError,
        config: {
          method: 'post',
          silentError: true,
        },
      })
    ).rejects.toMatchObject({
      status: 401,
    });

    expect(ElMessage).not.toHaveBeenCalled();
    expect(presentProblemFeedback).not.toHaveBeenCalled();
  });

  it('closes an in-flight relogin prompt when entering the login route', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;

    await expect(onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
    });
    expect(ElMessage).toHaveBeenCalled();

    const { dismissReloginPrompt } = await import('@/utils/http');
    dismissReloginPrompt();

    expect(elMessageClose).toHaveBeenCalled();
  });

  it('presents skipped relogin auth problems through the unified error channel', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;

    await expect(
      onError({
        config: {
          method: 'post',
          skipRelogin: true,
          feedback: { mode: 'auto' as const },
        },
        response: {
          status: 401,
          data: {
            type: 'about:blank',
            title: '用户名或密码错误',
            status: 401,
            detail: '用户名或密码错误',
            instance: '',
            errorCode: 401,
          },
          headers: {},
        },
      })
    ).rejects.toMatchObject({
      status: 401,
      problem: expect.objectContaining({
        status: 401,
        detail: '用户名或密码错误',
      }),
    });

    expect(presentProblemFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        problem: expect.objectContaining({
          status: 401,
          detail: '用户名或密码错误',
        }),
        feedback: expect.objectContaining({
          mode: 'auto' as const,
        }),
      })
    );
  });

  it('normalizes problem details and forwards rate-limit headers to the problem presenter', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;
    const error = {
      config: {
        method: 'post',
        feedback: { mode: 'auto' as const, key: 'monitor.job.run' },
      },
      response: {
        status: 429,
        data: {
          type: 'https://problems.test/rate-limit',
          title: '请求过于频繁',
          status: 429,
          detail: '请稍后再试',
          instance: '/monitor/job/run',
        },
        headers: {
          'retry-after': '30',
          'ratelimit-limit': '100',
          'ratelimit-remaining': '0',
          'ratelimit-reset': '30',
          'x-request-id': 'req-429',
          'x-trace-id': 'trace-429',
        },
      },
    };

    await expect(onError(error)).rejects.toMatchObject({
      status: 429,
      problem: expect.objectContaining({
        title: '请求过于频繁',
        status: 429,
      }),
      meta: expect.objectContaining({
        retryAfter: 30,
        rateLimitLimit: 100,
        rateLimitRemaining: 0,
        rateLimitReset: 30,
      }),
    });
    expect(presentProblemFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        problem: expect.objectContaining({
          title: '请求过于频繁',
          status: 429,
        }),
        meta: expect.objectContaining({
          requestId: 'req-429',
          traceId: 'trace-429',
          retryAfter: 30,
        }),
      })
    );
  });

  it.each([
    [403, 30009, '不允许操作超级管理员用户'],
    [403, 30010, '没有权限访问用户数据'],
    [422, 30011, '修改密码失败，旧密码错误'],
  ])(
    'presents user failure %s/%s without expiring the session',
    async (status, errorCode, detail) => {
      const { clientConfig } = await loadModule();
      const { isRelogin } = await import('@/utils/http');
      const failure = {
        config: { method: 'put', feedback: { mode: 'auto' as const } },
        response: {
          status,
          data: {
            type: 'about:blank',
            title: detail,
            status,
            detail,
            errorCode,
            ...(status === 422
              ? {
                  errors: [
                    {
                      field: 'oldPassword',
                      message: detail,
                      code: 'value_error',
                    },
                  ],
                }
              : {}),
          },
          headers: {},
        },
      };

      await expect(clientConfig.transforms[1].onError(failure)).rejects.toMatchObject({
        status,
        problem: expect.objectContaining({ status, errorCode, detail }),
      });
      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(presentProblemFeedback).toHaveBeenCalledTimes(1);
      expect(presentProblemFeedback).toHaveBeenCalledWith(
        expect.objectContaining({
          problem: expect.objectContaining(failure.response.data),
        })
      );
      expect(ElMessage).not.toHaveBeenCalled();
      expect(isRelogin.show).toBe(false);
    }
  );

  it('passes 422 validation problems through the unified error channel', async () => {
    const { clientConfig } = await loadModule();
    const onError = clientConfig.transforms[1].onError;
    const validationTarget = { apply: vi.fn() };

    await expect(
      onError({
        config: {
          method: 'post',
          feedback: {
            mode: 'auto' as const,
            key: 'system.user.create',
            validationTarget,
          },
        },
        response: {
          status: 422,
          data: {
            type: 'https://problems.test/validation-error',
            title: '参数验证失败',
            status: 422,
            detail: '请检查输入字段',
            instance: '/system/user',
            errors: [{ field: 'userName', message: '不能为空', code: 'missing' }],
          },
          headers: {},
        },
      })
    ).rejects.toMatchObject({
      status: 422,
      problem: expect.objectContaining({
        errors: [{ field: 'userName', message: '不能为空', code: 'missing' }],
      }),
    });

    expect(presentProblemFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        problem: expect.objectContaining({
          status: 422,
          errors: [{ field: 'userName', message: '不能为空', code: 'missing' }],
        }),
        feedback: expect.objectContaining({
          validationTarget,
        }),
      })
    );
  });
  it('releases failed relogin presentation without replacing the original 401', async () => {
    const { clientConfig } = await loadModule();
    const { isRelogin } = await import('@/utils/http');
    const onError = clientConfig.transforms[1].onError;
    ElMessage.mockImplementationOnce(() => {
      throw new Error('message provider failed');
    });
    await expect(onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
      problem: { detail: '登录状态已过期，请重新登录' },
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(isRelogin.show).toBe(false);
    await expect(onError(expiredAuthError)).rejects.toMatchObject({ status: 401 });
    expect(ElMessage).toHaveBeenCalledTimes(2);
  });

  it('clears relogin state even if a message handle cannot close', async () => {
    const { clientConfig } = await loadModule();
    const { dismissReloginPrompt, isRelogin } = await import('@/utils/http');
    await expect(clientConfig.transforms[1].onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
    });
    elMessageClose.mockImplementationOnce(() => {
      throw new Error('provider disposed');
    });
    expect(dismissReloginPrompt).not.toThrow();
    expect(isRelogin.show).toBe(false);
  });
  it('contains asynchronous close failures from stale relogin prompts', async () => {
    const { clientConfig } = await loadModule();
    const { dismissReloginPrompt, isRelogin } = await import('@/utils/http');
    let closeCalls = 0;
    ElMessage.mockImplementationOnce(() => {
      dismissReloginPrompt();
      return {
        close: () => {
          closeCalls++;
          return Promise.reject(new Error('stale close rejected'));
        },
      };
    });
    await expect(clientConfig.transforms[1].onError(expiredAuthError)).rejects.toMatchObject({
      status: 401,
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(closeCalls).toBe(1);
    expect(isRelogin.show).toBe(false);
  });
  it('reuses auth recovery for a current read without changing its silent transport context', async () => {
    const { clientConfig } = await loadModule();
    const { presentRequestError, dismissReloginPrompt } = await import('@/utils/http');
    const failure = await clientConfig.transforms[1]
      .onError({
        ...expiredAuthError,
        config: { ...expiredAuthError.config, silentError: true },
      })
      .then(
        () => {
          throw new Error('Expected an HTTP failure');
        },
        (error) => error as HttpError
      );
    expect(ElMessage).not.toHaveBeenCalled();
    presentRequestError(failure, {
      ...failure.config,
      silentError: false,
      feedback: { mode: 'auto' },
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(ElMessage).toHaveBeenCalledTimes(1);
    expect(ElMessage.mock.calls[0][0]).toMatchObject({
      type: 'warning',
      action: { label: '重新登录' },
    });
    expect(failure.config).toMatchObject({ silentError: true });
    dismissReloginPrompt();
  });
  it.each([
    [401, 500],
    [400, 401],
  ])(
    'uses transport status %s for auth when problem status is %s',
    async (status, problemStatus) => {
      const { clientConfig } = await loadModule();
      const { dismissReloginPrompt } = await import('@/utils/http');
      await clientConfig.transforms[1]
        .onError({
          config: { url: '/private' },
          response: {
            status,
            data: {
              type: 'about:blank',
              title: 'failure',
              detail: 'failure',
              status: problemStatus,
            },
          },
        })
        .catch(() => undefined);
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(ElMessage).toHaveBeenCalledTimes(status === 401 ? 1 : 0);
      dismissReloginPrompt();
    }
  );
  it('leaves query read failures to local state while retaining current-scope auth recovery', async () => {
    const { rawOnError } = await loadModule();
    const { queryRequest } = await import('@zxio/http');
    const { setQuerySession, scopeRequestOptions } = await import('@/queries/context');
    const scope = setQuerySession(1, [], []);
    const options = queryRequest(new AbortController().signal, scopeRequestOptions(scope)).options;
    const failure = {
      ...expiredAuthError,
      response: {
        ...expiredAuthError.response,
        status: 503,
        data: { status: 503, detail: 'offline' },
      },
    };
    await rawOnError(failure, options).catch(() => undefined);
    expect(presentProblemFeedback).not.toHaveBeenCalled();
    expect(ElMessage).not.toHaveBeenCalled();
    await rawOnError(expiredAuthError, options).catch(() => undefined);
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(ElMessage).toHaveBeenCalledTimes(1);
  });

  it('suppresses old-scope response feedback and rejects a queued request before token application', async () => {
    const { rawOnError } = await loadModule();
    const { setQuerySession, endQuerySession, scopeRequestOptions } = await import(
      '@/queries/context'
    );
    const previous = setQuerySession(1, [], []);
    const options = scopeRequestOptions(previous);
    endQuerySession();
    setQuerySession(2, [], []);
    await rawOnError(expiredAuthError, options).catch(() => undefined);
    expect(ElMessage).not.toHaveBeenCalled();
    const config = createHttpClient.mock.calls[0][0];
    const beforeRequest = config.transforms?.[0]?.beforeRequest;
    await expect(
      beforeRequest?.(
        { url: '/system/dict/type', method: 'post' },
        options as ResolvedRequestOptions,
        {} as never
      )
    ).rejects.toMatchObject({ name: 'AbortError' });
  });
});
