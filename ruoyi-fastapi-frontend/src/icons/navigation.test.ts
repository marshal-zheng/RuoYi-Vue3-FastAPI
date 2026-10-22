import { describe, expect, it } from 'vitest';
import { resolveNavigationIcon } from './navigation';

describe('navigation icon choices', () => {
  it.each(['constructor', 'toString', '__proto__'])(
    'keeps unknown inherited name %s as a custom SVG identifier',
    (name) => {
      expect(resolveNavigationIcon(name)).toBe(`svg-icon:${name}`);
      expect(resolveNavigationIcon(`svg-icon:${name}`)).toBe(`svg-icon:${name}`);
    }
  );

  it('keeps mapped menu names, custom protocols and empty icons', () => {
    expect(resolveNavigationIcon('system')).toBe('svg-icon:material-symbols-settings');
    expect(resolveNavigationIcon('svg-icon:system')).toBe('svg-icon:material-symbols-settings');
    expect(resolveNavigationIcon('svg-icon:custom')).toBe('svg-icon:custom');
    expect(resolveNavigationIcon('mdi:home')).toBe('mdi:home');
    expect(resolveNavigationIcon('#')).toBe('');
    expect(resolveNavigationIcon()).toBe('');
  });
});
