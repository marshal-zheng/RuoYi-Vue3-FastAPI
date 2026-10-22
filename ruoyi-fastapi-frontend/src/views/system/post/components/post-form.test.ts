import { describe, expect, it } from 'vitest';
import { initialPost, postFieldIssues, toPostDto } from './post-form';

const valid = {
  postName: '业务岗位',
  postCode: 'business',
  postSort: 0,
  status: '0',
  remark: null,
};

describe('post write boundary', () => {
  it('routes structured server fields and leaves unstructured conflicts at form level', () => {
    expect(postFieldIssues(new Error('岗位名称已存在'))).toEqual([]);
    expect(
      postFieldIssues({
        problem: {
          type: 'validation-error',
          title: '字段不合法',
          status: 422,
          detail: '字段不合法',
          instance: '/system/post',
          errors: [
            { field: 'post_name', message: '名称不能为空' },
            { field: 'postCode', message: '编码不能为空' },
            { field: 'unknown', message: '其他问题' },
            { field: '', message: '表单无法保存' },
          ],
        },
      })
    ).toEqual([
      { path: ['postName'], message: '名称不能为空' },
      { path: ['postCode'], message: '编码不能为空' },
      { path: ['unknown'], message: '其他问题' },
      { message: '表单无法保存' },
    ]);
  });

  it('keeps zero sort and empty remark, while identity and audit fields cannot leak from inputs', () => {
    expect(initialPost({ postSort: 0, status: '1', remark: null })).toMatchObject({
      postSort: 0,
      status: '1',
      remark: null,
    });
    expect(toPostDto({ ...valid, postId: 999, createBy: 'forged' }, 7)).toEqual({
      ...valid,
      postId: 7,
    });
    expect(toPostDto({ ...valid, postId: 999 })).not.toHaveProperty('postId');
  });

  it.each([
    { postName: ' ' },
    { postName: '名'.repeat(51) },
    { postCode: '' },
    { postCode: 'c'.repeat(65) },
    { postSort: -1 },
    { postSort: 1.5 },
    { postSort: '0' },
    { status: 0 },
    { status: 'deleted' },
    { remark: 'old string' },
  ])('rejects malformed runtime values before reaching the API: %j', (invalid) => {
    expect(() => toPostDto({ ...valid, ...invalid })).toThrow('岗位数据格式不正确');
  });
});
