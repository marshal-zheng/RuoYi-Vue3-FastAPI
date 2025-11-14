/**
 * 键盘管理器组合式函数
 * 基于企业级最佳实践，提供完整的键盘事件管理
 */

import { ref, onUnmounted } from 'vue'
import { createKeyboardManager, INTERACTION_MODES } from '../graph/keyboardManager'

export function useKeyboardManager(graph, options = {}) {
  const keyboardManager = ref(null)
  const currentMode = ref(INTERACTION_MODES.PAN)

  // 初始化键盘管理器
  const initKeyboardManager = () => {
    if (!graph || !graph.value) return

    keyboardManager.value = createKeyboardManager(graph.value, options)
    return keyboardManager.value
  }

  // 设置交互模式
  const setInteractionMode = (mode) => {
    if (keyboardManager.value) {
      keyboardManager.value.setInteractionMode(mode)
      currentMode.value = mode
    }
  }

  // 注册剪贴板处理器
  const setClipboardHandler = (handler) => {
    if (keyboardManager.value) {
      keyboardManager.value.setClipboardHandler(handler)
    }
  }

  // 注册历史处理器
  const setHistoryHandler = (handler) => {
    if (keyboardManager.value) {
      keyboardManager.value.setHistoryHandler(handler)
    }
  }

  // 注册自定义动作
  const registerAction = (action, handler) => {
    if (keyboardManager.value) {
      keyboardManager.value.registerAction(action, handler)
    }
  }

  // 获取当前模式
  const getCurrentMode = () => currentMode.value

  // 检查空格键状态
  const isSpacePressed = () => {
    return keyboardManager.value?.spacePressed || false
  }

  // 组件销毁时清理
  onUnmounted(() => {
    if (keyboardManager.value) {
      keyboardManager.value.destroy()
    }
  })

  return {
    keyboardManager,
    currentMode,
    initKeyboardManager,
    setInteractionMode,
    setClipboardHandler,
    setHistoryHandler,
    registerAction,
    getCurrentMode,
    isSpacePressed,
    INTERACTION_MODES
  }
}

// 导出交互模式常量
export { INTERACTION_MODES }
