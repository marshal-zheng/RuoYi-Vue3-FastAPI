import type { PostApi, PostDto, PostValues, ServerIssue } from './domain';
import type { FieldIssue, RuleFor, Save } from '@zxio/schema-form/form-create';

export function createPostRules(): RuleFor<PostValues>[] {
  return [
    {
      type: 'ZxInput',
      field: 'postName',
      title: '岗位名称',
      validate: [{
        type: 'string', required: true, whitespace: true, max: 50,
        message: '岗位名称不能为空或全为空白，且不能超过50个字符',
      }],
    },
    {
      type: 'ZxInput',
      field: 'postCode',
      title: '岗位编码',
      validate: [{
        type: 'string', required: true, whitespace: true, max: 64,
        message: '岗位编码不能为空或全为空白，且不能超过64个字符',
      }],
    },
    {
      type: 'ZxInputNumber',
      field: 'postSort',
      title: '显示顺序',
      props: { min: 0, precision: 0 },
      validate: [{
        type: 'integer', required: true, min: 0,
        message: '显示顺序必须为非负整数',
      }],
    },
    {
      type: 'ZxInput',
      field: 'status',
      title: '状态',
      props: { placeholder: '0：正常；1：停用' },
      validate: [{
        type: 'enum', required: true, enum: ['0', '1'],
        message: '状态必须为0（正常）或1（停用）',
      }],
    },
    {
      type: 'ZxInput',
      field: 'remark',
      title: '备注',
      props: { type: 'textarea', rows: 3 },
      fullWidth: true,
    },
  ];
}

export function toPostDto(values: PostValues, postId?: number): PostDto {
  const { postName, postCode, postSort, status, remark } = values;
  if (typeof postName !== 'string' || !postName.trim() || postName.length > 50) {
    throw new TypeError('岗位名称不能为空或全为空白，且不能超过50个字符');
  }
  if (typeof postCode !== 'string' || !postCode.trim() || postCode.length > 64) {
    throw new TypeError('岗位编码不能为空或全为空白，且不能超过64个字符');
  }
  if (typeof postSort !== 'number' || !Number.isInteger(postSort) || postSort < 0) {
    throw new TypeError('显示顺序必须为非负整数');
  }
  if (status !== '0' && status !== '1') {
    throw new TypeError('状态必须为0（正常）或1（停用）');
  }
  if (typeof remark !== 'string') {
    throw new TypeError('备注必须为文本');
  }
  const dto: PostDto = { postName, postCode, postSort, status, remark };
  if (postId !== undefined) dto.postId = postId;
  return dto;
}

const issueFields = new Map<string, keyof PostValues>([
  ['post_name', 'postName'],
  ['post_code', 'postCode'],
  ['post_sort', 'postSort'],
  ['status', 'status'],
  ['remark', 'remark'],
]);

export function postFieldIssues(errors: readonly ServerIssue[]): FieldIssue[] {
  return errors.map(({ field, message }): FieldIssue => {
    const target = issueFields.get(field);
    return target === undefined ? { message } : { path: [target], message };
  });
}

export function createPostSave(api: PostApi, postId?: number): Save<PostValues> {
  return async (values, signal) => {
    const result = await api.write(toPostDto(values, postId), signal);
    if (result.ok) return { ok: true };
    return { ok: false, issues: postFieldIssues(result.errors) };
  };
}
