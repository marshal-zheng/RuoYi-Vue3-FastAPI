import { describe, expect, it } from 'vitest';

import { mockDataset } from '../data';

describe('system mock invariants', () => {
  it('keeps menu, dict, and department keys unique', () => {
    const menuIds = mockDataset.system.menus.map((menu) => menu.menuId);
    const dictKeys = mockDataset.system.dicts.map((dict) => `${dict.dictType}:${dict.dictValue}`);
    const deptIds = mockDataset.system.departments.map((department) => department.deptId);

    expect(new Set(menuIds).size).toBe(menuIds.length);
    expect(new Set(dictKeys).size).toBe(dictKeys.length);
    expect(new Set(deptIds).size).toBe(deptIds.length);
  });

  it('keeps menu parent and role references valid', () => {
    const menuIds = new Set(mockDataset.system.menus.map((menu) => menu.menuId));
    const roleKeys = new Set(mockDataset.auth.roles.map((role) => role.roleKey));

    mockDataset.system.menus.forEach((menu) => {
      expect(['M', 'C', 'F']).toContain(menu.menuType);
      expect(['0', '1']).toContain(menu.status);
      if (menu.parentId !== 0) {
        expect(menuIds.has(menu.parentId)).toBe(true);
      }
      menu.roles?.forEach((roleKey) => expect(roleKeys.has(roleKey)).toBe(true));
    });
  });

  it('keeps department parent references valid', () => {
    const deptIds = new Set<number>(
      mockDataset.system.departments.map((department) => department.deptId)
    );

    mockDataset.system.departments.forEach((department) => {
      expect(department.deptName).toBeTruthy();
      expect(['0', '1']).toContain(department.status);
      if (department.parentId !== 0) {
        expect(deptIds.has(department.parentId)).toBe(true);
      }
    });
  });
});
