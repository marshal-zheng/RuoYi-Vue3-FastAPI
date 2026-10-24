import { beforeEach, expect, it, vi } from 'vitest';
import { addPost, updatePost } from '@/api/system/post';
const request = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: request }));
beforeEach(() => request.mockReset().mockResolvedValue({ postId: 31 }));

it.each([
  [addPost, 'post', 'system.post.create'],
  [updatePost, 'put', 'system.post.update'],
] as const)(
  'allows the save owner to suppress errors without suppressing HTTP success',
  async (write, method, key) => {
    await write(
      { postName: 'QA', postCode: 'qa', postSort: 0, status: '0' },
      { silentError: true }
    );
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/system/post',
        method,
        silentError: true,
        feedback: { mode: 'auto', key },
      })
    );
  }
);
