/** Business navigation icon choices. SVGs are local Material Symbols Filled assets. */
const symbol = (name: string) => `svg-icon:material-symbols-${name}`;

export const navigationIcons = Object.freeze({
  toggle: symbol('menu_open'),
  more: symbol('more_horiz'),
  user: symbol('person'),
  chevronDown: symbol('expand_more'),
  settings: symbol('settings'),
  lightMode: symbol('light_mode'),
  darkMode: symbol('dark_mode'),
  search: symbol('search'),
});

/** Existing menu identifiers remain application data, separate from their artwork. */
export const navigationMenuIcons: Readonly<Record<string, string>> = Object.freeze({
  system: symbol('settings'),
  user: symbol('person'),
  peoples: symbol('group'),
  'tree-table': symbol('menu'),
  tree: symbol('account_tree'),
  post: symbol('badge'),
  dict: symbol('menu_book'),
  edit: symbol('tune'),
  message: symbol('campaign'),
  log: symbol('history'),
  form: symbol('description'),
  logininfor: symbol('login'),
  monitor: symbol('monitoring'),
  online: symbol('devices'),
  job: symbol('schedule'),
  druid: symbol('storage'),
  server: symbol('dns'),
  redis: symbol('memory'),
  'redis-list': symbol('storage'),
  tool: symbol('construction'),
  build: symbol('design_services'),
  code: symbol('code'),
  swagger: symbol('api'),
  list: symbol('view_list'),
  table: symbol('table_chart'),
  dashboard: symbol('dashboard'),
});

export function resolveNavigationIcon(icon?: string): string {
  if (!icon || icon === '#') return '';
  const name = icon.startsWith('svg-icon:') ? icon.slice('svg-icon:'.length) : icon;
  return navigationMenuIcons[name] ?? (icon.includes(':') ? icon : `svg-icon:${icon}`);
}
