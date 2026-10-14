import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useGraphStore } from '@/components/business/ZxFlow/stores/graphStore';

describe('graph state invariants', () => {
  beforeEach(() => setActivePinia(createPinia()));

  it('rejects duplicate node identifiers before mutating state', () => {
    const store = useGraphStore();
    store.addNodes([{ id: 'first', shape: 'rect' }]);
    expect(() => store.addNodes([{ id: 'first', shape: 'rect' }])).toThrow('节点 ID first 已存在');
    expect(store.nodes).toHaveLength(1);
  });

  it('rejects identity changes while retaining the existing edge', () => {
    const store = useGraphStore();
    store.addEdges([{ id: 'edge', shape: 'edge' }]);
    expect(() => store.updateEdge('edge', { id: 'replacement' })).toThrow('ID 和图形类型');
    expect(store.edges[0]).toMatchObject({ id: 'edge' });
  });
});
