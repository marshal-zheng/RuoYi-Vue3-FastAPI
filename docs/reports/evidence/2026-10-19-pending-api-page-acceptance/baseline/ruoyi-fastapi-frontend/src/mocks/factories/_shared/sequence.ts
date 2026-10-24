export interface MockSequence {
  next(): number;
  reset(nextValue?: number): void;
}

export function createSequence(start = 1): MockSequence {
  let value = start;
  return {
    next() {
      const current = value;
      value += 1;
      return current;
    },
    reset(nextValue = start) {
      value = nextValue;
    },
  };
}
