import { onBeforeUnmount, ref, onMounted, watch, inject, isRef } from 'vue'
import { Dnd } from '@antv/x6-plugin-dnd'
import { GRAPH_INSTANCE_KEY } from './useGraphInstance'

export function useDnd(arg1 = null, arg2 = {}) {
  let graphRef = null
  let options

  const isGraphInstance = (candidate) =>
    !!candidate && typeof candidate?.createNode === 'function'

  const isGraphLike = (g) => {
    if (!g) return false
    if (typeof g === 'function') {
      try {
        const val = g()
        if (val == null) {
          return true
        }
        return isGraphInstance(val)
      } catch {
        // Treat function resolvers as lazy graph providers even if they throw for now
        return true
      }
    }
    if (isRef(g)) {
      const val = g.value
      if (val == null) {
        return true
      }
      return isGraphInstance(val)
    }
    return isGraphInstance(g)
  }

  if (isGraphLike(arg1)) {
    graphRef = arg1
    options = arg2 || {}
    console.log('[useDnd] Using provided graph instance')
  } else {
    options = arg1 || {}
    // 延迟获取 graph - 在 Vue setup 上下文中通过 inject 获取
    try {
      const context = inject(GRAPH_INSTANCE_KEY, null)
      if (context && context.graph) {
        graphRef = context.graph
        console.log('[useDnd] Got graph from inject:', {
          isRef: !!graphRef?.__v_isRef,
          hasValue: !!graphRef?.value,
          valueType: graphRef?.value?.constructor?.name
        })
      } else {
        console.log('[useDnd] No graph context available yet, will wait for it')
        graphRef = ref(null)
      }
    } catch (e) {
      console.log('[useDnd] inject failed (not in setup context), creating empty ref')
      graphRef = ref(null)
    }
  }

  // 确保 graphRef 始终是一个 ref
  if (!graphRef) {
    console.log('[useDnd] graphRef is null, creating empty ref')
    graphRef = ref(null)
  }

  const dndRef = ref(null)

  const resolveGraphInstance = (candidate, depth = 0) => {
    if (!candidate || depth > 5) {
      return null
    }

    if (typeof candidate?.createNode === 'function') {
      return candidate
    }

    if (candidate?.value && candidate.value !== candidate) {
      return resolveGraphInstance(candidate.value, depth + 1)
    }

    return null
  }

  const readGraphSource = () => {
    if (!graphRef) return null
    if (typeof graphRef === 'function') {
      try {
        return graphRef()
      } catch (error) {
        console.log('[useDnd] readGraphSource: graph resolver threw error:', error)
        return null
      }
    }
    if (isRef(graphRef)) {
      return graphRef.value
    }
    return graphRef
  }

  const describeGraphCandidate = () => {
    const source = readGraphSource()
    if (!source) {
      if (typeof graphRef === 'function') {
        return 'function'
      }
      if (isRef(graphRef)) {
        return 'null'
      }
      return 'null'
    }
    return source.constructor?.name ?? typeof source
  }

  const getGraph = () => {
    if (!graphRef) {
      console.log('[useDnd] getGraph: graphRef is null/undefined')
      return null
    }
    if (typeof graphRef === 'function') {
      try {
        const result = graphRef()
        const resolved = resolveGraphInstance(result)
        console.log('[useDnd] getGraph: graphRef is function, result:', {
          resultType: result?.constructor?.name,
          hasCreateNode: typeof resolved?.createNode === 'function'
        })
        return resolved
      } catch (e) {
        console.log('[useDnd] getGraph: graphRef function threw error:', e)
        return null
      }
    }
    const candidate = readGraphSource()
    const resolved = resolveGraphInstance(candidate ?? graphRef)
    console.log('[useDnd] getGraph: returning graphRef.value or graphRef:', {
      hasValue: isRef(graphRef) ? graphRef.value != null : undefined,
      candidateType: candidate?.constructor?.name ?? typeof candidate,
      hasCreateNode: typeof resolved?.createNode === 'function'
    })
    if (!resolved) {
      console.log('[useDnd] getGraph: graph instance not ready (missing createNode)')
    }
    return resolved
  }

  const ensureInit = () => {
    const g = getGraph()
    console.log('[useDnd] ensureInit called - graph:', !!g, 'dndRef:', !!dndRef.value)
    if (g && !dndRef.value) {
      console.log('[useDnd] Initializing DnD with graph:', g?.constructor?.name)
      try {
        dndRef.value = new Dnd({
          target: g,
          scaled: false,
          animation: false,
          validateNode() {
            return true
          },
          getDragNode: (node) => node.clone(),
          getDropNode: (node) => node.clone(),
          ...options
        })
        console.log('[useDnd] DnD initialized successfully')
      } catch (error) {
        console.error('[useDnd] Failed to initialize DnD:', error)
      }
    } else if (!g) {
      console.log('[useDnd] Cannot initialize DnD: graph not available')
    } else if (dndRef.value) {
      console.log('[useDnd] DnD already initialized')
    }
  }

  onMounted(() => {
    console.log('[useDnd] onMounted - checking if graph is ready')
    ensureInit()
  })

  // 惰性监听 graph 的可用性
  const shouldWatchGraph =
    graphRef && typeof watch === 'function' && (isRef(graphRef) || typeof graphRef === 'function')

  if (shouldWatchGraph) {
    watch(
      () => readGraphSource(),
      (newGraph) => {
        console.log('[useDnd] Graph changed:', {
          hasGraph: !!newGraph,
          type: newGraph?.constructor?.name,
          hasCreateNode: typeof newGraph?.createNode === 'function'
        })
        if (newGraph && typeof newGraph.createNode === 'function') {
          console.log('[useDnd] Graph became available, initializing DnD...')
          ensureInit()
        }
      },
      { immediate: true }
    )
  }

  let pendingStart = null
  let stopPendingWatch = null
  let pendingTimeout = null

  const clearPending = () => {
    pendingStart = null
    if (stopPendingWatch) {
      stopPendingWatch()
      stopPendingWatch = null
    }
    if (pendingTimeout) {
      clearTimeout(pendingTimeout)
      pendingTimeout = null
    }
  }

  const runStart = (nodeOptions, event) => {
    const g = getGraph()
    console.log('[useDnd] runStart called - graph available:', !!g, 'hasCreateNode:', typeof g?.createNode === 'function')
    if (!g || typeof g.createNode !== 'function') {
      console.log('[useDnd] No valid graph instance available')
      return 'no-graph'
    }
    if (!dndRef.value) {
      console.log('[useDnd] DnD not initialized, initializing now...')
      ensureInit()
    }
    if (!dndRef.value) {
      console.error('[useDnd] Failed to initialize DnD even after ensureInit')
      return 'no-dnd'
    }

    try {
      const node = g.createNode(nodeOptions)
      console.log('[useDnd] Created node for drag:', node?.id)
      dndRef.value.start(node, event)
      console.log('[useDnd] DnD started successfully')
      return 'success'
    } catch (error) {
      console.error('[useDnd] Error in runStart:', error)
      return 'error'
    }
  }

  const startDrag = (nodeOptions, event) => {
    console.log('[useDnd] startDrag called')
    const result = runStart(nodeOptions, event)
    if (result === 'success' || result === 'error') {
      clearPending()
      return
    }

    if (result !== 'no-graph' && result !== 'no-dnd') {
      return
    }

    console.warn('[useDnd] Graph not ready for DnD, waiting for availability...')
    console.log('[useDnd] Current graph state:', describeGraphCandidate())
    pendingStart = { nodeOptions, event }

    // 设置 watch 监听 graphRef 和 dndRef 的变化
    if (!stopPendingWatch && shouldWatchGraph) {
      console.log('[useDnd] Setting up watch for pending drag operation...')
      stopPendingWatch = watch(
        () => [readGraphSource(), dndRef.value],
        ([graphValue, dnd]) => {
          if (!pendingStart) return
          console.log('[useDnd] Watch triggered - graph:', !!graphValue, 'dnd:', !!dnd)
          const status = runStart(pendingStart.nodeOptions, pendingStart.event)
          if (status === 'success' || status === 'error') {
            clearPending()
          }
        },
        { immediate: true }
      )
    }

    // 设置超时机制作为备选方案
    if (pendingTimeout) {
      clearTimeout(pendingTimeout)
    }
    pendingTimeout = setTimeout(() => {
      if (!pendingStart) return
      console.log('[useDnd] Timeout reached, trying one last time...')
      const status = runStart(pendingStart.nodeOptions, pendingStart.event)
      if (status !== 'success') {
        console.error('[useDnd] No graph available for DnD after waiting 3000ms')
        console.log('[useDnd] Final graph state:', describeGraphCandidate())
      }
      clearPending()
    }, 3000)
  }

  onBeforeUnmount(() => {
    clearPending()
  })

  return {
    startDrag
  }
}
