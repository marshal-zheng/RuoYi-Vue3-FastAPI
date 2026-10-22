import axios, {
  AxiosError,
  CanceledError,
  type AxiosAdapter,
  type InternalAxiosRequestConfig,
} from 'axios';
import type { RequestOptions } from '@zxio/http';
import { assertRequestScope } from '@/queries/context';
import {
  getCsrfToken,
  getSecurityTokenVersion,
  getSecuritySessionVersion,
  getSecuritySessionSignal,
  getToken,
  setCsrfToken,
  setToken,
} from './auth';

interface SessionResponse {
  token: string;
  csrfToken?: string;
}

type SessionConfig = InternalAxiosRequestConfig & {
  requestOptions?: RequestOptions;
};

let cookieOperations: Promise<unknown> = Promise.resolve();

/** Login, logout and renewal all replace the same origin-wide authentication cookies. */
export const withSessionCookieLock = async <T>(
  operation: () => Promise<T>,
  signal?: AbortSignal
): Promise<T> => {
  const run = () => {
    if (signal?.aborted) throw new CanceledError('Session changed');
    return operation();
  };
  if (typeof navigator !== 'undefined' && navigator.locks) {
    return await navigator.locks
      .request('ruoyi-session-refresh', { signal }, run)
      .catch((error) => {
        if (signal?.aborted) throw new CanceledError('Session changed');
        throw error;
      });
  }
  const result = cookieOperations.then(run, run);
  cookieOperations = result.catch(() => undefined);
  return result;
};

const expiresSoon = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now() + 30_000;
  } catch {
    return false;
  }
};

const assertCurrent = (config: SessionConfig): void => {
  if (config.signal?.aborted) throw new CanceledError('Request was cancelled', config);
  config.cancelToken?.throwIfRequested();
  assertRequestScope(config.requestOptions);
};

const waitForRefresh = (refresh: Promise<string>, config: SessionConfig): Promise<string> => {
  assertCurrent(config);
  return new Promise((resolve, reject) => {
    const abort = () => reject(new CanceledError('Request was cancelled', config));
    config.signal?.addEventListener?.('abort', abort, { once: true });
    refresh
      .then(resolve, reject)
      .finally(() => config.signal?.removeEventListener?.('abort', abort));
  });
};

/** One browser-session flight; Axios still owns serialization, parsing and cancellation. */
export const createSessionTransport = (onToken: (token: string) => void) => {
  const refreshClient = axios.create({
    baseURL: import.meta.env.VITE_APP_BASE_API,
    timeout: 10000,
  });
  const transport = axios.getAdapter(axios.defaults.adapter);
  let pending: Promise<string> | undefined;
  let pendingVersion: number | undefined;

  const refresh = (): Promise<string> => {
    const version = getSecurityTokenVersion();
    if (pending && pendingVersion === version) return pending;
    const signal = getSecuritySessionSignal();
    const renew = async () => {
      if (getSecurityTokenVersion() !== version) throw new CanceledError('Session changed');
      const response = await refreshClient.post<SessionResponse>('/auth/refresh', undefined, {
        headers: { 'X-CSRF-Token': getCsrfToken() || '' },
        signal,
      });
      if (getSecurityTokenVersion() !== version) throw new CanceledError('Session changed');
      if (!response.data.token) throw new Error('Session refresh response is missing token');
      setToken(response.data.token);
      setCsrfToken(response.data.csrfToken || '');
      onToken(response.data.token);
      return response.data.token;
    };
    const task = withSessionCookieLock(renew, signal);
    pendingVersion = version;
    const flight = Promise.resolve(task)
      .then((value) => value)
      .finally(() => {
        if (pending === flight) {
          pending = undefined;
          pendingVersion = undefined;
        }
      });
    pending = flight;
    return flight;
  };

  const applyCredentials = (config: SessionConfig) => {
    assertCurrent(config);
    const token = getToken();
    if (token) config.headers.set('Authorization', `Bearer ${token}`);
    const csrf = getCsrfToken();
    if (csrf) config.headers.set('X-CSRF-Token', csrf);
  };

  const adapter: AxiosAdapter = async (rawConfig) => {
    const config = rawConfig as SessionConfig;
    const sessionVersion = getSecuritySessionVersion();
    const assertSession = () => {
      assertCurrent(config);
      if (getSecuritySessionVersion() !== sessionVersion)
        throw new CanceledError('Session changed', config);
    };
    const protectedRequest =
      config.requestOptions?.withToken !== false &&
      config.headers.get('isToken') !== false &&
      !/^\/(?:login|register|auth\/(?:refresh|logout))(?:\?|$)/.test(config.url || '') &&
      Boolean(getToken()) &&
      config.headers.has('Authorization');
    if (!protectedRequest) return transport(config);
    if (expiresSoon(getToken() || '')) {
      try {
        await waitForRefresh(refresh(), config);
      } catch (error) {
        assertCurrent(config);
        if (axios.isAxiosError(error)) {
          throw new AxiosError(
            error.message,
            error.code,
            config,
            error.request,
            error.response ? { ...error.response, config } : undefined
          );
        }
        throw error;
      }
    }
    assertSession();
    applyCredentials(config);
    const sentToken = getToken();
    try {
      return await transport(config);
    } catch (error) {
      if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error;
      assertSession();
      // A late rejection may belong to the token another request already replaced.
      if (getToken() === sentToken) {
        try {
          await waitForRefresh(refresh(), config);
        } catch {
          assertSession();
          throw error;
        }
      }
      assertSession();
      if (!getToken()) throw error;
      applyCredentials(config);
      // Retry only an explicit auth rejection, once, with the same serialized body.
      return transport(config);
    }
  };
  return { adapter, refresh };
};
