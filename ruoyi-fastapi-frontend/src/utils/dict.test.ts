import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { getDicts } from '@/api/system/dict/data';
import useDictStore from '@/store/modules/dict';
import { useDict } from './dict';

vi.mock('@/api/system/dict/data', () => ({ getDicts: vi.fn() }));
const settled = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  setActivePinia(createPinia());
  vi.mocked(getDicts).mockReset();
});

describe('dictionary collection consumer', () => {
  it('updates all consumers from items and preserves submitted string values', async () => {
    vi.mocked(getDicts).mockResolvedValue({
      items: [
        { dictLabel: '正常', dictValue: '0', listClass: 'primary' },
        { dictLabel: '停用', dictValue: '1' },
      ],
    });
    const first = useDict('sys_normal_disable');
    const second = useDict('sys_normal_disable');
    expect(first.sys_normal_disable.value).toEqual([]);
    await settled();
    expect(getDicts).toHaveBeenCalledTimes(1);
    expect(first.sys_normal_disable.value.map(({ label, value }) => ({ label, value }))).toEqual([
      { label: '正常', value: '0' },
      { label: '停用', value: '1' },
    ]);
    expect(second.sys_normal_disable.value).toEqual(first.sys_normal_disable.value);
    expect(useDict('sys_normal_disable').sys_normal_disable.value).toEqual(
      first.sys_normal_disable.value
    );
    expect(getDicts).toHaveBeenCalledTimes(1);
  });

  it('retries failures instead of caching an empty dictionary', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.mocked(getDicts).mockRejectedValueOnce(new Error('unavailable'));
    useDict('sys_retry');
    await settled();
    expect(useDictStore().getDict('sys_retry')).toBeUndefined();
    vi.mocked(getDicts).mockResolvedValueOnce({ items: [{ dictLabel: '恢复', dictValue: '0' }] });
    const retry = useDict('sys_retry');
    await settled();
    expect(retry.sys_retry.value[0].value).toBe('0');
  });
});
