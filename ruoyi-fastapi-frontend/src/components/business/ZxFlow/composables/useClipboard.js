import { useGraphInstance } from './useGraphInstance'

export function useClipboard(graphInstance = null) {
  let graph

  try {
    graph = graphInstance || useGraphInstance()
  } catch (error) {
    graph = graphInstance
  }

  const copy = (cells) => {
    const g = graph?.value || graph
    if (g) {
      const clipboard = g.getPlugin('clipboard')
      if (clipboard) {
        clipboard.copy(cells || g.getSelectedCells())
      }
    }
  }

  const paste = (options = {}) => {
    const g = graph?.value || graph
    if (g) {
      const clipboard = g.getPlugin('clipboard')
      if (clipboard) {
        // 默认配置确保粘贴的节点有新的ID
        const defaultOptions = {
          offset: 20,
          ...options
        }
        return clipboard.paste(defaultOptions)
      }
    }
    return []
  }

  const cut = (cells) => {
    const g = graph?.value || graph
    if (g) {
      const clipboard = g.getPlugin('clipboard')
      if (clipboard) {
        clipboard.cut(cells || g.getSelectedCells())
      }
    }
  }

  const isEmpty = () => {
    const g = graph?.value || graph
    if (g) {
      const clipboard = g.getPlugin('clipboard')
      if (clipboard) {
        return clipboard.isEmpty()
      }
    }
    return true
  }

  return {
    copy,
    paste,
    cut,
    isEmpty
  }
}
