import tab from './tab';
import auth from './auth';
import cache from './cache';
import modal from './modal';
import download from './download';
import httpPlugin from './http';

export default function installPlugins(app) {
  // 页签操作
  app.config.globalProperties.$tab = tab;
  // 认证对象
  app.config.globalProperties.$auth = auth;
  // 缓存对象
  app.config.globalProperties.$cache = cache;
  // 模态框对象
  app.config.globalProperties.$modal = modal;
  // 下载文件
  app.config.globalProperties.$download = download;
  // HTTP 客户端
  app.use(httpPlugin);
}
