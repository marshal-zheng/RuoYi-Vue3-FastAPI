import { isField, type FieldDataSource } from '@formily/core';
import type {
  BusinessContext,
  FieldIssue,
  NativeSchema,
  SchemaNode,
  SchemaProperties,
} from '@zxio/schema-form/formily';
import type {
  UserCreateModel,
  UserDetailReadModel,
  UserUpdateModel,
} from '@/api/_generated/types.gen';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { isRecord } from '@/types/http-contract';

export interface UserValues {
  deptId: number | null;
  userName: string;
  nickName: string;
  password: string;
  phonenumber: string;
  email: string;
  sex: '0' | '1' | '2' | null;
  status: '0' | '1';
  remark: RemarkValue;
  postIds: number[];
  roleIds: number[];
}
export function initialUser(response?: UserDetailReadModel): UserValues {
  const user = response?.data;
  return {
    deptId: user?.deptId ?? null,
    userName: user?.userName ?? '',
    nickName: user?.nickName ?? '',
    password: '',
    phonenumber: user?.phonenumber ?? '',
    email: user?.email ?? '',
    sex: user?.sex ?? null,
    status: user?.status ?? '0',
    remark: readRemark(user?.remark),
    postIds: [...(response?.postIds ?? [])],
    roleIds: [...(response?.roleIds ?? [])],
  };
}
const phone = /^1[3-9][0-9]\d{8}$/;
const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const ids = (value: unknown): value is number[] =>
  Array.isArray(value) && value.every((id) => Number.isSafeInteger(id) && id > 0);
export function userIssues(values: UserValues, creating: boolean): FieldIssue<UserValues>[] {
  const issues: FieldIssue<UserValues>[] = [];
  const check = (field: keyof UserValues, valid: boolean, message: string) => {
    if (!valid) issues.push({ path: [field], message });
  };
  check(
    'nickName',
    typeof values.nickName === 'string' && !!values.nickName.trim() && values.nickName.length <= 30,
    '用户昵称不能为空且不能超过 30 个字符'
  );
  if (creating) {
    check(
      'userName',
      typeof values.userName === 'string' &&
        values.userName.trim().length >= 2 &&
        values.userName.length <= 20,
      '用户名称长度必须介于 2 和 20 之间'
    );
    check(
      'password',
      typeof values.password === 'string' &&
        values.password.length >= 5 &&
        values.password.length <= 20 &&
        /^[^<>"'|\\]+$/.test(values.password),
      '用户密码需为 5–20 个字符，且不能包含 < > " \' \\ |'
    );
  }
  check(
    'phonenumber',
    typeof values.phonenumber === 'string' &&
      (!values.phonenumber || phone.test(values.phonenumber)),
    '请输入正确的手机号码'
  );
  check(
    'email',
    typeof values.email === 'string' &&
      values.email.length <= 50 &&
      (!values.email || email.test(values.email)),
    '请输入正确的邮箱地址'
  );
  check(
    'deptId',
    values.deptId == null || (Number.isSafeInteger(values.deptId) && values.deptId > 0),
    '请选择有效的部门'
  );
  check('sex', values.sex == null || ['0', '1', '2'].includes(values.sex), '请选择有效的性别');
  check('status', values.status === '0' || values.status === '1', '请选择有效的状态');
  for (const name of ['postIds', 'roleIds'] as const)
    check(name, ids(values[name]), '请选择有效的选项');
  try {
    if (values.remark === undefined) throw new Error('missing remark');
    readRemark(values.remark);
  } catch {
    issues.push({ path: ['remark'], message: '备注格式不正确' });
  }
  return issues;
}
/** Identity, password-on-edit and server metadata never come from editable values. */
export function toUserDto(values: UserValues, userId?: number): UserCreateModel | UserUpdateModel {
  if (userIssues(values, userId === undefined).length)
    throw new Error('用户数据格式不正确，请检查填写内容');
  const payload = {
    deptId: values.deptId ?? null,
    nickName: values.nickName,
    phonenumber: values.phonenumber,
    email: values.email,
    sex: values.sex ?? null,
    status: values.status,
    remark: readRemark(values.remark),
    postIds: [...values.postIds],
    roleIds: [...values.roleIds],
  };
  return userId === undefined
    ? { ...payload, userName: values.userName, password: values.password }
    : { ...payload, userId };
}
export function userFieldIssues(error: unknown): FieldIssue<UserValues>[] {
  const problem = isRecord(error) && isRecord(error.problem) ? error.problem : undefined;
  if (!problem) return [];
  const aliases: Record<string, keyof UserValues> = {
    user_name: 'userName',
    nick_name: 'nickName',
    dept_id: 'deptId',
    role_ids: 'roleIds',
    post_ids: 'postIds',
  };
  const known: (keyof UserValues)[] = [
    'deptId',
    'userName',
    'nickName',
    'password',
    'phonenumber',
    'email',
    'sex',
    'status',
    'remark',
    'postIds',
    'roleIds',
  ];
  const issues = Array.isArray(problem.errors)
    ? problem.errors.flatMap<FieldIssue<UserValues>>((issue) => {
        if (!isRecord(issue) || typeof issue.message !== 'string') return [];
        const field =
          typeof issue.field === 'string' ? (aliases[issue.field] ?? issue.field) : undefined;
        const path = known.find((name) => name === field);
        return [
          {
            ...(path ? { path: [path] } : {}),
            message: issue.message,
          },
        ];
      })
    : [];
  if (issues.length) return issues;
  const conflict: Record<string, keyof UserValues> = {
    '30006': 'userName',
    '30007': 'phonenumber',
    '30008': 'email',
  };
  const field = conflict[String(problem.errorCode)];
  return field
    ? [
        {
          path: [field],
          message: typeof problem.detail === 'string' ? problem.detail : '该值已被使用',
        },
      ]
    : [];
}

export function createUserSchema(resources: {
  creating: boolean;
  departments(): FieldDataSource;
  departmentCache(): FieldDataSource;
  departmentLoading(): boolean;
  posts(): {
    postId?: number | null;
    postName?: string | null;
    status?: string | null;
  }[];
  roles(): {
    roleId?: number | null;
    roleName?: string | null;
    status?: string | null;
  }[];
  statuses(): readonly { label: string; value: string }[];
  active(): boolean;
}) {
  return (ctx: BusinessContext<UserValues>): NativeSchema => {
    const rule = (name: keyof UserValues) => [
      {
        triggerType: 'onInput',
        validator: () =>
          userIssues(ctx.read(), resources.creating).find((issue) => issue.path?.[0] === name)
            ?.message ?? '',
      },
    ];
    const treeProps = () => ({
      nodeKey: 'id',
      valueKey: 'id',
      props: { value: 'id', label: 'label', children: 'children' },
      checkStrictly: true,
      clearable: true,
      filterable: true,
      placeholder: '请选择归属部门',
      cacheData: resources.departmentCache(),
      loading: resources.departmentLoading(),
    });
    const postOptions = () =>
      resources.posts().map((item) => ({
        label: item.postName ?? '',
        value: item.postId,
        disabled: item.status === '1',
      }));
    const roleOptions = () =>
      resources.roles().map((item) => ({
        label: item.roleName ?? '',
        value: item.roleId,
        disabled: item.status === '1',
      }));
    ctx.bindResource(
      () => ({
        tree: resources.departments(),
        props: treeProps(),
        posts: postOptions(),
        roles: roleOptions(),
        statuses: [...resources.statuses()],
        active: resources.active(),
      }),
      (value) => {
        for (const [name, patch] of Object.entries({
          deptId: { dataSource: value.tree, componentProps: value.props },
          postIds: { dataSource: value.posts },
          roleIds: { dataSource: value.roles },
          status: { dataSource: value.statuses },
          sex: {
            componentProps: {
              dictType: 'sys_user_sex',
              active: value.active,
              placeholder: '请选择',
            },
          },
        })) {
          ctx.form.query(name).forEach((field) => {
            if (isField(field)) ctx.configure(field, patch);
          });
        }
      }
    );
    const input = (
      name: keyof UserValues,
      title: string,
      maxlength: number
    ): SchemaNode<string> => ({
      type: 'string',
      title,
      'x-component': 'ZxInput',
      'x-component-props': { placeholder: `请输入${title}`, maxlength },
      'x-validator': rule(name),
    });
    return {
      type: 'object',
      properties: {
        nickName: {
          required: true,
          ...input('nickName', '用户昵称', 30),
          'x-ai-context': { itemId: 'nickName' },
        },
        deptId: {
          type: 'number',
          title: '归属部门',
          'x-component': 'ZxTreeSelect',
          'x-component-props': {
            ...treeProps(),
            data: resources.departments(),
          },
          'x-validator': rule('deptId'),
        },
        phonenumber: {
          ...input('phonenumber', '手机号码', 11),
          'x-ai-context': { itemId: 'phonenumber' },
        },
        email: {
          ...input('email', '邮箱', 50),
          'x-ai-context': { itemId: 'email' },
        },
        ...(resources.creating
          ? {
              userName: { ...input('userName', '用户名称', 20), required: true },
              password: {
                required: true,
                ...input('password', '用户密码', 20),
                'x-component-props': {
                  placeholder: '请输入用户密码',
                  type: 'password',
                  maxlength: 20,
                  showPassword: true,
                },
              },
            }
          : {}),
        sex: {
          type: 'string',
          title: '用户性别',
          'x-component': 'UserDictSelect',
          'x-component-props': {
            dictType: 'sys_user_sex',
            active: resources.active(),
            placeholder: '请选择',
          },
          'x-validator': rule('sex'),
        },
        status: {
          type: 'string',
          title: '状态',
          'x-component': 'ZxRadioGroup',
          'x-component-props': { options: resources.statuses() },
          'x-validator': rule('status'),
        },
        postIds: {
          type: 'array',
          title: '岗位',
          'x-component': 'ZxSelect',
          'x-component-props': {
            multiple: true,
            options: postOptions(),
            placeholder: '请选择',
          },
          'x-validator': rule('postIds'),
        },
        roleIds: {
          type: 'array',
          title: '角色',
          'x-component': 'ZxSelect',
          'x-component-props': {
            multiple: true,
            options: roleOptions(),
            placeholder: '请选择',
          },
          'x-validator': rule('roleIds'),
        },
        remark: {
          type: 'object',
          title: '备注',
          'x-component': 'RemarkEditor',
          'x-decorator-props': { class: 'schema-form__full' },
          'x-validator': rule('remark'),
        },
      } satisfies SchemaProperties<UserValues>,
    };
  };
}
