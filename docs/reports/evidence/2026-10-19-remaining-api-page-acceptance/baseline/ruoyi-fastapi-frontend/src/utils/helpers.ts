/** Small shared helpers consumed by the colour conversion utilities. */
export function clamp(value: number, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value));
}

export function has<T extends string>(obj: object, keys: T[]): obj is Record<T, unknown> {
  return keys.every((key) => Object.prototype.hasOwnProperty.call(obj, key));
}

export function padEnd(str: string, length: number, char = '0') {
  return str + char.repeat(Math.max(0, length - str.length));
}

export function chunk(str: string, size = 1) {
  const chunks: string[] = [];
  for (let index = 0; index < str.length; index += size) {
    chunks.push(str.slice(index, index + size));
  }
  return chunks;
}
