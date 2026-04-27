import type { FeedbackRegistryEntry } from './types';

const feedbackRegistry: Record<string, FeedbackRegistryEntry> = {
  'system.user.create': { success: '新增用户成功' },
  'system.user.update': { success: '修改用户成功' },
  'system.user.delete': { success: '删除用户成功' },
  'system.user.reset-password': { success: '重置密码成功' },
  'system.user.change-status': { success: '修改用户状态成功' },
  'system.user.assign-role': { success: '分配角色成功' },
  'system.user.update-profile': { success: '修改个人信息成功' },
  'system.user.update-password': { success: '修改密码成功' },
  'system.user.upload-avatar': { success: '上传头像成功' },
  'system.user.import': { success: '导入用户完成' },

  'system.role.create': { success: '新增角色成功' },
  'system.role.update': { success: '修改角色成功' },
  'system.role.delete': { success: '删除角色成功' },
  'system.role.data-scope': { success: '修改数据权限成功' },
  'system.role.change-status': { success: '修改角色状态成功' },
  'system.role.auth-user.remove': { success: '取消用户授权成功' },
  'system.role.auth-user.assign': { success: '分配用户成功' },

  'system.menu.create': { success: '新增菜单成功' },
  'system.menu.update': { success: '修改菜单成功' },
  'system.menu.delete': { success: '删除菜单成功' },

  'system.dept.create': { success: '新增部门成功' },
  'system.dept.update': { success: '修改部门成功' },
  'system.dept.delete': { success: '删除部门成功' },

  'system.notice.create': { success: '新增通知成功' },
  'system.notice.update': { success: '修改通知成功' },
  'system.notice.delete': { success: '删除通知成功' },

  'system.dict-type.create': { success: '新增字典类型成功' },
  'system.dict-type.update': { success: '修改字典类型成功' },
  'system.dict-type.delete': { success: '删除字典类型成功' },
  'system.dict-type.refresh-cache': { success: '刷新字典缓存成功' },
  'system.dict-data.create': { success: '新增字典数据成功' },
  'system.dict-data.update': { success: '修改字典数据成功' },
  'system.dict-data.delete': { success: '删除字典数据成功' },

  'system.post.create': { success: '新增岗位成功' },
  'system.post.update': { success: '修改岗位成功' },
  'system.post.delete': { success: '删除岗位成功' },

  'system.config.create': { success: '新增参数成功' },
  'system.config.update': { success: '修改参数成功' },
  'system.config.delete': { success: '删除参数成功' },

  'monitor.online.force-logout': { success: '强退用户成功' },
  'monitor.cache.clear': { success: '清理缓存成功' },
  'monitor.audit.delete': { success: '删除审计日志成功' },
  'monitor.audit.clear': { success: '清空审计日志成功' },
  'monitor.job.create': { success: '新增任务成功' },
  'monitor.job.update': { success: '修改任务成功' },
  'monitor.job.delete': { success: '删除任务成功' },
  'monitor.job.run': { success: '执行任务成功', accepted: '任务已受理，可稍后查看执行结果' },
  'monitor.job.change-status': { success: '修改任务状态成功' },
  'monitor.job-log.clear': { success: '清空任务日志成功' },
  'monitor.operlog.delete': { success: '删除操作日志成功' },
  'monitor.operlog.clear': { success: '清空操作日志成功' },
  'monitor.logininfor.clear': { success: '清空登录日志成功' },
  'monitor.logininfor.unlock': { success: '解锁用户成功' },

  'project.project.create': { success: '新增工程成功' },
  'project.project.update': { success: '修改工程成功' },
  'project.project.delete': { success: '删除工程成功' },
  'project.project.import': { success: '导入工程完成' },
  'project.project.import-batch': { success: '批量导入工程完成' },
  'project.topology.update': { success: '保存拓扑成功' },
  'project.version.create': { success: '新增版本成功' },
  'project.version.update': { success: '修改版本成功' },
  'project.version.delete': { success: '删除版本成功' },
  'project.version.clone': { success: '克隆版本成功' },
  'project.version.lock-state': {
    success: ({ successContext }) =>
      successContext.action === 'unlock' ? '解除固化成功' : '版本固化成功',
  },
  'project.version.unlock-project': { success: '解除工程版本固化成功' },

  'device.device.create': { success: '新增设备成功' },
  'device.device.update': { success: '修改设备成功' },
  'device.device.delete': { success: '删除设备成功' },
  'device.device.clone': { success: '克隆设备成功' },
  'device.device.import-batch': { success: '批量导入设备完成' },
  'device.category.create': { success: '新增设备分类成功' },
  'device.category.update': { success: '修改设备分类成功' },
  'device.category.delete': { success: '删除设备分类成功' },

  'protocol.protocol.create': { success: '新增协议成功' },
  'protocol.protocol.update': { success: '修改协议成功' },
  'protocol.protocol.delete': { success: '删除协议成功' },
  'protocol.protocol.delete-batch': { success: '批量删除协议成功' },
  'protocol.protocol.import': { success: '导入协议完成' },
  'protocol.protocol.import-batch': { success: '批量导入协议完成' },

  'simulation.session.start': {
    success: '仿真已启动',
    accepted: '仿真启动请求已受理，可稍后查看运行状态',
  },
  'simulation.event.create': { success: '事件创建成功' },
  'simulation.event.update': { success: '事件更新成功' },
  'simulation.event.delete': { success: '事件删除成功' },
  'simulation.event.trigger': { success: '事件已触发' },
  'system.dev-menu.sync': { success: '菜单同步成功' },
  'tool.gen.update': { success: '更新生成配置成功' },
  'tool.gen.import-table': { success: '导入数据表成功' },
  'tool.gen.create-table': { success: '创建数据表成功' },
  'tool.gen.delete': { success: '删除生成表成功' },
  'tool.gen.sync-db': { success: '同步表结构成功' },
};

const warnedMissingKeys = new Set<string>();

interface RegistryRuntimeOptions {
  isDev: boolean;
  warn: (message: string) => void;
  warnedKeys?: Set<string>;
}

export const getFeedbackRegistry = (): Record<string, FeedbackRegistryEntry> => feedbackRegistry;

export const resolveFeedbackRegistryEntryWithRuntime = (
  key: string,
  { isDev, warn, warnedKeys = warnedMissingKeys }: RegistryRuntimeOptions
): FeedbackRegistryEntry => {
  const entry = feedbackRegistry[key];
  if (entry) {
    return entry;
  }

  if (isDev) {
    throw new Error(`[feedback] missing registry key: ${key}`);
  }

  if (!warnedKeys.has(key)) {
    warnedKeys.add(key);
    warn(`[feedback] missing registry key: ${key}`);
  }

  return { success: '操作成功' };
};

export const resolveFeedbackRegistryEntry = (key: string): FeedbackRegistryEntry => {
  return resolveFeedbackRegistryEntryWithRuntime(key, {
    isDev: import.meta.env.DEV,
    warn: (message) => console.warn(message),
  });
};

export const assertFeedbackRegistry = (
  registry: Record<string, FeedbackRegistryEntry> = feedbackRegistry
): void => {
  Object.entries(registry).forEach(([key, entry]) => {
    if (!entry || typeof entry !== 'object' || !('success' in entry)) {
      throw new Error(`[feedback] invalid registry entry: ${key}`);
    }
  });
};
