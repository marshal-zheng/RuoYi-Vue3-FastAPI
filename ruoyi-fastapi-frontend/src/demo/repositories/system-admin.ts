import type { DemoOfflineDb } from '@/demo/db';
import type {
  DemoAccount,
  DemoDepartment,
  DemoDictData,
  DemoDictType,
  DemoMenu,
  DemoPost,
  DemoRole,
  DemoSystemUser,
} from '@/demo/scenarios';

export class SystemAdminRepository {
  constructor(private readonly db: DemoOfflineDb) {}

  get database(): DemoOfflineDb {
    return this.db;
  }

  listUsers(): Promise<DemoSystemUser[]> {
    return this.db.systemUsers.toArray();
  }

  getUser(userId: number): Promise<DemoSystemUser | undefined> {
    return this.db.systemUsers.get(userId);
  }

  getUserByUsername(userName: string): Promise<DemoSystemUser | undefined> {
    return this.db.systemUsers.where('userName').equals(userName).first();
  }

  saveUser(user: DemoSystemUser): Promise<number> {
    return this.db.systemUsers.put(user);
  }

  deleteUsers(userIds: number[]): Promise<void> {
    return this.db.systemUsers.bulkDelete(userIds);
  }

  listRoles(): Promise<DemoRole[]> {
    return this.db.roles.toArray();
  }

  getRole(roleId: number): Promise<DemoRole | undefined> {
    return this.db.roles.get(roleId);
  }

  saveRole(role: DemoRole): Promise<number> {
    return this.db.roles.put(role);
  }

  deleteRoles(roleIds: number[]): Promise<void> {
    return this.db.roles.bulkDelete(roleIds);
  }

  listPosts(): Promise<DemoPost[]> {
    return this.db.posts.toArray();
  }

  getPost(postId: number): Promise<DemoPost | undefined> {
    return this.db.posts.get(postId);
  }

  savePost(post: DemoPost): Promise<number> {
    return this.db.posts.put(post);
  }

  listMenus(): Promise<DemoMenu[]> {
    return this.db.menus.toArray();
  }

  getMenu(menuId: number): Promise<DemoMenu | undefined> {
    return this.db.menus.get(menuId);
  }

  saveMenu(menu: DemoMenu): Promise<number> {
    return this.db.menus.put(menu);
  }

  deleteMenus(menuIds: number[]): Promise<void> {
    return this.db.menus.bulkDelete(menuIds);
  }

  listDepartments(): Promise<DemoDepartment[]> {
    return this.db.departments.toArray();
  }

  getDepartment(deptId: number): Promise<DemoDepartment | undefined> {
    return this.db.departments.get(deptId);
  }

  saveDepartment(department: DemoDepartment): Promise<number> {
    return this.db.departments.put(department);
  }

  deleteDepartments(deptIds: number[]): Promise<void> {
    return this.db.departments.bulkDelete(deptIds);
  }

  listDictTypes(): Promise<DemoDictType[]> {
    return this.db.dictTypes.toArray();
  }

  getDictType(dictId: number): Promise<DemoDictType | undefined> {
    return this.db.dictTypes.get(dictId);
  }

  getDictTypeByType(dictType: string): Promise<DemoDictType | undefined> {
    return this.db.dictTypes.where('dictType').equals(dictType).first();
  }

  saveDictType(dictType: DemoDictType): Promise<number> {
    return this.db.dictTypes.put(dictType);
  }

  deleteDictTypes(dictIds: number[]): Promise<void> {
    return this.db.dictTypes.bulkDelete(dictIds);
  }

  listDictData(): Promise<DemoDictData[]> {
    return this.db.dicts.toArray();
  }

  getDictData(dictCode: number): Promise<DemoDictData | undefined> {
    return this.db.dicts.get(dictCode);
  }

  saveDictData(dictData: DemoDictData): Promise<number> {
    return this.db.dicts.put(dictData);
  }

  deleteDictData(dictCodes: number[]): Promise<void> {
    return this.db.dicts.bulkDelete(dictCodes);
  }

  listAccounts(): Promise<DemoAccount[]> {
    return this.db.accounts.toArray();
  }

  getAccountByUsername(username: string): Promise<DemoAccount | undefined> {
    return this.db.accounts.get(username);
  }

  getAccountByUserId(userId: number): Promise<DemoAccount | undefined> {
    return this.db.accounts.where('userId').equals(userId).first();
  }

  saveAccount(account: DemoAccount): Promise<string> {
    return this.db.accounts.put(account);
  }

  deleteAccounts(usernames: string[]): Promise<void> {
    return this.db.accounts.bulkDelete(usernames);
  }
}
