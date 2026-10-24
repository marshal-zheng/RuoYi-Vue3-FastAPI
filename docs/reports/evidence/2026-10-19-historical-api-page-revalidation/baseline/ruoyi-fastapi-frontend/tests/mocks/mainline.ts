import { afterEach, beforeEach } from 'vitest';

import { createMockHandlers } from '@/mocks/handlers';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '@/mocks/store/db';
import { createMockDataSource, replaceMockDataSource } from '@/mocks/store/datasource';
import type { MockDataSource } from '@/mocks/store';

import { mockServer } from './server';

let mainlineTestSequence = 0;

export interface MainlineMockContext {
  dataSource(): MockDataSource;
}

export function setupMainlineMockHandlers(): MainlineMockContext {
  let db: MockDemoDb | undefined;
  let dataSource: MockDataSource | undefined;

  beforeEach(async () => {
    mainlineTestSequence += 1;
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-mainline-api-test-${mainlineTestSequence}`);
    replaceMockDemoDb(db);
    dataSource = createMockDataSource(db);
    replaceMockDataSource(dataSource);
    await dataSource.init();
    mockServer.use(...createMockHandlers({ strategy: 'pure', dataSource }));
  });

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db?.delete();
    db = undefined;
    dataSource = undefined;
  });

  return {
    dataSource() {
      if (!dataSource) {
        throw new Error('Mainline mock data source is not initialized.');
      }
      return dataSource;
    },
  };
}
