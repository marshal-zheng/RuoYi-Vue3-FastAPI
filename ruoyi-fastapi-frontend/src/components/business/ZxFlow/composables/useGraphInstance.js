import { inject, provide, ref } from 'vue'

export const GRAPH_INSTANCE_KEY = Symbol('graphInstance')

// 提供 Graph 实例
export function provideGraphInstance() {
  const graph = ref(null)

  provide(GRAPH_INSTANCE_KEY, {
    graph,
    setGraph: (instance) => {
      graph.value = instance
    }
  })

  return {
    graph,
    setGraph: (instance) => {
      graph.value = instance
    }
  }
}

// 使用 Graph 实例
export function useGraphInstance(options = {}) {
  const { required = true, warnIfMissing = !required } = options
  // 传入默认值以避免 Vue 在注入缺失时输出控制台告警
  const context = inject(GRAPH_INSTANCE_KEY, null)

  if (!context) {
    if (required) {
      throw new Error('useGraphInstance must be used within XFlow component')
    }

    if (warnIfMissing && import.meta.env?.DEV) {
      console.warn('[ZxFlow] Graph instance context not found. Dag features may not work as expected.')
    }

    return ref(null)
  }

  return context.graph
}

export function useOptionalGraphInstance() {
  return useGraphInstance({ required: false, warnIfMissing: false })
}
