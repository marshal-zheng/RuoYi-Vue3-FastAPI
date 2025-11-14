export const DAG_NODE_SIZE = {
  horizontal: {
    width: 200,
    height: 38
  },
  vertical: {
    width: 45,
    height: 200
  }
}

/**
 * 根据布局方向（LR/TB）获取节点尺寸
 * @param {'LR'|'TB'} direction
 */
export const getNodeSizeByDirection = (direction) => {
  return direction === 'TB' ? DAG_NODE_SIZE.vertical : DAG_NODE_SIZE.horizontal
}

/**
 * 根据布局方向（horizontal/vertical）获取节点尺寸
 * @param {'horizontal'|'vertical'} layout
 */
export const getNodeSizeByLayout = (layout) => {
  return layout === 'vertical' ? DAG_NODE_SIZE.vertical : DAG_NODE_SIZE.horizontal
}
