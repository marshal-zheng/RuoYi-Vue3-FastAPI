/** Values persisted in a generated form design are JSON data, never executable callbacks. */
export type GeneratorValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | GeneratorValue[]
  | { [key: string]: GeneratorValue };
