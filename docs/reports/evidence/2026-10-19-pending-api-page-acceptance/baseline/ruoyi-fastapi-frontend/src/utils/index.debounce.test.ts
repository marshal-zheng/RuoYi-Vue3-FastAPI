import { afterEach, describe, expect, it, vi } from 'vitest';
import { debounce } from './index';

describe('debounce callback contract', () => {
  afterEach(() => vi.useRealTimers());

  it('delivers the last arguments and receiver to a delayed callback', () => {
    vi.useFakeTimers();
    const receiver = {
      label: 'owner',
      callback: vi.fn(function (this: { label: string }, value: string) {
        return `${this.label}:${value}`;
      }),
    };
    const callback = debounce(receiver.callback, 100);
    callback.call(receiver, 'first');
    vi.advanceTimersByTime(50);
    callback.call(receiver, 'last');
    vi.advanceTimersByTime(100);
    expect(receiver.callback).toHaveBeenCalledExactlyOnceWith('last');
    expect(receiver.callback.mock.contexts[0]).toBe(receiver);
  });

  it('preserves immediate return values without a trailing callback', () => {
    vi.useFakeTimers();
    const fn = vi.fn((value: number) => value * 2);
    const callback = debounce(fn, 100, true);
    expect(callback(3)).toBe(6);
    expect(callback(4)).toBe(6);
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledExactlyOnceWith(3);
    expect(callback(5)).toBe(10);
  });
});
