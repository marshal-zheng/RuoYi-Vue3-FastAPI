export const MOCK_USER_IDS = {
  admin: 1,
  editor: 2,
} as const;

export const MOCK_ROLE_IDS = {
  admin: 1,
  editor: 2,
} as const;

export const MOCK_DEPT_IDS = {
  root: 100,
  platform: 101,
  delivery: 102,
} as const;

export const MOCK_PROJECT_IDS = {
  commandCenter: 1001,
  trainingRange: 1002,
} as const;

export const MOCK_VERSION_IDS = {
  commandCenterBaseline: 2001,
  commandCenterReview: 2002,
  trainingRangeBaseline: 2101,
} as const;

export const MOCK_TOPOLOGY_IDS = {
  commandCenterBaseline: 'topology-command-center-baseline',
  commandCenterReview: 'topology-command-center-review',
  trainingRangeBaseline: 'topology-training-range-baseline',
} as const;

export const MOCK_SIMULATION_IDS = {
  commandCenterSession: 'sim-command-center-001',
} as const;
