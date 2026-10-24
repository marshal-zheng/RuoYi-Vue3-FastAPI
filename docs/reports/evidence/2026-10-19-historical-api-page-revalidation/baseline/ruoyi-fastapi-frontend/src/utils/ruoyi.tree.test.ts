import { describe, expect, it } from 'vitest';
import { handleTree } from './ruoyi';

describe('tree construction with API identifiers', () => {
  it('joins numeric identifiers to their serialized parent identifiers', () => {
    const root = {
      id: 1,
      parentId: 0,
      name: 'parent',
      children: undefined as unknown[] | undefined,
    };
    const child = {
      id: 2,
      parentId: '1',
      name: 'child',
      children: undefined as unknown[] | undefined,
    };
    const tree = handleTree([root, child]);
    expect(tree).toEqual([root]);
    expect(root.children).toEqual([child]);
    expect(root.children?.[0]).toBe(child);
  });

  it('supports custom keys and identifiers which resemble object prototype properties', () => {
    const root = { key: '__proto__', parent: 'none', nodes: undefined as unknown[] | undefined };
    const child = { key: 'child', parent: '__proto__', nodes: undefined as unknown[] | undefined };
    expect(handleTree([root, child], 'key', 'parent', 'nodes')).toEqual([root]);
    expect(root.nodes).toEqual([child]);
  });
});
