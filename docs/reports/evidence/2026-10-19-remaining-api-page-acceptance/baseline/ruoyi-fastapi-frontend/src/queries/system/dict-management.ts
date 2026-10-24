import { shallowReactive, watch } from 'vue';
import { AbortError } from '@zxio/http';
import { dictCommands, captureDictCommand } from './dict';
import { queryScope, scopeRequestOptions } from '../context';
import type { RequestOptions } from '@zxio/http';

/** The option resource uses Query; these existing management lists still own their request views. */
export function useDictManagement(refreshList: () => unknown) {
  async function afterWrite<T>(operation: Promise<T>): Promise<T> {
    const scope = queryScope.value;
    const result = await operation;
    if (scope === queryScope.value) {
      try {
        void Promise.resolve(refreshList()).catch(reportRefreshError);
      } catch (error) {
        reportRefreshError(error);
      }
    }
    return result;
  }
  function reportRefreshError(error: unknown): void {
    window.dispatchEvent(new CustomEvent('ruoyi:dict-list-refresh-error', { detail: error }));
  }
  return {
    createItem: (input: Parameters<typeof dictCommands.createItem>[0]['input']) =>
      afterWrite(dictCommands.createItem(captureDictCommand(input))),
    updateItem: (input: Parameters<typeof dictCommands.updateItem>[0]['input']) =>
      afterWrite(dictCommands.updateItem(captureDictCommand(input))),
    deleteItems: (input: Parameters<typeof dictCommands.deleteItems>[0]['input']) =>
      afterWrite(dictCommands.deleteItems(captureDictCommand(input))),
    deleteTypes: (input: Parameters<typeof dictCommands.deleteTypes>[0]['input']) =>
      afterWrite(dictCommands.deleteTypes(captureDictCommand(input))),
    refreshCache: () => afterWrite(dictCommands.refreshCache(captureDictCommand(null))),
  };
}

/** Request-mode list state stays local until stage B adopts the controlled list contract. */
export function useDictManagementList<P, R>(
  load: (params: P, options: RequestOptions) => Promise<R>
) {
  const status = shallowReactive({ loading: false, error: null as unknown, hasData: false });
  let lastSuccess: { identity: string; result: R } | undefined;
  let generation = 0;
  watch(
    queryScope,
    () => {
      generation++;
      lastSuccess = undefined;
      status.loading = false;
      status.error = null;
      status.hasData = false;
    },
    { flush: 'sync' }
  );
  async function loadData(params: P): Promise<R> {
    const scope = queryScope.value;
    if (!scope) throw new AbortError({ message: '会话已结束，请重新登录' });
    const identity = JSON.stringify([scope.key, params]);
    const request = ++generation;
    status.loading = true;
    status.error = null;
    status.hasData = lastSuccess?.identity === identity;
    try {
      const result = await load(params, scopeRequestOptions(scope));
      if (scope !== queryScope.value) throw new AbortError({ message: '会话已结束，请重新登录' });
      if (request === generation) {
        lastSuccess = { identity, result };
        status.hasData = true;
      }
      return result;
    } catch (error) {
      if (request === generation) status.error = error;
      // Keep this request view's last result for the same scope and filters; never cache options here.
      if (lastSuccess?.identity === identity && scope === queryScope.value)
        return lastSuccess.result;
      throw error;
    } finally {
      if (request === generation) status.loading = false;
    }
  }
  return { loadData, status };
}
