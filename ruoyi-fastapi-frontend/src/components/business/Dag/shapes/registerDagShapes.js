import { Graph } from '@antv/x6'
import { Curve, Path } from '@antv/x6-geometry'
import { register } from '@antv/x6-vue-shape'
import DagNode from './DagNode.vue'
import DevicePortNode from './DevicePortNode.vue'
import { PORT_GROUPS } from '../constants/portConfig.js'

export const DAG_NODE = 'dag-node'
export const DEVICE_PORT_NODE = 'device-port-node'
export const DAG_EDGE = 'dag-edge'
export const DAG_CONNECTOR = 'dag-connector'

let registered = false

export const registerDagShapes = () => {
  if (registered) {
    return
  }

  register({
    shape: DAG_NODE,
    width: 180,
    height: 36,
    component: DagNode,
    effect: ['data'],
    attrs: {
      body: {
        width: 180,
        height: 36
      }
    },
    ports: {
      groups: PORT_GROUPS
    }
  })

  // 注册设备端口节点（端口视觉在组件中绘制，但保留 X6 端口用于连线）
  register({
    shape: DEVICE_PORT_NODE,
    width: 190,
    height: 120,
    component: DevicePortNode,
    effect: ['data'],
    attrs: {
      body: {
        width: 190,
        height: 120
      }
    },
    ports: {
      groups: PORT_GROUPS
    }
  })

  Graph.registerConnector(
    DAG_CONNECTOR,
    (sourcePoint, targetPoint, routePoints = [], options = {}) => {
      if (routePoints && routePoints.length > 0) {
        const points = [sourcePoint, ...routePoints, targetPoint]
        const curves = Curve.throughPoints(points)
        const path = new Path(curves)
        return options.raw ? path : path.serialize()
      }

      const deltaY = Math.abs(targetPoint.y - sourcePoint.y)
      const deltaX = Math.abs(targetPoint.x - sourcePoint.x)
      
      const path = new Path()
      path.appendSegment(Path.createSegment('M', sourcePoint))

      // 最小控制距离，避免节点过近时曲线太扁
      const minControl = 50
      
      // 根据连接方向判断主要是横向还是纵向
      const isHorizontal = deltaX > deltaY
      
      let control1, control2
      
      if (isHorizontal) {
        // 横向连接：控制点在水平方向延伸，考虑方向避免回折
        const direction = targetPoint.x > sourcePoint.x ? 1 : -1
        const hControl = Math.max(deltaX * 0.5, minControl) * direction
        control1 = {
          x: sourcePoint.x + hControl,
          y: sourcePoint.y
        }
        control2 = {
          x: targetPoint.x - hControl,
          y: targetPoint.y
        }
      } else {
        // 纵向连接：控制点在垂直方向延伸
        const vControl = Math.max(deltaY * 0.5, minControl)
        control1 = {
          x: sourcePoint.x,
          y: sourcePoint.y + vControl
        }
        control2 = {
          x: targetPoint.x,
          y: targetPoint.y - vControl
        }
      }

      // 使用三次贝塞尔曲线
      path.appendSegment(
        Path.createSegment('C', control1, control2, targetPoint)
      )

      return options.raw ? path : path.serialize()
    },
    true
  )

  Graph.registerEdge(
    DAG_EDGE,
    {
      inherit: 'edge',
      attrs: {
        line: {
          stroke: '#C2C8D5',
          strokeWidth: 2,
          targetMarker: null
        }
      },
      zIndex: -1
    },
    true
  )

  registered = true
}
