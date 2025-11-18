<template>
  <!-- 这个组件不需要渲染任何内容，只是用来处理图实例初始化 -->
</template>

<script>
import { defineComponent, onMounted, inject } from 'vue'
import { useOptionalGraphInstance } from '../../ZxFlow/composables/useGraphInstance'
import { useContextMenu } from '../../ZxFlow/composables/useContextMenu'
import { useClipboard } from '../../ZxFlow/composables/useClipboard'
import { useHistory } from '../../ZxFlow/composables/useHistory'

export default defineComponent({
  name: 'DagGraphHandler',
  props: {
    selectionHandler: {
      type: Object,
      required: true
    },
    customMenuItems: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['graph-ready', 'context-menu-ready'],
  setup(props, { emit }) {
    onMounted(() => {
      try {
        // 获取图实例
        const graph = useOptionalGraphInstance()
        console.log('DagGraphHandler: Graph instance obtained:', graph)

        // 初始化右键菜单
        console.log('DagGraphHandler: customMenuItems received:', props.customMenuItems)
        const contextMenuHandler = useContextMenu(graph, {
          enabled: true,
          enableBlankMenu: true,
          enableNodeMenu: true,
          enableEdgeMenu: true,
          customItems: props.customMenuItems
        })
        console.log('DagGraphHandler: contextMenuHandler created:', contextMenuHandler)

        // 初始化剪贴板和历史记录处理器
        const clipboardHandler = useClipboard(graph)
        const historyHandler = useHistory(graph)

        // 设置处理器
        if (contextMenuHandler.setClipboardHandler) {
          contextMenuHandler.setClipboardHandler(clipboardHandler)
        }
        if (contextMenuHandler.setHistoryHandler) {
          contextMenuHandler.setHistoryHandler(historyHandler)
        }
        if (contextMenuHandler.setSelectionHandler) {
          contextMenuHandler.setSelectionHandler(props.selectionHandler)
        }

        // 设置图形事件
        const setupEvents = () => {
          const g = graph?.value || graph
          if (g && typeof g.on === 'function') {
            if (contextMenuHandler.setupGraphEvents) {
              contextMenuHandler.setupGraphEvents(g)
            }

            // 添加连接状态管理
            const container = g.container?.parentElement || g.container
            if (container) {
              // 连接开始时添加 connecting 类
              g.on('edge:connecting', () => {
                container.classList.add('connecting')
              })

              // 连接结束时移除 connecting 类
              g.on('edge:connected', () => {
                container.classList.remove('connecting')
              })

              // 连接取消时移除 connecting 类
              g.on('edge:connection-removed', () => {
                container.classList.remove('connecting')
              })
            }

            console.log('DagGraphHandler: Graph events setup completed')

            // 通知父组件图实例已准备好
            emit('graph-ready', graph)
            emit('context-menu-ready', contextMenuHandler)
          } else {
            console.log('DagGraphHandler: Graph instance not ready, retrying...')
            setTimeout(setupEvents, 100)
          }
        }
        setupEvents()
      } catch (error) {
        console.error('DagGraphHandler: Failed to initialize:', error)
      }
    })

    return {}
  }
})
</script>
