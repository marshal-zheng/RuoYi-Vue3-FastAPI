/**
 * 仿真动画管理 Composable
 * 负责令牌动画、帧动画控制
 */

const SIMULATION_TOKEN_SIZE = 14;

// 令牌颜色配置（根据总线类型）
const TOKEN_COLORS = {
  LAN: { fill: '#3b82f6', stroke: '#60a5fa' }, // 蓝色
  CAN: { fill: '#22c55e', stroke: '#4ade80' }, // 绿色
  RS422: { fill: '#f97316', stroke: '#fb923c' }, // 橙色
  RS485: { fill: '#f97316', stroke: '#fb923c' }, // 橙色
  '1553B': { fill: '#a855f7', stroke: '#c084fc' }, // 紫色
  default: { fill: '#f97316', stroke: '#ffffff' }, // 默认橙色
};

export function useSimulationAnimation() {
  const simulationArtifacts = {
    tokens: new Set(),
    animations: new Set(),
  };

  /**
   * 注册仿真令牌
   */
  function registerSimulationToken(token) {
    if (token) {
      simulationArtifacts.tokens.add(token);
    }
  }

  /**
   * 销毁仿真令牌
   */
  function disposeSimulationToken(token) {
    if (token) {
      token.remove?.();
      simulationArtifacts.tokens.delete(token);
    }
  }

  /**
   * 销毁所有仿真令牌
   */
  function disposeAllSimulationTokens() {
    simulationArtifacts.tokens.forEach((token) => {
      token.remove?.();
    });
    simulationArtifacts.tokens.clear();
  }

  /**
   * 销毁仿真动画
   */
  function disposeSimulationAnimations() {
    simulationArtifacts.animations.forEach((controller) => {
      if (typeof controller?.cancel === 'function') {
        controller.cancel();
      }
    });
    simulationArtifacts.animations.clear();
  }

  /**
   * 创建仿真令牌
   * @param {Object} graph - 图实例
   * @param {Object} startPoint - 起始点
   * @param {String} busType - 总线类型
   */
  function createSimulationToken(graph, startPoint, busType = 'default') {
    if (!graph || !startPoint) {
      return null;
    }
    const halfSize = SIMULATION_TOKEN_SIZE / 2;
    const colors = TOKEN_COLORS[busType] || TOKEN_COLORS.default;

    const token = graph.addNode({
      shape: 'circle',
      width: SIMULATION_TOKEN_SIZE,
      height: SIMULATION_TOKEN_SIZE,
      x: startPoint.x - halfSize,
      y: startPoint.y - halfSize,
      zIndex: 1000,
      attrs: {
        body: {
          fill: colors.fill,
          stroke: colors.stroke,
          strokeWidth: 2,
          filter: {
            name: 'dropShadow',
            args: {
              dx: 0,
              dy: 0,
              blur: 6,
              color: colors.fill,
              opacity: 0.6,
            },
          },
        },
      },
      data: {
        isSimToken: true,
        busType,
      },
      rotatable: false,
      draggable: false,
      resizable: false,
    });
    registerSimulationToken(token);
    return token;
  }

  /**
   * 缓动函数 - 使动画更流畅
   */
  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /**
   * 边上的令牌动画
   * @param {Object} edge - 边对象
   * @param {String} direction - 方向 'forward' | 'reverse'
   * @param {Number} duration - 动画持续时间
   * @param {Object} callbacks - 回调函数
   * @param {String} busType - 总线类型
   */
  function animateEdgeToken(edge, direction = 'forward', duration = 950, callbacks = {}, busType = 'default') {
    if (!edge) {
      if (callbacks.onCancelled) {
        callbacks.onCancelled();
      }
      return null;
    }

    const graph = edge.model?.graph;
    if (!graph) {
      if (callbacks.onCancelled) {
        callbacks.onCancelled();
      }
      return null;
    }

    // 获取边的总线类型
    const edgeData = edge.getData?.() || {};
    const actualBusType = busType !== 'default' ? busType : (edgeData.busType || edgeData.interfaceType || 'default');

    const edgeView = graph.findViewByCell?.(edge);
    const pathElement =
      edgeView?.container?.querySelector?.('path[data-edge-path="1"]') ||
      edgeView?.container?.querySelector?.('path');
    const pathTotalLength =
      typeof pathElement?.getTotalLength === 'function' ? pathElement.getTotalLength() : 0;
    const sourcePoint = edge.getSourcePoint?.();
    const targetPoint = edge.getTargetPoint?.();

    if (!pathElement && (!sourcePoint || !targetPoint)) {
      if (callbacks.onCancelled) {
        callbacks.onCancelled();
      }
      return null;
    }

    const startPoint = direction === 'forward' ? sourcePoint : targetPoint;
    const token = createSimulationToken(graph, startPoint, actualBusType);
    if (!token) {
      if (callbacks.onCancelled) {
        callbacks.onCancelled();
      }
      return null;
    }

    const state = {
      rafId: 0,
      cancelled: false,
      startTs: 0,
    };

    const controller = {
      cancel() {
        if (state.cancelled) {
          return;
        }
        state.cancelled = true;
        if (state.rafId) {
          cancelAnimationFrame(state.rafId);
        }
        disposeSimulationToken(token);
        simulationArtifacts.animations.delete(controller);
        if (callbacks.onCancelled) {
          callbacks.onCancelled();
        }
      },
    };

    const stepFrame = (timestamp) => {
      if (state.cancelled) {
        return;
      }
      if (!state.startTs) {
        state.startTs = timestamp;
      }
      const linearProgress = Math.min((timestamp - state.startTs) / duration, 1);
      // 使用缓动函数使动画更流畅
      const progress = easeInOutCubic(linearProgress);
      const travelProgress = direction === 'forward' ? progress : 1 - progress;
      const halfSize = SIMULATION_TOKEN_SIZE / 2;
      let x = 0;
      let y = 0;

      if (pathElement && pathTotalLength > 0) {
        const point = pathElement.getPointAtLength(pathTotalLength * travelProgress);
        x = point.x - halfSize;
        y = point.y - halfSize;
      } else if (sourcePoint && targetPoint) {
        if (direction === 'forward') {
          x = sourcePoint.x + (targetPoint.x - sourcePoint.x) * progress - halfSize;
          y = sourcePoint.y + (targetPoint.y - sourcePoint.y) * progress - halfSize;
        } else {
          x = targetPoint.x + (sourcePoint.x - targetPoint.x) * progress - halfSize;
          y = targetPoint.y + (sourcePoint.y - targetPoint.y) * progress - halfSize;
        }
      }

      token.position(x, y);

      // 根据进度调整令牌大小，产生脉冲效果
      const scaleFactor = 1 + Math.sin(linearProgress * Math.PI) * 0.15;
      const scaledSize = SIMULATION_TOKEN_SIZE * scaleFactor;
      token.resize(scaledSize, scaledSize);

      if (linearProgress >= 1) {
        disposeSimulationToken(token);
        simulationArtifacts.animations.delete(controller);
        if (callbacks.onCompleted) {
          callbacks.onCompleted();
        }
        return;
      }
      state.rafId = requestAnimationFrame(stepFrame);
    };

    state.rafId = requestAnimationFrame(stepFrame);
    simulationArtifacts.animations.add(controller);
    return controller;
  }

  return {
    animateEdgeToken,
    disposeSimulationAnimations,
    disposeAllSimulationTokens,
  };
}
