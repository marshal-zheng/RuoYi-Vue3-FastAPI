import { describe, expect, it } from 'vitest';

import { mockDataset } from '../data';

describe('auth mock invariants', () => {
  it('keeps account usernames and role keys unique', () => {
    const usernames = mockDataset.auth.accounts.map((account) => account.username);
    const roleKeys = mockDataset.auth.roles.map((role) => role.roleKey);

    expect(new Set(usernames).size).toBe(usernames.length);
    expect(new Set(roleKeys).size).toBe(roleKeys.length);
  });

  it('keeps account role and permission references valid', () => {
    const roles = new Map(mockDataset.auth.roles.map((role) => [role.roleKey, role]));

    mockDataset.auth.accounts.forEach((account) => {
      expect(account.username).toBeTruthy();
      expect(account.password).toBeTruthy();
      expect(['0', '1']).toContain(account.status);
      account.roles.forEach((roleKey) => expect(roles.has(roleKey)).toBe(true));
      account.permissions.forEach((permission) => {
        const covered =
          permission === '*:*:*' ||
          account.roles.some((roleKey) => roles.get(roleKey)?.permissions.includes(permission));
        expect(covered).toBe(true);
      });
    });
  });
});
