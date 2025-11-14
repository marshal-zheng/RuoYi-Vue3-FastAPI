import { computed } from 'vue'
import { useGraphInstance } from './useGraphInstance'

/**
 * 插件加载状态检测 Hook
 * 用于检查指定插件是否已加载，避免在插件未就绪时调用相关功能
 */
export function useLoaded(pluginName) {
  const graph = useGraphInstance()

  // 检查插件是否已加载
  const isLoaded = computed(() => {
    if (!graph || !graph.value) {
      return false
    }

    const plugin = graph.value.getPlugin(pluginName)
    return !!plugin
  })

  // 安全调用函数（只有在插件加载后才执行）
  const safeCall = (callback) => {
    if (!graph || !graph.value) {
      console.warn('Graph instance not available')
      return false
    }

    const plugin = graph.value.getPlugin(pluginName)
    if (!plugin) {
      console.warn(
        `Plugin ${pluginName} is not loaded. Please ensure the corresponding component is included.`
      )
      return false
    }

    if (typeof callback === 'function') {
      try {
        return callback(plugin)
      } catch (error) {
        console.error(`Error calling function for plugin ${pluginName}:`, error)
        return false
      }
    }

    return true
  }

  // 等待插件加载完成
  const waitForPlugin = (timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now()

      const check = () => {
        if (isLoaded.value) {
          resolve(graph.value.getPlugin(pluginName))
          return
        }

        if (Date.now() - startTime > timeout) {
          reject(new Error(`Plugin ${pluginName} failed to load within ${timeout}ms`))
          return
        }

        setTimeout(check, 50)
      }

      check()
    })
  }

  return {
    isLoaded,
    safeCall,
    waitForPlugin
  }
}
