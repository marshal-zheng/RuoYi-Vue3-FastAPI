import type { DeviceMockData } from '../types';
import { mockDevices } from './devices';

export const deviceMockData = {
  devices: mockDevices,
} satisfies DeviceMockData;

export * from './devices';
