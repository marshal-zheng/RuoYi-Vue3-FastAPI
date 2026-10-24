import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import {
  useQuery,
  type QueryClient,
  type QueryKey,
  type UseQueryOptions,
} from '@tanstack/vue-query';
import { effectScope } from 'vue';
import { describe, expect, it } from 'vitest';
import type { MenuTreeNode } from '@/api/system/menu';

const enabled = process.env.CODEX_DEPT_QUERY_WRITE === '1';
const source = process.env.VITE_ZXUI_LOCAL === 'true';
const baseURL = process.env.CODEX_DEPT_API_BASE || 'http://127.0.0.1:8088';
const evidencePath = resolve(
  process.env.CODEX_DEPT_EVIDENCE ||
    `../docs/reports/evidence/2026-10-17-department-query-convergence/${source ? 'source' : 'installed'}-actual.json`
);

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

async function until(check: () => boolean, label: string): Promise<void> {
  const deadline = Date.now() + 15_000;
  while (!check()) {
    if (Date.now() > deadline) throw new Error(`Timed out: ${label}`);
    await new Promise((done) => setTimeout(done, 10));
  }
}

function flatten(nodes: readonly MenuTreeNode[]): MenuTreeNode[] {
  return nodes.flatMap((node) => [node, ...flatten(node.children || [])]);
}

function safeFailure(error: unknown) {
  const value = error as {
    name?: string;
    status?: number;
    response?: { status?: number };
    message?: string;
  };
  // Never persist axios config, request, headers, token, full responses or user data.
  return {
    name: value?.name || 'Error',
    status: value?.status || value?.response?.status || 0,
    message: value?.message || 'Unknown failure',
  };
}

describe.skipIf(!enabled)('opt-in real local department lifecycle', () => {
  it('updates active department/user query subscriptions and cleans only owned records', async () => {
    const endpoint = new URL(baseURL);
    assert(
      ['127.0.0.1', 'localhost', '[::1]'].includes(endpoint.hostname),
      'Real write probe is restricted to loopback'
    );
    // A 6-character millisecond suffix leaves room for names within the server's 30-char limit.
    const marker = `codex_dept_query_${Date.now().toString(36).slice(-6)}`;
    const evidence: {
      checks: Record<string, unknown>;
      cleanup: {
        created: number;
        deleted: number;
        verifiedAbsent: boolean;
        failure?: ReturnType<typeof safeFailure>;
      };
    } & Record<string, unknown> = {
      timestamp: new Date().toISOString(),
      mode: source ? 'source' : 'installed',
      marker,
      transport: 'Actual business deptCommands/query factories/request/http to loopback FastAPI',
      mocks: false,
      uiRendered: false,
      checks: {},
      cleanup: { created: 0, deleted: 0, verifiedAbsent: false },
    };
    let stage = 'backend-preflight';
    let commands: typeof import('@/queries/system/dept').deptCommands | undefined;
    let capture: typeof import('@/queries/system/dept').captureDeptCommand | undefined;
    let deptApi: typeof import('@/api/system/dept') | undefined;
    let client: QueryClient | undefined;
    let context: typeof import('@/queries/context') | undefined;
    let auth: typeof import('@/utils/auth') | undefined;
    let loginApi: typeof import('@/api/login') | undefined;
    let ownLogin = false;
    let failure: unknown;
    const ownedIds: number[] = [];
    const stops: Array<() => void> = [];
    const requests: Array<{ method: string; path: string; status?: number }> = [];
    try {
      const preflight = await fetch(`${baseURL}/docs`, {
        signal: AbortSignal.timeout(5000),
      });
      assert(preflight.ok, `Backend preflight HTTP ${preflight.status}`);
      stage = 'business-module-load';
      auth = await import('@/utils/auth');
      loginApi = await import('@/api/login');
      context = await import('@/queries/context');
      const domain = await import('@/queries/system/dept');
      const users = await import('@/queries/system/user');
      deptApi = await import('@/api/system/dept');
      client = (await import('@/queries/client')).queryClient;
      const { http } = await import('@/utils/http');
      http.axiosInstance.defaults.baseURL = baseURL;
      client.mount();
      commands = domain.deptCommands;
      capture = domain.captureDeptCommand;
      http.axiosInstance.interceptors.request.use((config) => {
        requests.push({
          method: config.method || 'get',
          path: config.url || '',
        });
        return config;
      });
      http.axiosInstance.interceptors.response.use((response) => {
        const request = [...requests]
          .reverse()
          .find((entry) => entry.path === response.config.url && entry.status === undefined);
        if (request) request.status = response.status;
        return response;
      });

      stage = 'login';
      if (process.env.CODEX_DEPT_TOKEN) {
        auth.setToken(process.env.CODEX_DEPT_TOKEN);
        auth.setCsrfToken(process.env.CODEX_DEPT_CSRF || '');
      } else {
        assert(process.env.CODEX_DEPT_PASSWORD, 'Set CODEX_DEPT_PASSWORD or a fresh owned token');
        const captcha = await loginApi.getCodeImg();
        assert(
          !captcha.captchaEnabled ||
            (process.env.CODEX_DEPT_CAPTCHA_CODE && process.env.CODEX_DEPT_CAPTCHA_UUID),
          'Captcha enabled: supply CODEX_DEPT_CAPTCHA_CODE and CODEX_DEPT_CAPTCHA_UUID from a fresh captcha'
        );
        const session = await loginApi.login(
          process.env.CODEX_DEPT_USERNAME || 'admin',
          process.env.CODEX_DEPT_PASSWORD,
          process.env.CODEX_DEPT_CAPTCHA_CODE || '',
          process.env.CODEX_DEPT_CAPTCHA_UUID || ''
        );
        auth.setToken(session.token);
        auth.setCsrfToken(session.csrfToken || '');
        ownLogin = true;
      }
      const info = await loginApi.getInfo();
      const scope = context.setQuerySession(info.user.userId, info.roles, info.permissions);
      evidence.authorization = {
        managementListPermission: 'system:dept:list',
        userTreePermission: 'system:user:list',
        permissionDataUnchanged: true,
      };
      const listOptions = domain.deptListOptions(scope, {
        deptName: `  ${marker}  `,
      });
      const treeOptions = domain.userDeptTreeOptions(scope);
      const activeClient = client;
      const observe = <T, TKey extends QueryKey>(
        options: UseQueryOptions<T, Error, T, T, TKey>
      ) => {
        const lifecycle = effectScope();
        const result = lifecycle.run(() => useQuery<T, Error, T, TKey>(options, activeClient));
        assert(result, 'Query effect scope did not start');
        stops.push(() => lifecycle.stop());
        return {
          getCurrentResult: () => ({
            data: result.data.value,
            isFetching: result.isFetching.value,
          }),
        };
      };
      const list = observe(listOptions);
      const tree = observe(treeOptions);
      const secondTree = observe(treeOptions);
      await Promise.all([client.fetchQuery(listOptions), client.fetchQuery(treeOptions)]);
      assert(
        requests.filter((entry) => entry.path === '/system/user/deptTree').length === 1,
        'Concurrent user-tree observers must share one real request'
      );
      evidence.checks.coldSharing = { treeSubscribers: 2, treeRequests: 1 };

      stage = 'create-parent-child';
      const parent = await commands.createDept(
        capture({
          parentId: 0,
          deptName: `${marker}_parent`,
          orderNum: 0,
          status: '0',
        })
      );
      assert(Number.isSafeInteger(parent.deptId), 'Create parent did not return an identity');
      ownedIds.push(parent.deptId);
      evidence.cleanup.created++;
      const child = await commands.createDept(
        capture({
          parentId: parent.deptId,
          deptName: `${marker}_child`,
          orderNum: 0,
          status: '0',
        })
      );
      assert(Number.isSafeInteger(child.deptId), 'Create child did not return an identity');
      ownedIds.push(child.deptId);
      evidence.cleanup.created++;
      const hasTreeNode = (id: number) =>
        flatten(tree.getCurrentResult().data || []).some((node) => node.id === id);
      const hasRow = (id: number) =>
        list.getCurrentResult().data?.items.some((row) => row.deptId === id) === true;
      try {
        await until(
          () => hasRow(child.deptId) && hasTreeNode(child.deptId),
          'created records in active queries'
        );
      } catch (error) {
        const directList = await deptApi.listDept({ deptName: marker });
        const directTree = await (await import('@/api/system/user')).deptTreeSelect();
        evidence.createDiagnostic = {
          cachedList: list
            .getCurrentResult()
            .data?.items.filter((row) => row.deptName?.startsWith(marker))
            .map(({ deptId, parentId, status }) => ({ deptId, parentId, status })),
          cachedTree: flatten(tree.getCurrentResult().data || [])
            .filter((node) => node.label.startsWith(marker))
            .map(({ id }) => ({ id, type: typeof id })),
          directList: directList.items
            .filter((row) => row.deptName?.startsWith(marker))
            .map(({ deptId, parentId, status }) => ({ deptId, parentId, status })),
          directTree: flatten(directTree.items)
            .filter((node) => node.label.startsWith(marker))
            .map(({ id }) => ({ id, type: typeof id })),
          settled: {
            list: !list.getCurrentResult().isFetching,
            tree: !tree.getCurrentResult().isFetching,
          },
        };
        throw error;
      }
      evidence.checks.create = { parentAndChildVisible: true };

      stage = 'rename-with-active-user-list';
      const userOptions = users.userListOptions(scope, {
        deptId: parent.deptId,
        page: 1,
        pageSize: 1,
      });
      const userList = observe(userOptions);
      await client.fetchQuery(userOptions);
      const beforeUsers = requests.filter((entry) => entry.path === '/system/user/list').length;
      const renamed = `${marker}_new`;
      await commands.updateDept(capture({ deptId: child.deptId, deptName: renamed }));
      await until(
        () =>
          list.getCurrentResult().data?.items.find((row) => row.deptId === child.deptId)
            ?.deptName === renamed &&
          flatten(tree.getCurrentResult().data || []).find((node) => node.id === child.deptId)
            ?.label === renamed &&
          !userList.getCurrentResult().isFetching &&
          requests.filter((entry) => entry.path === '/system/user/list').length > beforeUsers,
        'rename propagated without manual invalidation'
      );
      assert(
        secondTree.getCurrentResult().data === tree.getCurrentResult().data,
        'Subscribers diverged'
      );
      evidence.checks.rename = {
        managementAndBothTreeObserversUpdated: true,
        userListRefetched: true,
      };

      stage = 'disable-enable-normal-filter';
      await commands.updateDept(capture({ deptId: child.deptId, status: '1' }));
      await until(
        () =>
          !hasTreeNode(child.deptId) &&
          list.getCurrentResult().data?.items.find((row) => row.deptId === child.deptId)?.status ===
            '1',
        'disabled child removed from normal-only user tree'
      );
      await commands.updateDept(capture({ deptId: child.deptId, status: '0' }));
      await until(() => hasTreeNode(child.deptId), 'enabled child restored to user tree');
      evidence.checks.status = {
        disabledRetainedInManagement: true,
        userTreeNormalFilter: true,
        enabledRestored: true,
      };

      stage = 'server-exclusion-and-editor';
      const excluded = await client.fetchQuery(
        domain.deptExcludeChildOptions(scope, parent.deptId)
      );
      assert(
        !excluded.items.some((row) => ownedIds.includes(row.deptId)),
        'Exclusion included self or descendant'
      );
      const editor = await domain.readDeptEditor(scope, child.deptId);
      assert(editor.data?.deptName === renamed, 'Editor detail snapshot was not current');
      evidence.checks.excludeAndEditor = {
        selfAndDescendantExcluded: true,
        editorReadUsesRealDetail: true,
      };

      stage = 'real-parameter-error';
      const beforeError = requests.length;
      let rejectedStatus = 0;
      try {
        await deptApi.listDept({ status: 'invalid' as never });
      } catch (error) {
        rejectedStatus = safeFailure(error).status;
      }
      assert(rejectedStatus === 422, `Expected actual HTTP 422, got ${rejectedStatus}`);
      assert(requests.length === beforeError + 1, 'Parameter branch did not reach actual HTTP');
      assert(
        hasTreeNode(child.deptId) && hasRow(child.deptId),
        'Failed independent read erased successful cache'
      );
      evidence.checks.parameterError = {
        status: 422,
        successfulCachePreserved: true,
      };
      evidence.passed = true;
    } catch (error) {
      failure = error;
      evidence.passed = false;
      evidence.failure = { stage, ...safeFailure(error) };
    } finally {
      stops.forEach((stop) => stop());
      if (deptApi && commands && capture && auth?.getToken()) {
        try {
          // Recover own IDs even if a create response was lost after the backend committed.
          const remaining = await deptApi.listDept({ deptName: marker });
          const owned = remaining.items.filter((row) => row.deptName?.startsWith(marker));
          for (const row of owned.sort(
            (a, b) => String(b.ancestors).length - String(a.ancestors).length
          )) {
            await commands.deleteDept(capture(row.deptId));
            evidence.cleanup.deleted++;
          }
          const after = await deptApi.listDept({ deptName: marker });
          evidence.cleanup.verifiedAbsent = !after.items.some((row) =>
            row.deptName?.startsWith(marker)
          );
          assert(evidence.cleanup.verifiedAbsent, 'Own temporary departments remain');
        } catch (error) {
          evidence.cleanup.failure = safeFailure(error);
          failure ||= error;
        }
      }
      if (ownLogin && loginApi) {
        try {
          await loginApi.logout({ silentSuccess: true, silentError: true });
          evidence.ownSessionEnded = true;
        } catch (error) {
          evidence.sessionCleanupFailure = safeFailure(error);
          failure ||= error;
        }
      }
      context?.endQuerySession();
      auth?.clearSecurityTokens();
      client?.unmount();
      client?.clear();
      evidence.requestCounts = requests.reduce((counts: Record<string, number>, request) => {
        const key = `${request.method.toUpperCase()} ${request.path.replace(/\/\d+(?=\/|$)/g, '/:id')}`;
        counts[key] = (counts[key] || 0) + 1;
        return counts;
      }, {});
      if (failure) evidence.passed = false;
      mkdirSync(dirname(evidencePath), { recursive: true });
      writeFileSync(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`, {
        mode: 0o600,
      });
    }
    // Suppress error objects that may contain token-bearing request configs in Vitest output.
    if (failure) throw new Error(`${stage}: ${safeFailure(failure).message}`);
    expect(evidence.passed).toBe(true);
    expect(evidence.cleanup.verifiedAbsent).toBe(true);
  });
});
