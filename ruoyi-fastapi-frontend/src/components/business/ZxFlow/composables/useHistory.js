import { useGraphInstance } from './useGraphInstance'

export function useHistory(graphInstance = null) {
  let graph

  try {
    graph = graphInstance || useGraphInstance()
  } catch (error) {
    graph = graphInstance
  }

  const undo = () => {
    const g = graph?.value || graph
    if (g) {
      const history = g.getPlugin('history')
      if (history) {
        history.undo()
      }
    }
  }

  const redo = () => {
    const g = graph?.value || graph
    if (g) {
      const history = g.getPlugin('history')
      if (history) {
        history.redo()
      }
    }
  }

  const canUndo = () => {
    const g = graph?.value || graph
    if (g) {
      const history = g.getPlugin('history')
      if (history) {
        return history.canUndo()
      }
    }
    return false
  }

  const canRedo = () => {
    const g = graph?.value || graph
    if (g) {
      const history = g.getPlugin('history')
      if (history) {
        return history.canRedo()
      }
    }
    return false
  }

  const clean = () => {
    const g = graph?.value || graph
    if (g) {
      const history = g.getPlugin('history')
      if (history) {
        history.clean()
      }
    }
  }

  return {
    undo,
    redo,
    canUndo,
    canRedo,
    clean
  }
}
