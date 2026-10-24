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
        type: 'string', required: true, whitespace: true, max: 50,
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
        type: 'string', required: true, whitespace: true, max: 64,
        message: '岗位编码不能为空或全为空白，且不能超过64个字符',
        trigger: 'blur',
      }],
    },
    {
      type: 'ZxInputNumber',
      field: 'postSort',
      title: '显示顺序',
      col: { span: 24, md: 12 },
      props: { min: 0, precision: 0, step: 1 },
      validate: [{
        type: 'integer', required: true, min: 0,
        message: '显示顺序必须为非负整数',
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
        type: 'enum', required: true, enum: ['0', '1'],
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
    },
  ];
}

export function toPostDto(values: Values | PostValues, postId?: number): PostDto {
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
    throw new TypeError('状态必须为0或1');
  }
  if (typeof remark !== 'string') {
    throw new TypeError('备注必须为文本');
  }

  const dto: PostDto = { postName, postCode, postSort, status, remark };
  if (postId !== undefined) dto.postId = postId;
  return dto;
}

export function postFieldIssues(errors: readonly ServerIssue[]): FieldIssue[] {
  return errors.map(({ field, message }) => {
    switch (field) {
      case 'post_name': return { field: 'postName', message };
      case 'post_code': return { field: 'postCode', message };
      case 'post_sort': return { field: 'postSort', message };
      default: return { field, message };
    }
  });
}

export function createPostSave(api: PostApi, postId?: number): Save {
  return async (values, signal) => {
    const result = await api.write(toPostDto(values, postId), signal);
    if (result.ok) return { ok: true };
    return { ok: false, issues: postFieldIssues(result.errors) };
  };
}
