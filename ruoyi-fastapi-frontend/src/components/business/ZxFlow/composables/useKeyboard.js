import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useGraphInstance } from './useGraphInstance'
import { useLatest } from './useLatest'

export function useKeyboard(key, callback, action = 'keydown') {
  const graph = useGraphInstance()
  const latestCallback = useLatest(callback)

  // 更新回调引用
  const updateCallback = (newCallback) => {
    latestCallback.value = newCallback
  }

  const bindKey = () => {
    if (graph && graph.value) {
      graph.value.bindKey(
        key,
        (e) => {
          if (latestCallback && latestCallback.value) {
            latestCallback.value(e)
          }
        },
        action
      )
    }
  }

  const unbindKey = () => {
    if (graph && graph.value) {
      graph.value.unbindKey(key)
    }
  }

  // 监听 graph 变化
  watch(
    graph,
    (newGraph) => {
      if (newGraph) {
        bindKey()
      }
    },
    { immediate: true }
  )

  onUnmounted(() => {
    unbindKey()
  })

  return {
    updateCallback,
    bindKey,
    unbindKey
  }
}
