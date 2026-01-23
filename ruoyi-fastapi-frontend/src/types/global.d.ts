/**
 * 全局类型声明
 */
import type { HttpClientImpl } from '@zxio/http';

// 扩展 Vue 组件自定义属性
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    /** HTTP 客户端 - @zxio/http */
    $http: HttpClientImpl;
  }
}

export {};
