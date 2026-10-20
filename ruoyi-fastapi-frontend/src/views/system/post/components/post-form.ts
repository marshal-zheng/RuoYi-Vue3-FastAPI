import type { FieldIssue, RuleFor, Values } from '@zxio/schema-form/form-create';
import type { PostModel } from '@/api/_generated/types.gen';
import { isProblemDetails, isRecord } from '@/types/http-contract';

export type PostValues = {
  postName: string;
  postCode: string;
  postSort: number;
  status: '0' | '1';
  remark: string;
};

export type StatusOption = { label: string; value: '0' | '1' };
const limits = { name: 50, code: 64 } as const;

export function createPostRules(
  statusOptions: () => readonly StatusOption[]
): RuleFor<PostValues>[] {
  return [
    {
      type: 'ZxInput',
      field: 'postName',
      title: '岗位名称',
      props: { maxlength: limits.name, placeholder: '请输入岗位名称' },
      validate: [
        {
          required: true,
          whitespace: true,
          max: limits.name,
          message: `岗位名称不能为空且不能超过 ${limits.name} 个字符`,
          trigger: 'blur',
        },
      ],
    },
    {
      type: 'ZxInput',
      field: 'postCode',
      title: '岗位编码',
      props: { maxlength: limits.code, placeholder: '请输入岗位编码' },
      validate: [
        {
          required: true,
          whitespace: true,
          max: limits.code,
          message: `岗位编码不能为空且不能超过 ${limits.code} 个字符`,
          trigger: 'blur',
        },
      ],
    },
    {
      type: 'ZxInputNumber',
      field: 'postSort',
      title: '岗位顺序',
      props: { min: 0, precision: 0, controlsPosition: 'right' },
      validate: [
        {
          required: true,
          type: 'integer',
          min: 0,
          message: '请输入大于或等于 0 的整数',
          trigger: 'change',
        },
      ],
    },
    {
      type: 'ZxRadioGroup',
      field: 'status',
      title: '岗位状态',
      props: { options: statusOptions },
      validate: [
        {
          required: true,
          type: 'enum',
          enum: ['0', '1'],
          message: '请选择岗位状态',
          trigger: 'change',
        },
      ],
    },
    {
      type: 'ZxInput',
      field: 'remark',
      title: '备注',
      props: { type: 'textarea', rows: 3, placeholder: '请输入内容' },
    },
  ];
}

export function initialPost(detail?: PostModel): PostValues {
  return {
    postName: detail?.postName ?? '',
    postCode: detail?.postCode ?? '',
    postSort: detail?.postSort ?? 0,
    status: detail?.status ?? '0',
    remark: detail?.remark ?? '',
  };
}

/** Only editable business fields cross the write boundary; identity belongs to the session. */
export function toPostDto(values: Values, postId?: number): PostModel {
  const { postName, postCode, postSort, status, remark } = values;
  if (
    typeof postName !== 'string' ||
    !postName.trim() ||
    postName.length > limits.name ||
    typeof postCode !== 'string' ||
    !postCode.trim() ||
    postCode.length > limits.code ||
    typeof postSort !== 'number' ||
    !Number.isInteger(postSort) ||
    postSort < 0 ||
    (status !== '0' && status !== '1') ||
    typeof remark !== 'string'
  ) {
    throw new Error('岗位数据格式不正确，请检查填写内容');
  }
  return {
    postName,
    postCode,
    postSort,
    status,
    remark,
    ...(postId === undefined ? {} : { postId }),
  };
}

/** Server field identities are explicit; error messages are never parsed for routing. */
export function postFieldIssues(error: unknown): FieldIssue[] {
  if (
    !isRecord(error) ||
    !isProblemDetails(error.problem) ||
    !Array.isArray(error.problem.errors)
  ) {
    return [];
  }
  const aliases: Record<string, keyof PostValues> = {
    post_name: 'postName',
    post_code: 'postCode',
    post_sort: 'postSort',
  };
  return error.problem.errors.flatMap((issue) =>
    isRecord(issue) && typeof issue.field === 'string' && typeof issue.message === 'string'
      ? [
          {
            ...(issue.field ? { path: [aliases[issue.field] ?? issue.field] } : {}),
            message: issue.message,
          },
        ]
      : []
  );
}
