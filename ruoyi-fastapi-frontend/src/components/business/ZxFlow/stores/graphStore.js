import { defineStore } from 'pinia'
import { StringExt } from '@antv/x6'

// 命令类型定义
export const COMMANDS = {
  INIT: 'init',
  ADD_NODES: 'addNodes',
  REMOVE_NODES: 'removeNodes',
  UPDATE_NODE: 'updateNode',
  ADD_EDGES: 'addEdges',
  REMOVE_EDGES: 'removeEdges',
  UPDATE_EDGE: 'updateEdge'
}

// 工具函数：深度合并对象
function apply(target, source) {
  if (!source) return target

  Object.keys(source).forEach((key) => {
    if (source[key] !== null && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      if (!target[key] || typeof target[key] !== 'object') {
        target[key] = {}
      }
      apply(target[key], source[key])
    } else {
      target[key] = source[key]
    }
  })

  return target
}

export const useGraphStore = defineStore('graph', {
  state: () => ({
    nodes: [],
    edges: [],
    changeList: []
  }),

  actions: {
    initData(data, options = {}) {
      this.nodes = data.nodes || []
      this.edges = data.edges || []

      if (!options.silent) {
        this.changeList.push({
          command: COMMANDS.INIT,
          data
        })
      }
    },

    addNodes(ns, options = {}) {
      if (!ns || !ns.length) return

      // 生成节点 ID
      ns.forEach((n) => {
        if (!n.id) {
          n.id = StringExt.uuid()
        }
      })

      // 检查重复 ID
      const duplicated = this.nodes.find((n) => ns.some((m) => m.id && m.id === n.id))

      if (!duplicated) {
        this.nodes.push(...ns)
        if (!options.silent) {
          this.changeList.push({
            command: COMMANDS.ADD_NODES,
            data: ns
          })
        }
      } else {
        console.error(`node id=${duplicated.id} already existed`)
      }
    },

    removeNodes(ids, options = {}) {
      if (!ids || !ids.length) return

      this.nodes = this.nodes.filter((n) => !ids.includes(n.id))

      if (!options.silent) {
        this.changeList.push({
          command: COMMANDS.REMOVE_NODES,
          data: ids
        })
      }
    },

    updateNode(id, data, options = {}) {
      const node = this.nodes.find((n) => n.id === id)
      if (node) {
        const changed = typeof data === 'function' ? data({ ...node }) : data

        if (changed.id !== undefined || changed.shape !== undefined) {
          console.error(`id and shape can't be changed`)
          return
        }

        apply(node, changed)

        if (!options.silent) {
          this.changeList.push({
            command: COMMANDS.UPDATE_NODE,
            data: { id, data: changed }
          })
        }
      }
    },

    addEdges(es, options = {}) {
      if (!es || !es.length) return

      // 生成边 ID
      es.forEach((e) => {
        if (!e.id) {
          e.id = StringExt.uuid()
        }
      })

      // 检查重复 ID
      const duplicated = this.edges.find((e) => es.some((m) => m.id && m.id === e.id))

      if (!duplicated) {
        this.edges.push(...es)
        if (!options.silent) {
          this.changeList.push({
            command: COMMANDS.ADD_EDGES,
            data: es
          })
        }
      } else {
        console.error(`edge id=${duplicated.id} already existed`)
      }
    },

    removeEdges(ids, options = {}) {
      if (!ids || !ids.length) return

      this.edges = this.edges.filter((n) => !ids.includes(n.id))

      if (!options.silent) {
        this.changeList.push({
          command: COMMANDS.REMOVE_EDGES,
          data: ids
        })
      }
    },

    updateEdge(id, data, options = {}) {
      const edge = this.edges.find((n) => n.id === id)
      if (edge) {
        const changed = typeof data === 'function' ? data({ ...edge }) : data

        if (changed.id !== undefined || changed.shape !== undefined) {
          console.error(`id and shape can't be changed`)
          return
        }

        apply(edge, changed)

        if (!options.silent) {
          this.changeList.push({
            command: COMMANDS.UPDATE_EDGE,
            data: { id, data: changed }
          })
        }
      }
    },

    clearChangeList() {
      this.changeList = []
    },

    // 批量更新方法（支持函数式更新）
    $patch(updater) {
      if (typeof updater === 'function') {
        const currentState = {
          nodes: [...this.nodes],
          edges: [...this.edges],
          changeList: [...this.changeList]
        }
        const newState = updater(currentState)

        if (newState.nodes) this.nodes = newState.nodes
        if (newState.edges) this.edges = newState.edges
        if (newState.changeList) this.changeList = newState.changeList
      } else {
        // 对象式更新
        if (updater.nodes) this.nodes = updater.nodes
        if (updater.edges) this.edges = updater.edges
        if (updater.changeList) this.changeList = updater.changeList
      }
    }
  },

  getters: {
    getNodeById: (state) => (id) => {
      return state.nodes.find((node) => node.id === id)
    },

    getEdgeById: (state) => (id) => {
      return state.edges.find((edge) => edge.id === id)
    },

    getAllNodes: (state) => state.nodes,

    getAllEdges: (state) => state.edges,

    getChangeList: (state) => state.changeList
  }
})
