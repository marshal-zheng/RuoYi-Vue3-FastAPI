import type { Table, UpdateSpec } from 'dexie';

export type DemoRepositoryId = string | number;

export interface DemoQuery<T extends object = Record<string, unknown>> {
  pageNum?: number;
  pageSize?: number;
  filters?: Partial<Record<Extract<keyof T, string>, unknown>>;
  sortBy?: Extract<keyof T, string>;
  sortOrder?: 'asc' | 'desc';
}

export interface DemoPage<T> {
  rows: T[];
  total: number;
  pageNum: number;
  pageSize: number;
}

export interface DemoRepository<T extends object, ID extends DemoRepositoryId> {
  list(query?: DemoQuery<T>): Promise<DemoPage<T>>;
  get(id: ID): Promise<T | undefined>;
  create(input: Partial<T>): Promise<T>;
  update(id: ID, patch: Partial<T>): Promise<T>;
  remove(id: ID): Promise<void>;
}

function matchesFilter(value: unknown, expected: unknown): boolean {
  if (expected === undefined || expected === null || expected === '') {
    return true;
  }

  if (typeof value === 'string' && typeof expected === 'string') {
    return value.toLowerCase().includes(expected.toLowerCase());
  }

  return value === expected;
}

function compareValues(left: unknown, right: unknown): number {
  if (left === right) return 0;
  if (left === undefined || left === null) return -1;
  if (right === undefined || right === null) return 1;
  return String(left).localeCompare(String(right), 'zh-Hans-CN', {
    numeric: true,
  });
}

export abstract class DexieDemoRepository<T extends object, ID extends DemoRepositoryId>
  implements DemoRepository<T, ID>
{
  protected constructor(
    protected readonly table: Table<T, ID>,
    protected readonly idKey: Extract<keyof T, string>
  ) {}

  async list(query: DemoQuery<T> = {}): Promise<DemoPage<T>> {
    const pageNum = Math.max(Number(query.pageNum ?? 1), 1);
    const pageSize = Math.max(Number(query.pageSize ?? 10), 1);
    const filters = query.filters ?? {};
    const filterEntries = Object.entries(filters);
    const allRows = await this.table.toArray();

    const filteredRows = allRows.filter((row) =>
      filterEntries.every(([field, expected]) => {
        const value = row[field as keyof T];
        return matchesFilter(value, expected);
      })
    );

    if (query.sortBy) {
      const direction = query.sortOrder === 'desc' ? -1 : 1;
      filteredRows.sort(
        (left, right) =>
          compareValues(left[query.sortBy as keyof T], right[query.sortBy as keyof T]) * direction
      );
    }

    const start = (pageNum - 1) * pageSize;

    return {
      rows: filteredRows.slice(start, start + pageSize),
      total: filteredRows.length,
      pageNum,
      pageSize,
    };
  }

  get(id: ID): Promise<T | undefined> {
    return this.table.get(id);
  }

  async create(input: Partial<T>): Promise<T> {
    const record = input as T;
    await this.table.add(record);
    return record;
  }

  async update(id: ID, patch: Partial<T>): Promise<T> {
    await this.table.update(id, patch as UpdateSpec<T>);
    const updated = await this.get(id);

    if (!updated) {
      throw new Error(`Demo repository record "${String(id)}" was not found after update.`);
    }

    return updated;
  }

  async remove(id: ID): Promise<void> {
    await this.table.delete(id);
  }
}
