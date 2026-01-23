/**
 * HTTP 全局插件
 *
 * 使用方式：
 * - Options API: this.$http.get({ url: '/api/xxx' })
 * - Composition API: const $http = inject('$http')
 * - 直接导入: import { http } from '@/utils/http'
 */
import type { App, InjectionKey } from 'vue';
import { http, type HttpClientImpl } from '@/utils/http';

// 注入 key，用于 Composition API
export const HTTP_KEY: InjectionKey<HttpClientImpl> = Symbol('$http');

export default {
  install(app: App) {
    // 注册全局属性（Options API）
    app.config.globalProperties.$http = http;

    // 注册 provide（Composition API）
    app.provide(HTTP_KEY, http);
    app.provide('$http', http);
  },
};

// 导出 http 实例
export { http };
