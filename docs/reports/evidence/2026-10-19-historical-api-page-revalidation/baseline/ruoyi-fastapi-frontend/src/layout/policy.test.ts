import { describe, expect, it } from 'vitest';

import { resolveLayoutVisibility as resolve } from './policy';

describe('application chrome policy', () => {
  const preferences = {
    headerVisible: true,
    tagsView: false,
    breadcrumbVisible: true,
  };

  it('keeps header, tags and breadcrumb preferences independent', () => {
    expect(resolve(preferences)).toEqual(preferences);
    expect(resolve({ ...preferences, headerVisible: false, tagsView: true })).toEqual({
      headerVisible: false,
      tagsView: true,
      breadcrumbVisible: true,
    });
  });

  it('applies only explicit route overrides without changing user preferences', () => {
    expect(
      resolve(preferences, {
        layout: { headerVisible: false, breadcrumbVisible: false },
      })
    ).toEqual({
      headerVisible: false,
      tagsView: false,
      breadcrumbVisible: false,
    });
    expect(resolve(preferences)).toEqual(preferences);
    expect(preferences.headerVisible).toBe(true);
  });

  it('ignores malformed route overrides', () => {
    expect(
      resolve(preferences, {
        layout: { tagsView: 'false', headerVisible: null },
      })
    ).toEqual(preferences);
    expect(resolve(preferences, { layout: null })).toEqual(preferences);
  });
});
