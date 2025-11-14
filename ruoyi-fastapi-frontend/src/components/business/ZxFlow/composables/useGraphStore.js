import { useGraphStore as usePiniaGraphStore } from '../stores/graphStore'
import { computed, getCurrentInstance } from 'vue'

// 导出 Pinia store 的便捷封装
export function useGraphStore(selector) {
  // 检查是否在 Vue 组件上下文中
  const instance = getCurrentInstance()
  if (!instance) {
    throw new Error(
      'useGraphStore can only be used inside a Vue component setup function or lifecycle hooks.'
    )
  }

  const store = usePiniaGraphStore()

  if (!store) {
    throw new Error(
      'useGraphStore: Pinia store is not available. Make sure Pinia is properly installed and configured.'
    )
  }

  // 如果提供了选择器函数，返回计算属性
  if (selector && typeof selector === 'function') {
    return computed(() => selector(store))
  }

  // 否则返回整个 store
  return store
}
