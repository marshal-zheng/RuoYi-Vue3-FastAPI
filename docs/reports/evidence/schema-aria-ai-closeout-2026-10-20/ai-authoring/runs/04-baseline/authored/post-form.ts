import type { Values } from '@zxio/schema-form';
import type { FieldIssue, RuleFor, Save } from '@zxio/schema-form/form-create';
import type { PostApi, PostDto, PostValues, ServerIssue } from './domain';

export function createPostRules(): RuleFor<PostValues>[] {
  return [
    {
      type: 'ZxInput',
      field: 'postName',
      title: '岗位名称',
      col: { span: 24, md: 12 },
      validate: [{
        type: 'string',
        required: true,
        whitespace: true,
        max: 50,
        message: '岗位名称不能为空或全为空白，且不能超过50个字符',
        trigger: 'blur',
      }],
    },
    {
      type: 'ZxInput',
      field: 'postCode',
      title: '岗位编码',
      col: { span: 24, md: 12 },
      validate: [{
        type: 'string',
        required: true,
        whitespace: true,
        max: 64,
        message: '岗位编码不能为空或全为空白，且不能超过64个字符',
        trigger: 'blur',
      }],
    },
    {
      type: 'ZxInputNumber',
      field: 'postSort',
      title: '显示顺序',
      col: { span: 24, md: 12 },
      props: { min: 0, precision: 0 },
      validate: [{
        type: 'integer',
        required: true,
        min: 0,
        message: '排序必须是非负整数',
        trigger: 'change',
      }],
    },
    {
      type: 'ZxRadioGroup',
      field: 'status',
      title: '状态',
      col: { span: 24, md: 12 },
      props: {
        options: [
          { label: '正常', value: '0' },
          { label: '停用', value: '1' },
        ],
      },
      validate: [{
        type: 'enum',
        required: true,
        enum: ['0', '1'],
        message: '请选择有效状态',
        trigger: 'change',
      }],
    },
    {
      type: 'ZxInput',
      field: 'remark',
      title: '备注',
      col: { span: 24 },
      props: { type: 'textarea', rows: 3 },
      validate: [{ type: 'string', message: '备注必须是文本' }],
    },
  ];
}

export function toPostDto(values: Values | PostValues, postId?: number): PostDto {
  const { postName, postCode, postSort, status, remark } = values;

  if (typeof postName !== 'string' || !postName.trim() || postName.length > 50) {
    throw new Error('岗位名称不能为空或全为空白，且不能超过50个字符');
  }
  if (typeof postCode !== 'string' || !postCode.trim() || postCode.length > 64) {
    throw new Error('岗位编码不能为空或全为空白，且不能超过64个字符');
  }
  if (typeof postSort !== 'number' || !Number.isInteger(postSort) || postSort < 0) {
    throw new Error('排序必须是非负整数');
  }
  if (status !== '0' && status !== '1') {
    throw new Error('请选择有效状态');
  }
  if (typeof remark !== 'string') {
    throw new Error('备注必须是文本');
  }

  const dto: PostDto = { postName, postCode, postSort, status, remark };
  if (postId !== undefined) dto.postId = postId;
  return dto;
}

export function postFieldIssues(errors: readonly ServerIssue[]): FieldIssue[] {
  const fields = new Map<string, keyof PostValues>([
    ['post_name', 'postName'],
    ['post_code', 'postCode'],
    ['post_sort', 'postSort'],
    ['status', 'status'],
    ['remark', 'remark'],
  ]);

  return errors.map(({ field, message }) => ({
    field: fields.get(field) ?? '',
    message,
  }));
}

export function createPostSave(api: PostApi, postId?: number): Save {
  return async (values, signal) => {
    const result = await api.write(toPostDto(values, postId), signal);
    return result.ok
      ? { ok: true }
      : { ok: false, issues: postFieldIssues(result.errors) };
  };
}
