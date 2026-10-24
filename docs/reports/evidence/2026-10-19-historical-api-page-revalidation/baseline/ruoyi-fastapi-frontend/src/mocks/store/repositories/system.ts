import type { MockDepartment, MockDictData, MockMenu, MockRole } from '../../data';

export interface MockSystemRepository {
  listMenus(): Promise<MockMenu[]>;
  listRoles(): Promise<MockRole[]>;
  listDictData(dictType?: string): Promise<MockDictData[]>;
  listDepartments(): Promise<MockDepartment[]>;
}
