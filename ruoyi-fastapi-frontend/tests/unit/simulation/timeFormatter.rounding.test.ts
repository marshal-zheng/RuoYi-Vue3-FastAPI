import { expect, it } from 'vitest';
import {
  formatSimulationTime,
  parseSimulationTime,
} from '@/views/project/simulation/utils/timeFormatter';

it.each([
  [14.999500274658203, '00:00:15.000', 15],
  [0.9995, '00:00:01.000', 1],
  [59.9995, '00:01:00.000', 60],
  [3599.9995, '01:00:00.000', 3600],
  [86399.9995, '24:00:00.000', 86400],
  [14.9994, '00:00:14.999', 14.999],
] as const)('formats %s seconds with normalized milliseconds', (seconds, expected, parsed) => {
  const formatted = formatSimulationTime(seconds);
  expect(formatted).toBe(expected);
  expect(parseSimulationTime(formatted)).toBe(parsed);
});
