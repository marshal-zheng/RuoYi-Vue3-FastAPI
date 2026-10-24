import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getMenu } from '@/api/system/menu';
import { getNotice } from '@/api/system/notice';
import { getPost } from '@/api/system/post';
import { getProject } from '@/api/system/project';
import { getProject as getBusinessProject } from '@/api/project/project';
import { getProtocol } from '@/api/protocol/protocol';
import { getData } from '@/api/system/dict/data';

const request = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: request }));
beforeEach(() => request.mockReset());
describe('editor detail read cancellation and feedback options', () => {
  it.each([
    [getMenu, '/system/menu/', 'menuId'],
    [getNotice, '/system/notice/', 'noticeId'],
    [getPost, '/system/post/', 'postId'],
    [getProject, '/project/', 'projectId'],
    [getBusinessProject, '/project/', 'projectId'],
    [getProtocol, '/system/protocol/', 'protocolId'],
    [getData, '/system/dict/data/', 'dictCode'],
  ] as const)('forwards the opening signal and silent feedback for %s', async (read, url, id) => {
    const controller = new AbortController();
    request.mockResolvedValue({ [id]: 11 });
    await read(11, { signal: controller.signal, silentError: true });
    expect(request).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({
        url: url + '11',
        method: 'get',
        signal: controller.signal,
        silentError: true,
      })
    );
  });
});
