import { computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useGraphInstance } from './useGraphInstance';

/**
 * 插件加载状态检测 Hook
 * 用于检查指定插件是否已加载，避免在插件未就绪时调用相关功能
 */
export function useLoaded(pluginName) {
  const graph = useGraphInstance();

  // 检查插件是否已加载
  const isLoaded = computed(() => {
    if (!graph || !graph.value) {
      return false;
    }

    const plugin = graph.value.getPlugin(pluginName);
    return !!plugin;
  });

  // 安全调用函数（只有在插件加载后才执行）
  const safeCall = (callback) => {
    if (!graph || !graph.value) {
      // 通过 false 告知调用方图实例尚未就绪。
      return false;
    }

    const plugin = graph.value.getPlugin(pluginName);
    if (!plugin) {
      return false;
    }

    if (typeof callback === 'function') {
      try {
        return callback(plugin);
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : `图形插件 ${pluginName} 操作失败`);
        return false;
      }
    }

    return true;
  };

  // 等待插件加载完成
  const waitForPlugin = (timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const check = () => {
        if (isLoaded.value) {
          resolve(graph.value.getPlugin(pluginName));
          return;
        }

        if (Date.now() - startTime > timeout) {
          reject(new Error(`Plugin ${pluginName} failed to load within ${timeout}ms`));
          return;
        }

        setTimeout(check, 50);
      };

      check();
    });
  };

  return {
    isLoaded,
    safeCall,
    waitForPlugin,
  };
}
