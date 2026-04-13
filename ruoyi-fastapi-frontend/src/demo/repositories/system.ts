import type { DemoOfflineDb } from '@/demo/db';
import type { DemoDepartment, DemoDictData, DemoMenu } from '@/demo/scenarios';

export class SystemRepository {
  constructor(private readonly db: DemoOfflineDb) {}

  listMenus(): Promise<DemoMenu[]> {
    return this.db.menus.toArray();
  }

  listMenusByRole(roleKey: string): Promise<DemoMenu[]> {
    return this.db.menus
      .filter((menu) => menu.roles.length === 0 || menu.roles.includes(roleKey))
      .toArray();
  }

  listDictsByType(dictType: string): Promise<DemoDictData[]> {
    return this.db.dicts.where('dictType').equals(dictType).sortBy('dictSort');
  }

  listDepartments(): Promise<DemoDepartment[]> {
    return this.db.departments.toArray();
  }
}
