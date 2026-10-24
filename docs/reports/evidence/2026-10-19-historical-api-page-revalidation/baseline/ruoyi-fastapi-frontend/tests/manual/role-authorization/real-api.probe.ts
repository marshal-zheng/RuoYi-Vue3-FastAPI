import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { useQuery } from '@tanstack/vue-query';
import { effectScope } from 'vue';
import { describe, expect, it } from 'vitest';

const enabled = process.env.CODEX_ROLE_QUERY_WRITE === '1';
const baseURL = process.env.CODEX_ROLE_API_BASE || 'http://127.0.0.1:8088';
const source = process.env.VITE_ZXUI_LOCAL === 'true';
const evidencePath = resolve(
  process.env.CODEX_ROLE_EVIDENCE ||
    `../docs/reports/evidence/2026-10-17-role-authorization-convergence/${source ? 'source' : 'installed'}-actual.json`
);
function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
async function until(check: () => boolean, label: string) {
  const deadline = Date.now() + 15_000;
  while (!check()) {
    if (Date.now() > deadline) throw new Error(`Timed out: ${label}`);
    await new Promise((done) => setTimeout(done, 15));
  }
}
function safeFailure(error: unknown) {
  const e = error as {
    name?: string;
    message?: string;
    status?: number;
    response?: { status?: number };
  };
  return {
    name: e?.name || 'Error',
    status: e?.status || e?.response?.status || 0,
    message: e?.message || 'Unknown error',
  };
}

describe.skipIf(!enabled)('owned real local role and authorization lifecycle', () => {
  it('coordinates bidirectional writes, page reads and embedded catalogs, then removes its fixtures', async () => {
    assert(
      ['127.0.0.1', 'localhost', '[::1]'].includes(new URL(baseURL).hostname),
      'Loopback only'
    );
    const marker = `codex_ra_${Date.now().toString(36).slice(-7)}`;
    const evidence: Record<string, any> = {
      timestamp: new Date().toISOString(),
      marker,
      mode: source ? 'source' : 'installed',
      transport: 'Real business commands/query options/useQuery/HTTP to loopback FastAPI',
      runtime: process.env.CODEX_ROLE_RUNTIME || 'standard-no-overlay',
      mocks: false,
      uiRendered: false,
      checks: {},
      cleanup: { users: 0, roles: 0, verifiedAbsent: false },
    };
    const requests: Array<{ method: string; path: string }> = [];
    const stops: Array<() => void> = [];
    let stage = 'preflight';
    let failure: unknown;
    let ownLogin = false;
    const users = await import('@/queries/system/user');
    const roles = await import('@/queries/system/role');
    const userApi = await import('@/api/system/user');
    const roleApi = await import('@/api/system/role');
    const loginApi = await import('@/api/login');
    const auth = await import('@/utils/auth');
    const context = await import('@/queries/context');
    const { queryClient: client } = await import('@/queries/client');
    const { http } = await import('@/utils/http');
    http.axiosInstance.defaults.baseURL = baseURL;
    const interceptor = http.axiosInstance.interceptors.request.use((config) => {
      requests.push({ method: config.method || 'get', path: config.url || '' });
      return config;
    });
    client.mount();
    const observe = (options: any) => {
      const lifecycle = effectScope();
      const query = lifecycle.run(() => useQuery(options, client))!;
      stops.push(() => lifecycle.stop());
      return query as any;
    };
    const roleIds: number[] = [];
    const userIds: number[] = [];
    try {
      assert(
        (await fetch(`${baseURL}/docs`, { signal: AbortSignal.timeout(5000) })).ok,
        'Backend unavailable'
      );
      const captcha = await loginApi.getCodeImg();
      assert(!captcha.captchaEnabled, 'Captcha enabled; no setting changed');
      assert(process.env.CODEX_ROLE_PASSWORD, 'Set CODEX_ROLE_PASSWORD');
      const session = await loginApi.login(
        process.env.CODEX_ROLE_USERNAME || 'admin',
        process.env.CODEX_ROLE_PASSWORD,
        '',
        ''
      );
      auth.setToken(session.token);
      auth.setCsrfToken(session.csrfToken || '');
      ownLogin = true;
      const info = await loginApi.getInfo();
      const scope = context.setQuerySession(info.user.userId, info.roles, info.permissions);
      const roleList = observe(roles.roleListOptions(scope, { roleName: marker, pageSize: 10 }));
      const secondList = observe(
        roles.roleListOptions(scope, { roleName: ` ${marker} `, pageSize: 10 })
      );
      await until(() => roleList.isSuccess.value && secondList.isSuccess.value, 'initial roles');
      assert(
        requests.filter((x) => x.path === '/system/role/list').length === 1,
        'Same role conditions must share one read'
      );
      evidence.checks.sharedRoleRead = { subscribers: 2, requests: 1 };
      const catalogs = observe(users.userCreateOptions(scope));
      stage = 'create-owned-fixtures';
      for (let i = 0; i < 3; i++) {
        const role = await roles.roleCommands.createRole(
          roles.captureRoleCommand({
            roleName: `${marker}_r${i}`,
            roleKey: `${marker}_r${i}`,
            roleSort: 0,
            status: '0',
            menuIds: [],
          })
        );
        roleIds.push(role.roleId);
        await users.userCommands.createUser(
          users.captureUserCommand({
            userName: `${marker}_u${i}`,
            nickName: `${marker}_u${i}`,
            password: `Probe${Date.now()}!`,
            status: '0',
            roleIds: [],
            postIds: [],
          })
        );
        const createdUsers = await userApi.listUser({ userName: `${marker}_u${i}`, pageSize: 10 });
        const user = createdUsers.items.find((item) => item.userName === `${marker}_u${i}`);
        assert(user?.userId, 'Created user missing from independent list');
        userIds.push(user.userId);
      }
      await until(
        () =>
          roleList.data.value?.total === 3 &&
          catalogs.data.value?.roles?.some((r: any) => r.roleId === roleIds[2]),
        'role create invalidates embedded user catalog'
      );
      evidence.checks.roleCreateCatalog = true;
      const rolePage2 = await client.fetchQuery(
        roles.roleListOptions(scope, { roleName: marker, page: 2, pageSize: 1 })
      );
      assert(rolePage2.items.length === 1 && rolePage2.total === 3, 'Role page 2/size 1');
      const filters = { userName: marker, pageSize: 1 };
      const allocated = observe(users.roleUsersOptions(scope, roleIds[0], 'allocated', filters));
      const unallocated = observe(
        users.roleUsersOptions(scope, roleIds[0], 'unallocated', filters)
      );
      const duplicate = observe(users.roleUsersOptions(scope, roleIds[0], 'unallocated', filters));
      const firstUserRoles = observe(users.userAuthRoleOptions(scope, userIds[0]));
      await until(
        () =>
          allocated.data.value?.total === 0 &&
          unallocated.data.value?.total === 3 &&
          duplicate.data.value?.total === 3 &&
          firstUserRoles.isSuccess.value,
        'initial authorization'
      );
      const unallocated2 = await client.fetchQuery(
        users.roleUsersOptions(scope, roleIds[0], 'unallocated', { ...filters, page: 2 })
      );
      assert(
        unallocated2.items.length === 1 &&
          unallocated2.items[0].userId !== unallocated.data.value.items[0].userId,
        'Unallocated second page is distinct'
      );
      evidence.checks.authorizationPaging = { total: 3, pageSize: 1, distinctPage2: true };

      stage = 'incremental-grant';
      await users.userCommands.assignRoleUsers(
        users.captureUserCommand({ roleId: roleIds[0], userIds })
      );
      await until(
        () =>
          allocated.data.value?.total === 3 &&
          unallocated.data.value?.total === 0 &&
          firstUserRoles.data.value?.roles.some((r: any) => r.roleId === roleIds[0] && r.flag),
        'grant updates both authorization directions'
      );
      const allocated2 = await client.fetchQuery(
        users.roleUsersOptions(scope, roleIds[0], 'allocated', { ...filters, page: 2 })
      );
      assert(
        allocated2.items[0].userId !== allocated.data.value.items[0].userId,
        'Allocated second page is distinct'
      );
      evidence.checks.incrementalGrant = true;
      const secondRoleAllocated = observe(
        users.roleUsersOptions(scope, roleIds[1], 'allocated', filters)
      );
      stage = 'full-replacement';
      await users.userCommands.assignRoles(
        users.captureUserCommand({ userId: userIds[0], roleIds: [roleIds[1], roleIds[2]] })
      );
      await until(
        () =>
          allocated.data.value?.total === 2 &&
          unallocated.data.value?.total === 1 &&
          secondRoleAllocated.data.value?.total === 1,
        'replace fans out to role users'
      );
      const assignedIds = () =>
        firstUserRoles.data.value?.roles
          .filter((r: any) => r.flag)
          .map((r: any) => r.roleId)
          .sort((a: number, b: number) => a - b);
      await until(
        () =>
          JSON.stringify(assignedIds()) ===
          JSON.stringify([roleIds[1], roleIds[2]].sort((a, b) => a - b)),
        'full replacement reflects user roles'
      );
      evidence.checks.fullReplacement = true;

      stage = 'role-rename-and-inactive-association';
      await roles.roleCommands.updateRole(
        roles.captureRoleCommand({
          roleId: roleIds[1],
          roleName: `${marker}_renamed`,
          roleKey: `${marker}_r1`,
          roleSort: 0,
        })
      );
      await until(
        () =>
          firstUserRoles.data.value?.roles.some(
            (r: any) => r.roleId === roleIds[1] && r.roleName === `${marker}_renamed`
          ) &&
          catalogs.data.value?.roles?.some(
            (r: any) => r.roleId === roleIds[1] && r.roleName === `${marker}_renamed`
          ),
        'rename updates catalogs'
      );
      await roles.roleCommands.changeStatus(
        roles.captureRoleCommand({ roleId: roleIds[1], status: '1' })
      );
      await until(
        () =>
          firstUserRoles.data.value?.roles.some(
            (r: any) => r.roleId === roleIds[1] && r.status === '1' && r.flag
          ),
        'inactive association stays visible'
      );
      evidence.checks.inactiveAssociationPreserved = true;
      await users.userCommands.assignRoles(
        users.captureUserCommand({ userId: userIds[0], roleIds: [roleIds[1], roleIds[2]] })
      );
      await roles.roleCommands.changeStatus(
        roles.captureRoleCommand({ roleId: roleIds[1], status: '0' })
      );

      stage = 'explicit-empty-and-revokes';
      await users.userCommands.assignRoles(
        users.captureUserCommand({ userId: userIds[0], roleIds: [] })
      );
      await until(
        () => assignedIds()?.length === 0 && secondRoleAllocated.data.value?.total === 0,
        'explicit empty removes all'
      );
      await users.userCommands.unassignRoleUser(
        users.captureUserCommand({ roleId: roleIds[0], userId: userIds[1] })
      );
      await until(() => allocated.data.value?.total === 1, 'single revoke');
      await users.userCommands.unassignRoleUsers(
        users.captureUserCommand({ roleId: roleIds[0], userIds: [userIds[2]] })
      );
      await until(
        () => allocated.data.value?.total === 0 && unallocated.data.value?.total === 3,
        'batch revoke'
      );
      evidence.checks.explicitEmptyAndIncrementalRevokes = true;

      stage = 'editor-snapshots-and-invalid-write';
      const editor = await roles.readRoleEditor(scope, roleIds[0]);
      assert(editor.data?.roleId === roleIds[0], 'Role editor identity');
      await roles.roleCommands.updateDataScope(
        roles.captureRoleCommand({
          roleId: roleIds[0],
          dataScope: '2',
          deptIds: [],
          deptCheckStrictly: true,
        })
      );
      const scoped = await roles.readRoleDataScopeEditor(scope, roleIds[0]);
      assert(scoped.data.dataScope === '2', 'Data scope detail');
      let invalidStatus = 0;
      try {
        await roles.roleCommands.changeStatus(
          roles.captureRoleCommand({ roleId: roleIds[0], status: 'invalid' as any })
        );
      } catch (error) {
        invalidStatus = safeFailure(error).status;
      }
      assert(invalidStatus === 422, 'Invalid status must return actual HTTP 422');
      evidence.checks.editorAndValidation = { dataScope: '2', invalidStatus };
      evidence.passed = true;
    } catch (error) {
      failure = error;
      evidence.failure = { stage, ...safeFailure(error) };
      evidence.passed = false;
    } finally {
      stops.splice(0).forEach((stop) => stop());
      if (ownLogin) {
        try {
          // Recover even a lost POST response by querying only this unique task marker.
          const ownedUsers = (
            await userApi.listUser({ userName: marker, pageSize: 100 })
          ).items.filter((u) => u.userName?.startsWith(marker));
          for (const user of ownedUsers) {
            await users.userCommands.assignRoles(
              users.captureUserCommand({ userId: user.userId!, roleIds: [] })
            );
            await users.userCommands.deleteUsers(users.captureUserCommand(user.userId!));
            evidence.cleanup.users++;
          }
          const ownedRoles = (
            await roleApi.listRole({ roleName: marker, pageSize: 100 })
          ).items.filter((r) => r.roleName?.startsWith(marker));
          for (const role of ownedRoles) {
            await roles.roleCommands.deleteRoles(roles.captureRoleCommand(role.roleId));
            evidence.cleanup.roles++;
          }
          const remainingUsers = await userApi.listUser({ userName: marker, pageSize: 100 });
          const remainingRoles = await roleApi.listRole({ roleName: marker, pageSize: 100 });
          evidence.cleanup.verifiedAbsent =
            remainingUsers.total === 0 && remainingRoles.total === 0;
          assert(evidence.cleanup.verifiedAbsent, 'Task fixtures remain');
        } catch (error) {
          evidence.cleanup.failure = safeFailure(error);
          failure ||= error;
        }
        try {
          await loginApi.logout({ silentError: true, silentSuccess: true });
          evidence.ownSessionEnded = true;
        } catch (error) {
          evidence.logoutFailure = safeFailure(error);
          failure ||= error;
        }
      }
      context.endQuerySession();
      auth.clearSecurityTokens();
      client.unmount();
      client.clear();
      http.axiosInstance.interceptors.request.eject(interceptor);
      evidence.requestCounts = requests.reduce((counts: Record<string, number>, request) => {
        const key = `${request.method.toUpperCase()} ${request.path.replace(/\/\d+(?=\/|$)/g, '/:id')}`;
        counts[key] = (counts[key] || 0) + 1;
        return counts;
      }, {});
      if (failure) evidence.passed = false;
      mkdirSync(dirname(evidencePath), { recursive: true });
      writeFileSync(evidencePath, JSON.stringify(evidence, null, 2) + '\n', { mode: 0o600 });
    }
    // Do not serialize token-bearing transport error objects in test diagnostics.
    if (failure) throw new Error(`${stage}: ${safeFailure(failure).message}`);
    expect(evidence.passed).toBe(true);
    expect(evidence.cleanup.verifiedAbsent).toBe(true);
  });
});
