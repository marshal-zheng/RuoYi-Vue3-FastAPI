import { MOCK_REFERENCE_TIME } from './constants';

export function formatMockDateTime(isoValue: string = MOCK_REFERENCE_TIME): string {
  const date = new Date(isoValue);
  const pad = (value: number) => value.toString().padStart(2, '0');
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

export function offsetMockTime(days: number, hours = 0): string {
  const date = new Date(MOCK_REFERENCE_TIME);
  date.setUTCDate(date.getUTCDate() + days);
  date.setUTCHours(date.getUTCHours() + hours);
  return date.toISOString();
}
