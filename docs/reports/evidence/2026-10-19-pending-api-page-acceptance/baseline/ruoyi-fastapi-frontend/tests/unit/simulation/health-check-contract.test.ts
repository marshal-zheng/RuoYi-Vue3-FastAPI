import { describe, expect, it } from 'vitest';
import { Node, Edge } from '@antv/x6';
import { useHealthCheck } from '@/views/project/simulation/composables/useHealthCheck';
import type { SimulationNodeData } from '@/views/project/simulation/composables/topology-types';

const device = (id: string, baudRate: number) =>
  new Node({
    id,
    data: {
      name: id,
      ports: [{ id: `${id}-port`, interfaceType: 'CAN', params: { baudRate } }],
    } satisfies SimulationNodeData,
  });

describe('health check public X6 contract', () => {
  it('uses real node/edge models and identifies parameter mismatches', () => {
    const first = device('node-1', 500000);
    const second = device('node-2', 250000);
    const edge = new Edge({
      id: 'edge-1',
      source: { cell: first.id, port: 'node-1-port' },
      target: { cell: second.id, port: 'node-2-port' },
    });
    const report = useHealthCheck().runHealthCheck({
      getNodes: () => [first, second],
      getEdges: () => [edge],
    });
    expect(report.canSimulate).toBe(true);
    expect(report.items.find((item) => item.id === 'param-consistency-warning')).toMatchObject({
      status: 'warning',
      details: {
        issues: [
          expect.objectContaining({
            issue: 'baudrate-mismatch',
            sourceValue: 500000,
            targetValue: 250000,
          }),
        ],
      },
    });
  });

  it('retains edge identifiers in loopback report details', () => {
    const first = device('node-1', 500000);
    const second = device('node-2', 500000);
    const edge = new Edge({
      id: 'loopback',
      source: { cell: first.id, port: 'node-1-port' },
      target: { cell: first.id, port: 'node-1-port' },
    });
    const report = useHealthCheck().runHealthCheck({
      getNodes: () => [first, second],
      getEdges: () => [edge],
    });
    expect(report.items.find((item) => item.id === 'conflict-loopback')?.details?.edgeIds).toEqual([
      'loopback',
    ]);
  });
});
