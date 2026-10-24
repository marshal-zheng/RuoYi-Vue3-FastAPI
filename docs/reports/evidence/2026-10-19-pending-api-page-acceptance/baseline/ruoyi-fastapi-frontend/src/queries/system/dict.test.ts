import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useQuery, VueQueryPlugin, MutationObserver, onlineManager } from '@tanstack/vue-query';
import { defineComponent, unref } from 'vue';
import { mount } from '@vue/test-utils';
import { queryClient } from '../client';
import { endQuerySession, setQuerySession } from '../context';
import {
  dictOptions,
  dictKeys,
  dictCommands,
  readDict,
  captureDictCommand,
  dictTypeOptions,
  dictTypeDetailOptions,
} from './dict';
import { getDicts, updateData } from '@/api/system/dict/data';
import * as typeApi from '@/api/system/dict/type';

vi.mock('@/api/system/dict/data', () => ({
  getDicts: vi.fn(),
  updateData: vi.fn(),
  addData: vi.fn(),
  delData: vi.fn(),
}));
vi.mock('@/api/system/dict/type', () => ({
  addType: vi.fn(),
  updateType: vi.fn(),
  delType: vi.fn(),
  refreshCache: vi.fn(),
  getType: vi.fn(),
  optionselect: vi.fn(),
}));
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

function observe(scope: Parameters<typeof dictOptions>[0], type: string) {
  let query!: ReturnType<typeof useQuery<readonly import('./dict').DictItem[]>>;
  const wrapper = mount(
    defineComponent({
      setup() {
        query = useQuery(dictOptions(scope, type));
        return () => null;
      },
    }),
    {
      global: { plugins: [[VueQueryPlugin, { queryClient }]] },
    }
  );
  return { query, stop: () => wrapper.unmount() };
}

beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  vi.resetAllMocks();
  setQuerySession(1, ['admin'], ['system:dict:edit']);
});

describe('shared dictionary resource', () => {
  it('shares reads across observers and fresh mounts, then refreshes every resource variant after a write', async () => {
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '旧值', dictValue: '0' }] });
    const scope = setQuerySession(1, ['admin'], ['system:dict:edit']);
    const a = observe(scope, ' sys_a ');
    const b = observe(scope, 'sys_a');
    const c = observe(scope, 'sys_b');
    const stops = [a.stop, b.stop, c.stop];
    await tick();
    expect(getDicts).toHaveBeenCalledTimes(2);
    expect(a.query.data.value?.[0].value).toBe('0');
    const fresh = observe(scope, 'sys_a');
    stops.push(fresh.stop);
    await tick();
    expect(getDicts).toHaveBeenCalledTimes(2);
    vi.mocked(getDicts).mockResolvedValue({ items: [{ dictLabel: '新值', dictValue: '0' }] });
    vi.mocked(updateData).mockResolvedValue({ dictCode: 1 });
    await dictCommands.updateItem(captureDictCommand({ dictCode: 1, dictType: 'sys_a' }));
    await tick();
    expect(getDicts).toHaveBeenCalledTimes(4);
    expect(a.query.data.value?.[0].label).toBe('新值');
    expect(c.query.data.value?.[0].label).toBe('新值');
    stops.forEach((stop) => stop());
  });

  it('waits for a stale imperative read, and does not execute when scope or type is absent', async () => {
    const scope = setQuerySession(1, ['admin'], ['system:dict:edit']);
    queryClient.setQueryData(
      dictOptions(scope, 'sys_a').queryKey,
      [{ label: '旧值', value: '0' }],
      { updatedAt: 1 }
    );
    let complete!: (value: { items: { dictLabel: string; dictValue: string }[] }) => void;
    vi.mocked(getDicts).mockImplementation(
      () =>
        new Promise((resolve) => {
          complete = resolve;
        })
    );
    let finished = false;
    const read = readDict('sys_a').then((value) => {
      finished = true;
      return value;
    });
    await tick();
    expect(finished).toBe(false);
    complete({ items: [{ dictLabel: '新值', dictValue: '0' }] });
    expect((await read)[0].label).toBe('新值');
    endQuerySession();
    await expect(readDict('sys_a')).resolves.toEqual([]);
    expect(unref(dictOptions(null, 'sys_a')).enabled).toBe(false);
    expect(getDicts).toHaveBeenCalledTimes(1);
  });

  it('returns write success even if refresh fails, and a late old-session write cannot populate the new scope', async () => {
    const old = setQuerySession(1, ['admin'], ['system:dict:edit']);
    let finish!: (value: { dictCode: number }) => void;
    vi.mocked(updateData).mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        })
    );
    const save = dictCommands.updateItem(captureDictCommand({ dictCode: 1, dictType: 'sys_a' }));
    endQuerySession();
    const current = setQuerySession(2, [], []);
    queryClient.setQueryData(dictOptions(current, 'sys_a').queryKey, [
      { label: '新账号', value: 'new-user' },
    ]);
    finish({ dictCode: 1 });
    await expect(save).resolves.toEqual({ dictCode: 1 });
    expect(queryClient.getQueryData(dictOptions(current, 'sys_a').queryKey)).toEqual([
      { label: '新账号', value: 'new-user' },
    ]);
    expect(queryClient.getQueryCache().findAll({ queryKey: dictKeys.all(old) })).toHaveLength(0);
  });
  it('rejects an old-session mutation queued offline before executing its write', async () => {
    onlineManager.setOnline(false);
    vi.mocked(updateData).mockResolvedValue({ dictCode: 1 });
    const observer = new MutationObserver(queryClient, {
      mutationFn: dictCommands.updateItem,
      retry: false,
    });
    const result = observer
      .mutate(captureDictCommand({ dictCode: 1, dictType: 'sys_a' }))
      .catch((error: unknown) => error);
    await tick();
    expect(observer.getCurrentResult().isPaused).toBe(true);
    endQuerySession();
    setQuerySession(2, [], []);
    onlineManager.setOnline(true);
    await queryClient.resumePausedMutations();
    await result;
    expect(updateData).not.toHaveBeenCalled();
  });
  it('invalidates live type choices and route metadata together after a type rename', async () => {
    const scope = setQuerySession(1, ['admin'], ['system:dict:edit']);
    vi.mocked(typeApi.optionselect).mockResolvedValue({
      items: [{ dictId: 3, dictType: 'old_type', dictName: '类型' }],
    });
    vi.mocked(typeApi.getType).mockResolvedValue({
      dictId: 3,
      dictType: 'old_type',
      dictName: '类型',
    });
    let choices!: ReturnType<typeof useQuery<readonly import('./dict').DictTypeOption[]>>;
    let detail!: ReturnType<typeof useQuery<import('@/api/system/dict/type').TypeRecord>>;
    const wrapper = mount(
      defineComponent({
        setup() {
          choices = useQuery(dictTypeOptions(scope));
          detail = useQuery(dictTypeDetailOptions(scope, '3'));
          return () => null;
        },
      }),
      { global: { plugins: [[VueQueryPlugin, { queryClient }]] } }
    );
    await tick();
    expect(choices.data.value?.[0].value).toBe('old_type');
    expect(detail.data.value?.dictType).toBe('old_type');
    vi.mocked(typeApi.optionselect).mockResolvedValue({
      items: [{ dictId: 3, dictType: 'new_type', dictName: '新类型' }],
    });
    vi.mocked(typeApi.getType).mockResolvedValue({
      dictId: 3,
      dictType: 'new_type',
      dictName: '新类型',
    });
    vi.mocked(typeApi.updateType).mockResolvedValue({ dictId: 3 });
    await dictCommands.updateType(captureDictCommand({ dictId: 3, dictType: 'new_type' }));
    await tick();
    expect(choices.data.value?.[0].value).toBe('new_type');
    expect(detail.data.value?.dictType).toBe('new_type');
    wrapper.unmount();
  });
});
