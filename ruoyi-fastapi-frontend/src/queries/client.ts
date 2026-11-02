import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { createDataClient, provideDataClient } from '@zxio/vue-query/resources';
import type { App } from 'vue';

// This SPA owns one client. Other hosted features keep their own key namespaces.
export const queryClient = new QueryClient();
export const dataClient = createDataClient({ queryClient });

export function setupQueries(app: App): void {
  app.use(VueQueryPlugin, { queryClient });
  provideDataClient(dataClient, app);
}
