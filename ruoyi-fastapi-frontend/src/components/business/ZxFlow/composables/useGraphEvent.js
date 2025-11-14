import { isRef, onMounted, onUnmounted, ref, watch } from 'vue'
import { useGraphInstance } from './useGraphInstance'
import { useLatest } from './useLatest'

export function useGraphEvent(eventName, callback, graphRef) {
  const resolvedGraph = graphRef ? (isRef(graphRef) ? graphRef : ref(graphRef)) : null
  const graph = resolvedGraph || useGraphInstance()
  const latestCallback = useLatest(callback)
  const handler = (...args) => {
    if (latestCallback && latestCallback.value) {
      latestCallback.value(...args)
    }
  }

  let stopWatch = null

  const bind = (instance) => {
    if (instance && instance.on) {
      instance.on(eventName, handler)
    }
  }

  const unbind = (instance) => {
    if (instance && instance.off) {
      instance.off(eventName, handler)
    }
  }

  onMounted(() => {
    if (!graph) return

    stopWatch = watch(
      () => graph.value,
      (next, prev) => {
        if (prev && prev !== next) {
          unbind(prev)
        }
        if (next) {
          bind(next)
        }
      },
      { immediate: true }
    )
  })

  onUnmounted(() => {
    if (stopWatch) {
      stopWatch()
      stopWatch = null
    }

    if (graph && graph.value) {
      unbind(graph.value)
    }
  })

  return {
    graph
  }
}
