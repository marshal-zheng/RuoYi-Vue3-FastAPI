import type { PostApi, PostDto, PostValues, ServerIssue } from './domain';
import type { FieldIssue, RuleFor, Save } from '@zxio/schema-form/form-create';

export function createPostRules(): RuleFor<PostValues>[] {
  const col = { span: 24, xs: 24, sm: 24, md: 12, lg: 12, xl: 12 };
  return [
    {
      type: 'ZxInput',
      field: 'postName',
      title: '岗位名称',
      col: { ...col },
      validate: [
        { type: 'string', required: true, whitespace: true, message: '请输入岗位名称，不能全为空白' },
        { type: 'string', max: 50, message: '岗位名称不能超过50个字符' },
      ],
    },
    {
      type: 'ZxInput',
      field: 'postCode',
      title: '岗位编码',
      col: { ...col },
      validate: [
        { type: 'string', required: true, whitespace: true, message: '请输入岗位编码，不能全为空白' },
        { type: 'string', max: 64, message: '岗位编码不能超过64个字符' },
      ],
    },
    {
      type: 'ZxInputNumber',
      field: 'postSort',
      title: '排序',
      col: { ...col },
      props: { min: 0, precision: 0 },
      validate: [
        { type: 'integer', required: true, min: 0, message: '排序必须为非负整数' },
      ],
    },
    {
      type: 'ZxInput',
      field: 'status',
      title: '状态（0正常，1停用）',
      col: { ...col },
      validate: [
        { type: 'enum', required: true, enum: ['0', '1'], message: '状态必须为0或1' },
      ],
    },
    {
      type: 'ZxInput',
      field: 'remark',
      title: '备注',
      col: { span: 24 },
      props: { type: 'textarea', rows: 3 },
    },
  ];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function toPostDto(values: unknown, postId?: number): PostDto {
  if (!isRecord(values)) {
    throw new TypeError('岗位表单值必须为对象');
  }
  const { postName, postCode, postSort, status, remark } = values;
  if (typeof postName !== 'string' || postName.trim().length === 0 || postName.length > 50) {
    throw new TypeError('岗位名称不能为空或全为空白，且不能超过50个字符');
  }
  if (typeof postCode !== 'string' || postCode.trim().length === 0 || postCode.length > 64) {
    throw new TypeError('岗位编码不能为空或全为空白，且不能超过64个字符');
  }
  if (typeof postSort !== 'number' || !Number.isInteger(postSort) || postSort < 0) {
    throw new TypeError('排序必须为非负整数');
  }
  if (status !== '0' && status !== '1') {
    throw new TypeError('状态必须为0或1');
  }
  if (typeof remark !== 'string') {
    throw new TypeError('备注必须为字符串');
  }

  const dto: PostDto = { postName, postCode, postSort, status, remark };
  if (postId !== undefined) dto.postId = postId;
  return dto;
}

const serverFields = new Map<string, keyof PostValues>([
  ['post_name', 'postName'],
  ['post_code', 'postCode'],
  ['post_sort', 'postSort'],
  ['status', 'status'],
  ['remark', 'remark'],
]);

export function postFieldIssues(errors: readonly ServerIssue[]): FieldIssue[] {
  return errors.map(({ field, message }): FieldIssue => {
    const mapped = serverFields.get(field);
    return mapped === undefined ? { message } : { path: [mapped], message };
  });
}

export function createPostSave(api: PostApi, postId?: number): Save<PostValues> {
  return async (values, signal) => {
    const result = await api.write(toPostDto(values, postId), signal);
    if (!result.ok) {
      return { ok: false, issues: postFieldIssues(result.errors) };
    }
    return { ok: true };
  };
}
