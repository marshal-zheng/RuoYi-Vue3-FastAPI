export interface LayoutVisibility {
  headerVisible: boolean;
  tagsView: boolean;
  breadcrumbVisible: boolean;
}

/** Route overrides are computed per page and never written to user preferences. */
export function resolveLayoutVisibility(
  preferences: LayoutVisibility,
  meta: Record<string, unknown> = {}
): LayoutVisibility {
  const override =
    meta.layout && typeof meta.layout === 'object'
      ? (meta.layout as Partial<LayoutVisibility>)
      : {};
  return {
    headerVisible:
      typeof override.headerVisible === 'boolean'
        ? override.headerVisible
        : preferences.headerVisible,
    tagsView: typeof override.tagsView === 'boolean' ? override.tagsView : preferences.tagsView,
    breadcrumbVisible:
      typeof override.breadcrumbVisible === 'boolean'
        ? override.breadcrumbVisible
        : preferences.breadcrumbVisible,
  };
}
