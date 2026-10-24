import { readonly, ref } from 'vue';

/** One business operation instance owns its complete validation/confirmation/write lifecycle. */
export function useOperation<Args extends unknown[], Result>(
  action: (...args: Args) => Result | Promise<Result>
) {
  const pending = ref(false);
  let current: Promise<Result> | undefined;

  const run = (...args: Args): Promise<Result> => {
    if (current) return current;
    // Acquire before invoking user code, including synchronous reentry or validation.
    const task = Promise.resolve()
      .then(() => action(...args))
      .finally(() => {
        current = undefined;
        pending.value = false;
      });
    current = task;
    pending.value = true;
    return task;
  };

  return { pending: readonly(pending), run };
}
