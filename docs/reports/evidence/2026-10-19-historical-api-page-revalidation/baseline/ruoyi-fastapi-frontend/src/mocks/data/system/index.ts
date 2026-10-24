import type { SystemMockData } from '../types';
import { mockDepartments } from './depts';
import { mockDicts } from './dicts';
import { mockMenus } from './menus';

export const systemMockData = {
  menus: mockMenus,
  dicts: mockDicts,
  departments: mockDepartments,
} satisfies SystemMockData;

export * from './depts';
export * from './dicts';
export * from './menus';
