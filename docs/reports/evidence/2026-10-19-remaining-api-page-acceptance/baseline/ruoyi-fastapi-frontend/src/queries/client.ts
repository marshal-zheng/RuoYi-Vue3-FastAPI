import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import type { App } from 'vue';

// This SPA owns one client. Other hosted features keep their own key namespaces.
export const queryClient = new QueryClient();

export function setupQueries(app: App): void {
  app.use(VueQueryPlugin, { queryClient });
}
