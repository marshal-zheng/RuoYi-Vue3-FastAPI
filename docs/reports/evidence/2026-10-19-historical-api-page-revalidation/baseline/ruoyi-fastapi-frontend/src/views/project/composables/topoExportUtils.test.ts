import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { exportTopologyAsImage, exportGraphJsonAsImage } from './topoExportUtils';
import { getProjectTopology } from '@/api/project/topology';

const render = vi.hoisted(() => ({
  fromJSON: vi.fn(),
  created: vi.fn(),
  disposed: vi.fn(),
}));
vi.mock('@/api/project/topology', () => ({ getProjectTopology: vi.fn() }));
vi.mock('@/components/business/Dag/shapes/registerDagShapes', () => ({
  registerDagShapes: vi.fn(),
  DAG_CONNECTOR: 'dag-connector',
}));
vi.mock('@antv/x6-plugin-export', () => ({ Export: class {} }));
vi.mock('@antv/x6', () => ({
  Graph: class {
    constructor() {
      render.created();
    }
    use() {}
    fromJSON(data: unknown) {
      render.fromJSON(data);
    }
    getNodes() {
      return [{}];
    }
    getEdges() {
      return [];
    }
    getContentBBox() {
      return { width: 10, height: 10 };
    }
    resize() {}
    zoomToFit() {}
    centerContent() {}
    dispose() {
      render.disposed();
    }
    toPNG(callback: (uri: string) => void) {
      callback('data:image/png;base64,aW1hZ2U=');
    }
  },
}));

describe('topology export consumes the real resource boundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('keeps a legitimate empty resource as an optional missing image', async () => {
    vi.mocked(getProjectTopology).mockResolvedValueOnce({});
    await expect(exportTopologyAsImage({ projectId: 1 })).resolves.toBeNull();
    expect(render.created).not.toHaveBeenCalled();
  });

  it('does not create a renderer for malformed cells from dynamic topology data', async () => {
    vi.mocked(getProjectTopology).mockResolvedValueOnce({
      topologyData: { graph: { cells: [null] } },
    });
    const pending = exportTopologyAsImage({ projectId: 1 });
    await vi.runAllTimersAsync();
    await expect(pending).resolves.toBeNull();
    expect(render.created).not.toHaveBeenCalled();
  });

  it('preserves valid cells, produces image bytes and releases the renderer', async () => {
    const graph = {
      cells: [
        {
          id: 'node-1',
          shape: 'rect',
          attrs: { body: { strokeWidth: 2 } },
          data: { ports: [] },
        },
      ],
    };
    const pending = exportGraphJsonAsImage(graph);
    await vi.runAllTimersAsync();
    await expect(pending).resolves.toBe('aW1hZ2U=');
    expect(render.fromJSON).toHaveBeenCalledExactlyOnceWith(graph);
    expect(render.disposed).toHaveBeenCalledOnce();
    expect(document.querySelector('div[style*="-10000px"]')).toBeNull();
  });
});
