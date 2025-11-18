import { Graph } from '@antv/x6'
import { Curve, Path } from '@antv/x6-geometry'
import { register } from '@antv/x6-vue-shape'
import DagNode from './DagNode.vue'
import { PORT_GROUPS } from '../config/portConfig.js'
import { DAG_NODE_CONFIG } from '../config/nodeConfig.js'
import { DAG_EDGE_CONFIG } from '../config/edgeConfig.js'
import { DAG_CONNECTOR_CONFIG } from '../config/connectorConfig.js'

export const DAG_NODE = DAG_NODE_CONFIG.shape
export const DAG_EDGE = DAG_EDGE_CONFIG.shape
export const DAG_CONNECTOR = DAG_CONNECTOR_CONFIG.name

let registered = false

export const registerDagShapes = () => {
  if (registered) {
    return
  }

  const nodeSize = DAG_NODE_CONFIG.size.horizontal
  
  register({
    shape: DAG_NODE,
    width: nodeSize.width,
    height: nodeSize.height,
    component: DagNode,
    effect: ['data'],
    attrs: {
      body: {
        width: nodeSize.width,
        height: nodeSize.height
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
      const minControl = DAG_CONNECTOR_CONFIG.minControl
      const controlFactor = DAG_CONNECTOR_CONFIG.controlFactor
      
      // 根据连接方向判断主要是横向还是纵向
      const isHorizontal = deltaX > deltaY
      
      let control1, control2
      
      if (isHorizontal) {
        // 横向连接：控制点在水平方向延伸，考虑方向避免回折
        const direction = targetPoint.x > sourcePoint.x ? 1 : -1
        const hControl = Math.max(deltaX * controlFactor, minControl) * direction
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
        const vControl = Math.max(deltaY * controlFactor, minControl)
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

  const edgeStyle = DAG_EDGE_CONFIG.style.normal
  const labelStyle = DAG_EDGE_CONFIG.label.weight
  
  Graph.registerEdge(
    DAG_EDGE,
    {
      inherit: 'edge',
      attrs: {
        line: {
          stroke: edgeStyle.stroke,
          strokeWidth: edgeStyle.strokeWidth,
          targetMarker: null
        }
      },
      defaultLabel: {
        markup: [
          {
            tagName: 'text',
            selector: 'text'
          }
        ],
        attrs: {
          text: {
            fill: labelStyle.fill,
            fontSize: labelStyle.fontSize,
            fontWeight: labelStyle.fontWeight,
            textAnchor: labelStyle.textAnchor,
            textVerticalAnchor: labelStyle.textVerticalAnchor,
            cursor: labelStyle.cursor
          }
        }
      },
      zIndex: -1
    },
    true
  )

  registered = true
}
