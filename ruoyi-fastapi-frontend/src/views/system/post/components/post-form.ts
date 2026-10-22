import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { isField } from '@formily/core';
import type {
  BusinessContext,
  FieldIssue,
  NativeSchema,
  SettledCheck,
} from '@zxio/schema-form/formily';
import type { PostModel } from '@/api/_generated/types.gen';
import { isProblemDetails, isRecord } from '@/types/http-contract';

export type PostValues = {
  postName: string;
  postCode: string;
  postSort: number;
  status: '0' | '1';
  remark: RemarkValue;
};

export type StatusOption = { label: string; value: '0' | '1' };
const limits = { name: 50, code: 64 } as const;

export function createPostSchema(statusOptions: () => readonly StatusOption[]) {
  let latestOptions = statusOptions();
  const createSchema = (ctx: BusinessContext<PostValues>): NativeSchema => {
    ctx.bindResource(statusOptions, (options) => {
      latestOptions = options;
      ctx.form.query('status').forEach((field) => {
        if (isField(field)) {
          ctx.configure(field, {
            dataSource: [...options],
            componentProps: { options: [...options] },
          });
        }
      });
    });
    const text = (title: string, max: number) => ({
      type: 'string',
      title,
      'x-component': 'ZxInput',
      'x-component-props': { maxlength: max, placeholder: `请输入${title}` },
      'x-validator': [
        {
          required: true,
          triggerType: 'onBlur',
          message: `${title}不能为空且不能超过 ${max} 个字符`,
          validator: (value: unknown) =>
            typeof value === 'string' && !!value.trim() && value.length <= max
              ? ''
              : `${title}不能为空且不能超过 ${max} 个字符`,
        },
      ],
    });
    return {
      type: 'object',
      properties: {
        postName: text('岗位名称', limits.name),
        postCode: text('岗位编码', limits.code),
        postSort: {
          type: 'number',
          title: '岗位顺序',
          'x-component': 'ZxInputNumber',
          'x-component-props': {
            min: 0,
            precision: 0,
            controlsPosition: 'right',
          },
          'x-validator': [
            {
              required: true,
              message: '请输入大于或等于 0 的整数',
              validator: (value: unknown) =>
                typeof value === 'number' && Number.isInteger(value) && value >= 0
                  ? ''
                  : '请输入大于或等于 0 的整数',
            },
          ],
        },
        status: {
          type: 'string',
          title: '岗位状态',
          'x-component': 'ZxRadioGroup',
          'x-component-props': { options: [...latestOptions] },
          'x-validator': [
            {
              required: true,
              message: '请选择岗位状态',
              validator: (value: unknown) =>
                value === '0' || value === '1' ? '' : '请选择岗位状态',
            },
          ],
        },
        remark: {
          type: 'object',
          title: '备注',
          'x-component': 'RemarkEditor',
          'x-component-props': { placeholder: '请输入内容' },
        },
      },
    };
  };
  const assertSettled: SettledCheck<PostValues> = (_values, states) => {
    const state = states.find((item) => item.path[0] === 'status');
    return JSON.stringify(state?.dataSource) === JSON.stringify(latestOptions) &&
      JSON.stringify(state?.componentProps.options) === JSON.stringify(latestOptions)
      ? []
      : [{ message: '岗位状态字典尚未同步' }];
  };
  return { createSchema, assertSettled };
}

export function initialPost(detail?: PostModel): PostValues {
  return {
    postName: detail?.postName ?? '',
    postCode: detail?.postCode ?? '',
    postSort: detail?.postSort ?? 0,
    status: detail?.status ?? '0',
    remark: readRemark(detail?.remark),
  };
}

/** Only editable business fields cross the write boundary; identity belongs to the session. */
export function toPostDto(values: Record<string, unknown>, postId?: number): PostModel {
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
    remark === undefined
  ) {
    throw new Error('岗位数据格式不正确，请检查填写内容');
  }
  let document: RemarkValue;
  try {
    document = readRemark(remark);
  } catch {
    throw new Error('岗位数据格式不正确，请检查备注内容');
  }
  return {
    postName,
    postCode,
    postSort,
    status,
    remark: document,
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
