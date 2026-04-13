import type { DemoOfflineDb } from '@/demo/db';

export type DemoSequenceName = 'projects' | 'projectVersions' | 'dicts' | 'menus' | 'departments';

export async function nextDemoSequence(
  db: DemoOfflineDb,
  name: DemoSequenceName,
  startAt = 1
): Promise<number> {
  return db.transaction('rw', db.sequences, async () => {
    const current = await db.sequences.get(name);
    const nextValue = current?.value ?? startAt;
    await db.sequences.put({
      name,
      value: nextValue + 1,
    });
    return nextValue;
  });
}
