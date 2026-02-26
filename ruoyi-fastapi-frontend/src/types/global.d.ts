/**
 * 全局类型声明
 */
import type { HttpClientImpl } from '@zxio/http';

// 扩展 Vue 组件自定义属性
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    /** HTTP 客户端 - @zxio/http */
    $http: HttpClientImpl;
    /** 字典 */
    useDict: (...args: any[]) => any;
    /** 下载 */
    download: (...args: any[]) => any;
    /** 时间格式化 */
    parseTime: (time: any, pattern?: string) => string;
    /** 重置表单 */
    resetForm: (refName: any) => void;
    /** 树形数据 */
    handleTree: (...args: any[]) => any[];
    /** 日期范围 */
    addDateRange: (...args: any[]) => any;
    /** 字典标签 */
    selectDictLabel: (...args: any[]) => string;
    /** 字典标签（多个） */
    selectDictLabels: (...args: any[]) => string;
  }
}

export {};
