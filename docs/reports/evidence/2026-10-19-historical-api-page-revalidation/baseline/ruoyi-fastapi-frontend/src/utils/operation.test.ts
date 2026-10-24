import { describe, expect, it, vi } from 'vitest';
import { watch } from 'vue';
import { useOperation } from './operation';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

describe('business operation lifecycle', () => {
  it('keeps synchronous pending observers inside the same operation', async () => {
    const waiting = deferred<void>();
    const action = vi.fn(() => waiting.promise);
    const operation = useOperation(action);
    let observed: Promise<void> | undefined;
    const stop = watch(
      operation.pending,
      (pending) => {
        if (pending) observed = operation.run();
      },
      { flush: 'sync' }
    );
    const first = operation.run();
    const sameOperation = observed === first;
    waiting.resolve();
    await Promise.all([first, observed]);
    stop();
    expect(sameOperation).toBe(true);
    expect(action).toHaveBeenCalledTimes(1);
  });

  it('acquires synchronously and runs the complete operation once during reentry', async () => {
    const validation = deferred<boolean>();
    const write = deferred<number>();
    const save = vi.fn(() => write.promise);
    const completed = vi.fn();
    const operation = useOperation(async () => {
      if (!(await validation.promise)) return false;
      const result = await save();
      completed();
      return result;
    });

    const first = operation.run();
    const duplicate = operation.run();
    expect(operation.pending.value).toBe(true);
    expect(duplicate).toBe(first);
    validation.resolve(true);
    await vi.waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(operation.pending.value).toBe(true);
    write.resolve(42);
    expect(await first).toBe(42);
    expect(await duplicate).toBe(42);
    expect(completed).toHaveBeenCalledTimes(1);
    expect(operation.pending.value).toBe(false);
  });

  it('keeps a slow operation protected beyond one second', async () => {
    vi.useFakeTimers();
    try {
      const waiting = deferred<void>();
      const action = vi.fn(() => waiting.promise);
      const operation = useOperation(action);
      const first = operation.run();
      await vi.advanceTimersByTimeAsync(2000);
      expect(operation.run()).toBe(first);
      expect(action).toHaveBeenCalledTimes(1);
      waiting.resolve();
      await first;
      expect(operation.pending.value).toBe(false);
    } finally {
      vi.useRealTimers();
    }
  });

  it.each(['failure', 'cancellation', 'synchronous throw'])(
    'retains %s and allows immediate retry',
    async (kind) => {
      const reason =
        kind === 'cancellation' ? new DOMException('cancelled', 'AbortError') : new Error(kind);
      let attempts = 0;
      const operation = useOperation(() => {
        if (++attempts === 1) {
          if (kind === 'synchronous throw') throw reason;
          return Promise.reject(reason);
        }
        return Promise.resolve('retried');
      });
      await expect(operation.run()).rejects.toBe(reason);
      expect(operation.pending.value).toBe(false);
      expect(await operation.run()).toBe('retried');
      expect(attempts).toBe(2);
    }
  );

  it('does not lock other operation instances and retains arguments and return values', async () => {
    const waiting = deferred<string>();
    const first = useOperation(() => waiting.promise);
    const second = useOperation(async (id: number) => id + 1);
    const pending = first.run();
    expect(await second.run(8)).toBe(9);
    expect(first.pending.value).toBe(true);
    expect(second.pending.value).toBe(false);
    waiting.resolve('first');
    expect(await pending).toBe('first');
  });
});
