import { describe, expect, it } from 'vitest';
import { initialUser, toUserDto, userFieldIssues, userIssues } from './user-form';
import { readRemark } from '@/components/ui/Remark/contract';
import { mockRemark } from '@/mocks/data/remark';

const editable = () => ({
  ...initialUser(),
  nickName: '用户昵称',
  userName: 'new_user',
  password: 'Secret123',
});
describe('user editor contract', () => {
  it('copies authority arrays and writes only the intended create/edit DTO fields', () => {
    const response = {
      data: { userId: 42, userName: 'before', nickName: 'Before', remarkText: '' },
      postIds: [3],
      roleIds: [2],
    };
    const model = initialUser(response);
    model.roleIds.push(9);
    expect(response.roleIds).toEqual([2]);
    const draft = {
      ...editable(),
      userId: 900,
      admin: true,
      loginIp: 'server',
      remarkText: 'server',
      roleIds: [2],
      postIds: [3],
    };
    const create = toUserDto(draft);
    expect(create).toMatchObject({ userName: 'new_user', password: 'Secret123', remark: null });
    expect(create).not.toHaveProperty('userId');
    const update = toUserDto(draft, 42);
    expect(update).toMatchObject({ userId: 42, nickName: '用户昵称', roleIds: [2], postIds: [3] });
    for (const key of ['userName', 'password', 'admin', 'loginIp', 'remarkText'])
      expect(update).not.toHaveProperty(key);
    expect(update.roleIds).not.toBe(draft.roleIds);
  });
  it.each([
    ['nickName', ''],
    ['nickName', 'x'.repeat(31)],
    ['userName', 'x'],
    ['password', 'x<123'],
    ['phonenumber', '1|012345678'],
    ['email', 'not-an-email'],
    ['status', '2'],
    ['sex', '3'],
    ['deptId', -1],
    ['postIds', ['3']],
    ['roleIds', [0]],
    ['remark', 'plain text'],
  ])('rejects malformed %s at the DTO boundary', (name, value) => {
    const draft = { ...editable(), [name]: value };
    expect(userIssues(draft, true)).toEqual(
      expect.arrayContaining([expect.objectContaining({ path: [name] })])
    );
    expect(() => toUserDto(draft)).toThrow();
  });
  it('accepts optional values and preserves rich remark structure including formatting', () => {
    const remark = readRemark(mockRemark('formatted', 'userschema'))!;
    const text = remark.body.content.content[0].content![0];
    if (text.type !== 'text') throw new Error('Expected text fixture');
    text.marks = [{ type: 'bold' }];
    const draft = {
      ...editable(),
      remark,
      phonenumber: '13912345678',
      email: 'person@example.com',
    };
    expect(userIssues(draft, true)).toEqual([]);
    expect(toUserDto(draft).remark).toEqual(remark);
    expect(userIssues({ ...draft, password: '' }, false)).toEqual([]);
  });
  it('maps structured aliases and known conflicts without attaching unknown paths to fields', () => {
    expect(
      userFieldIssues({
        problem: {
          errors: [
            { field: 'nick_name', message: '昵称已被占用' },
            { field: 'serverOnly', message: '需要核查' },
          ],
        },
      })
    ).toEqual([{ path: ['nickName'], message: '昵称已被占用' }, { message: '需要核查' }]);
    expect(userFieldIssues({ problem: { errorCode: 30006, detail: '名称重复' } })).toEqual([
      { path: ['userName'], message: '名称重复' },
    ]);
  });
});
