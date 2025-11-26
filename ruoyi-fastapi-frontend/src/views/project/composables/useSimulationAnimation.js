/**
 * 仿真动画管理 Composable
 * 负责令牌动画、帧动画控制
 */

const SIMULATION_TOKEN_SIZE = 12;

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
   */
  function createSimulationToken(graph, startPoint) {
    if (!graph || !startPoint) {
      return null;
    }
    const halfSize = SIMULATION_TOKEN_SIZE / 2;
    const token = graph.addNode({
      shape: 'circle',
      width: SIMULATION_TOKEN_SIZE,
      height: SIMULATION_TOKEN_SIZE,
      x: startPoint.x - halfSize,
      y: startPoint.y - halfSize,
      zIndex: 1000,
      attrs: {
        body: {
          fill: '#f97316',
          stroke: '#ffffff',
          strokeWidth: 2,
        },
      },
      data: {
        isSimToken: true,
      },
      rotatable: false,
      draggable: false,
      resizable: false,
    });
    registerSimulationToken(token);
    return token;
  }

  /**
   * 边上的令牌动画
   */
  function animateEdgeToken(edge, direction = 'forward', duration = 950, callbacks = {}) {
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
    const token = createSimulationToken(graph, startPoint);
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
      const progress = Math.min((timestamp - state.startTs) / duration, 1);
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

      if (progress >= 1) {
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
