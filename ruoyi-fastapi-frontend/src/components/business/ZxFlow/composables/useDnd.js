import { onBeforeUnmount, ref, onMounted, watch, inject, isRef } from 'vue';
import { ElMessage } from 'element-plus';
import { Dnd } from '@antv/x6-plugin-dnd';
import { GRAPH_INSTANCE_KEY } from './useGraphInstance';

export function useDnd(arg1 = null, arg2 = {}) {
  let graphRef = null;
  let options;

  const isGraphInstance = (candidate) => !!candidate && typeof candidate?.createNode === 'function';

  const isGraphLike = (g) => {
    if (!g) return false;
    if (typeof g === 'function') {
      try {
        const val = g();
        if (val == null) {
          return true;
        }
        return isGraphInstance(val);
      } catch {
        // Treat function resolvers as lazy graph providers even if they throw for now
        return true;
      }
    }
    if (isRef(g)) {
      const val = g.value;
      if (val == null) {
        return true;
      }
      return isGraphInstance(val);
    }
    return isGraphInstance(g);
  };

  if (isGraphLike(arg1)) {
    graphRef = arg1;
    options = arg2 || {};
  } else {
    options = arg1 || {};
    // 延迟获取 graph - 在 Vue setup 上下文中通过 inject 获取
    try {
      const context = inject(GRAPH_INSTANCE_KEY, null);
      if (context && context.graph) {
        graphRef = context.graph;
      } else {
        graphRef = ref(null);
      }
    } catch {
      graphRef = ref(null);
    }
  }

  // 确保 graphRef 始终是一个 ref
  if (!graphRef) {
    graphRef = ref(null);
  }

  const dndRef = ref(null);

  const resolveGraphInstance = (candidate, depth = 0) => {
    if (!candidate || depth > 5) {
      return null;
    }

    if (typeof candidate?.createNode === 'function') {
      return candidate;
    }

    if (candidate?.value && candidate.value !== candidate) {
      return resolveGraphInstance(candidate.value, depth + 1);
    }

    return null;
  };

  const readGraphSource = () => {
    if (!graphRef) return null;
    if (typeof graphRef === 'function') {
      try {
        return graphRef();
      } catch {
        return null;
      }
    }
    if (isRef(graphRef)) {
      return graphRef.value;
    }
    return graphRef;
  };

  const getGraph = () => {
    if (!graphRef) {
      return null;
    }
    if (typeof graphRef === 'function') {
      try {
        const result = graphRef();
        const resolved = resolveGraphInstance(result);

        return resolved;
      } catch {
        return null;
      }
    }
    const candidate = readGraphSource();
    const resolved = resolveGraphInstance(candidate ?? graphRef);

    return resolved;
  };

  const ensureInit = () => {
    const g = getGraph();

    if (g && !dndRef.value) {
      try {
        dndRef.value = new Dnd({
          target: g,
          scaled: false,
          animation: false,
          validateNode() {
            return true;
          },
          getDragNode: (node) => node.clone(),
          getDropNode: (node) => node.clone(),
          ...options,
        });
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : '拖拽插件初始化失败');
      }
    }
  };

  onMounted(() => {
    ensureInit();
  });

  // 惰性监听 graph 的可用性
  const shouldWatchGraph =
    graphRef && typeof watch === 'function' && (isRef(graphRef) || typeof graphRef === 'function');

  if (shouldWatchGraph) {
    watch(
      () => readGraphSource(),
      (newGraph) => {
        if (newGraph && typeof newGraph.createNode === 'function') {
          ensureInit();
        }
      },
      { immediate: true }
    );
  }

  let pendingStart = null;
  let stopPendingWatch = null;
  let pendingTimeout = null;

  const clearPending = () => {
    pendingStart = null;
    if (stopPendingWatch) {
      stopPendingWatch();
      stopPendingWatch = null;
    }
    if (pendingTimeout) {
      clearTimeout(pendingTimeout);
      pendingTimeout = null;
    }
  };

  const runStart = (nodeOptions, event) => {
    const g = getGraph();

    if (!g || typeof g.createNode !== 'function') {
      return 'no-graph';
    }
    if (!dndRef.value) {
      ensureInit();
    }
    if (!dndRef.value) {
      // 初始化已报告错误，保持 no-dnd 状态以便等待下一次 ready。
      return 'no-dnd';
    }

    try {
      const node = g.createNode(nodeOptions);

      dndRef.value.start(node, event);

      return 'success';
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '拖拽操作失败');
      return 'error';
    }
  };

  const startDrag = (nodeOptions, event) => {
    const result = runStart(nodeOptions, event);
    if (result === 'success' || result === 'error') {
      clearPending();
      return;
    }

    if (result !== 'no-graph' && result !== 'no-dnd') {
      return;
    }

    // 按现有惰性契约排队，等待图实例或拖拽插件就绪。

    pendingStart = { nodeOptions, event };

    // 设置 watch 监听 graphRef 和 dndRef 的变化
    if (!stopPendingWatch && shouldWatchGraph) {
      stopPendingWatch = watch(
        () => [readGraphSource(), dndRef.value],
        () => {
          if (!pendingStart) return;

          const status = runStart(pendingStart.nodeOptions, pendingStart.event);
          if (status === 'success' || status === 'error') {
            clearPending();
          }
        },
        { immediate: true }
      );
    }

    // 设置超时机制作为备选方案
    if (pendingTimeout) {
      clearTimeout(pendingTimeout);
    }
    pendingTimeout = setTimeout(() => {
      if (!pendingStart) return;

      const status = runStart(pendingStart.nodeOptions, pendingStart.event);
      if (status !== 'success') {
        ElMessage.error('画布尚未就绪，请稍后重试拖拽');
      }
      clearPending();
    }, 3000);
  };

  onBeforeUnmount(() => {
    clearPending();
  });

  return {
    startDrag,
  };
}
