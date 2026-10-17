import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getConfig, listConfig } from './system/config';
import { getType, optionselect } from './system/dict/type';
import { getData, getDicts } from './system/dict/data';
import { getDept } from './system/dept';
import { getRole } from './system/role';
import { getMenu, treeselect } from './system/menu';
import { getPost } from './system/post';
import { getNotice } from './system/notice';
import { getProject as getSystemProject } from './system/project';
import { getProject } from './project/project';
import { getProjectVersion } from './project/version';
import { getProtocol } from './protocol/protocol';
import { getDevice } from './device/device';
import { getDeviceCategory } from './device/category';
import { getJob } from './monitor/job';
import { getGenTable } from './tool/gen';
import { getUser } from './system/user';

const { transport, feedback } = vi.hoisted(() => ({
  transport: vi.fn(),
  feedback: vi.fn(() => Promise.resolve()),
}));
vi.mock('@/utils/request', () => ({ default: transport }));
vi.mock('@/utils/feedback/message', () => ({ showMessage: feedback }));

const cases = [
  { name: 'config', read: getConfig, field: 'configId' },
  { name: 'dict-type', read: getType, field: 'dictId' },
  { name: 'dict-data', read: getData, field: 'dictCode' },
  { name: 'dept', read: getDept, field: 'deptId' },
  { name: 'role', read: getRole, field: 'roleId' },
  { name: 'menu', read: getMenu, field: 'menuId' },
  { name: 'post', read: getPost, field: 'postId' },
  { name: 'notice', read: getNotice, field: 'noticeId' },
  { name: 'system-project', read: getSystemProject, field: 'projectId' },
  { name: 'project', read: getProject, field: 'projectId' },
  { name: 'version', read: getProjectVersion, field: 'versionId' },
  { name: 'protocol', read: getProtocol, field: 'protocolId' },
  { name: 'device', read: getDevice, field: 'deviceId' },
  { name: 'category', read: getDeviceCategory, field: 'deviceCategoryId' },
  { name: 'job', read: getJob, field: 'jobId' },
  {
    name: 'generator',
    read: getGenTable,
    field: 'tableId',
    wrap: (data: unknown) => ({ info: data, columns: [], tables: [] }),
  },
  {
    name: 'user',
    read: getUser,
    field: 'userId',
    wrap: (data: unknown) => ({ data, posts: [], roles: [] }),
  },
];

beforeEach(() => vi.clearAllMocks());

describe.each(cases)('$name detail identity', ({ read, field, wrap = (data: unknown) => data }) => {
  it.each([null, {}, { [field]: null }, { [field]: 0 }, { [field]: 88 }, { [field]: '77' }])(
    'rejects a missing or foreign identity %j before a caller can open an editor',
    async (detail) => {
      transport.mockResolvedValueOnce(wrap(detail));
      await expect(read(77)).rejects.toMatchObject({ name: 'DetailIdentityError' });
      expect(feedback).toHaveBeenCalledTimes(1);
    }
  );
  it('retains a matching resource and accepts a numeric route ID', async () => {
    const payload = wrap({ [field]: 77 });
    transport.mockResolvedValueOnce(payload);
    expect(await read('77')).toBe(payload);
    expect(feedback).not.toHaveBeenCalled();
  });
  it('preserves the original HTTP failure without reporting it twice', async () => {
    const failure = new Error('HTTP 404');
    transport.mockRejectedValueOnce(failure);
    await expect(read(77)).rejects.toBe(failure);
    expect(feedback).not.toHaveBeenCalled();
  });
});

it('leaves the current editor in charge of a silent identity failure', async () => {
  const controller = new AbortController();
  transport.mockResolvedValueOnce({ configId: 88 });
  await expect(
    getConfig(77, { signal: controller.signal, silentError: true })
  ).rejects.toMatchObject({ name: 'DetailIdentityError' });
  expect(feedback).not.toHaveBeenCalled();
  expect(transport).toHaveBeenCalledWith(
    expect.objectContaining({ signal: controller.signal, silentError: true })
  );
});

it('preserves the user creation options endpoint with an absent user', async () => {
  const options = { data: null, posts: [], roles: [], postIds: [], roleIds: [] };
  transport.mockResolvedValueOnce(options);
  expect(await getUser(undefined)).toBe(options);
  expect(transport).toHaveBeenCalledWith(expect.objectContaining({ url: '/system/user/' }));
  expect(feedback).not.toHaveBeenCalled();
});

it('preserves valid empty lists, options and dictionary collections', async () => {
  const empty = { items: [], total: 0, page: 1, pageSize: 10 };
  transport.mockResolvedValue(empty);
  for (const read of [
    () => listConfig(),
    optionselect,
    treeselect,
    () => getDicts('empty-contract'),
  ]) {
    expect(await read()).toBe(empty);
  }
  expect(feedback).not.toHaveBeenCalled();
});

it('uses the existing HTTP failure feedback for an explicit detail read', async () => {
  const failure = new Error('HTTP 404');
  transport.mockRejectedValueOnce(failure);
  await expect(getProtocol(77)).rejects.toBe(failure);
  expect(transport).toHaveBeenCalledWith(expect.objectContaining({ feedback: { mode: 'auto' } }));
  expect(feedback).not.toHaveBeenCalled();
});
