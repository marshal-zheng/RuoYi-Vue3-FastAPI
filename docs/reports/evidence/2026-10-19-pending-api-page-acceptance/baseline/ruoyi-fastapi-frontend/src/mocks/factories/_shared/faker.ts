import { fakerZH_CN as mockFaker } from '@faker-js/faker';

import { MOCK_REFERENCE_TIME, MOCK_SEED } from '../../data/_shared';

export function resetMockFaker(seed: number = MOCK_SEED, referenceTime = MOCK_REFERENCE_TIME) {
  mockFaker.seed(seed);
  mockFaker.setDefaultRefDate(referenceTime);
  return mockFaker;
}

resetMockFaker();

export { mockFaker };
