<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <span v-if="editorQuery.isPaused.value" aria-live="polite">用户详情等待网络连接</span>
    <el-alert
      v-else-if="editorQuery.error.value && !loadError"
      title="用户详情刷新失败，保留编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryResource">重试读取</el-button>
    </el-alert>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="formRef"
      :model="state.data"
      :rules="formRules"
      :disabled="detailLoading || state.disabled || state.loading || !!loadError"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="用户昵称" prop="nickName">
          <zx-input v-model="state.data.nickName" placeholder="请输入用户昵称" maxlength="30" />
        </el-form-item>

        <el-form-item label="归属部门" prop="deptId">
          <el-tree-select
            v-model="state.data.deptId"
            :data="deptOptions"
            :cache-data="selectedDeptCache"
            :loading="departmentQuery.isLoading.value"
            :props="{ value: 'id', label: 'label', children: 'children' }"
            value-key="id"
            placeholder="请选择归属部门"
            check-strictly
            style="width: 100%"
          >
            <template #label="{ value, label }">
              {{
                selectedDepartment && selectedDepartment.id === value
                  ? selectedDepartment.label
                  : label
              }}
            </template>
          </el-tree-select>
          <span v-if="departmentQuery.isPaused.value" role="status">部门列表等待网络连接</span>
          <el-alert
            v-else-if="departmentQuery.error.value"
            :title="
              departmentQuery.data.value ? '部门列表刷新失败，保留当前选择' : '部门列表读取失败'
            "
            type="error"
            :closable="false"
          >
            <el-button link type="primary" @click="retryDepartments">重试</el-button>
          </el-alert>
        </el-form-item>

        <el-form-item label="手机号码" prop="phonenumber">
          <zx-input v-model="state.data.phonenumber" placeholder="请输入手机号码" maxlength="11" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <zx-input v-model="state.data.email" placeholder="请输入邮箱" maxlength="50" />
        </el-form-item>

        <template v-if="!isEdit">
          <el-form-item label="用户名称" prop="userName">
            <zx-input v-model="state.data.userName" placeholder="请输入用户名称" maxlength="30" />
          </el-form-item>

          <el-form-item label="用户密码" prop="password">
            <zx-input
              v-model="state.data.password"
              placeholder="请输入用户密码"
              type="password"
              maxlength="20"
              show-password
            />
          </el-form-item>
        </template>

        <el-form-item label="用户性别">
          <DictSelect
            dict-type="sys_user_sex"
            :active="state.visible"
            v-model="state.data.sex"
            placeholder="请选择"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="状态">
          <DictStatus :types="['sys_normal_disable']" />
          <el-radio-group v-model="state.data.status">
            <el-radio v-for="dict in statusOptions" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="岗位">
          <el-select v-model="state.data.postIds" multiple placeholder="请选择" style="width: 100%">
            <el-option
              v-for="item in postOptions"
              :key="item.postId"
              :label="item.postName"
              :value="item.postId"
              :disabled="item.status == 1"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="角色">
          <el-select v-model="state.data.roleIds" multiple placeholder="请选择" style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="item.roleId"
              :label="item.roleName"
              :value="item.roleId"
              :disabled="item.status == 1"
            />
          </el-select>
        </el-form-item>

        <el-form-item data-form-full label="备注" prop="remark">
          <RemarkEditor
            v-if="state.visible"
            ref="remarkRef"
            :key="remarkSession"
            v-model="state.data.remark"
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup>
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import { readRemark } from '@/components/ui/Remark/contract';
import { ref, computed, shallowRef, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import { useQuery } from '@tanstack/vue-query';
import { useEditorRead } from '@/utils/editor-read';
import { useDict } from '@/utils/dict';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import {
  captureUserCommand,
  userCommands,
  readUserEditor,
  userDetailOptions,
  userCreateOptions,
} from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { copyUserDeptTree, userDeptTreeOptions } from '@/queries/system/dept';

const { sys_normal_disable: statusOptions } = useDict('sys_normal_disable');

const emit = defineEmits(['success']);

const formRef = ref();
const { remarkRef, remarkRule } = useRemarkField();
const remarkSession = ref(0);
const postOptions = ref([]);
const roleOptions = ref([]);
const detailLoading = ref(false);
const requestedId = ref();
const editorScope = shallowRef(null);
const selectedDepartment = shallowRef(null);

const formRules = computed(() => ({
  remark: [remarkRule],
  userName: [
    { required: true, message: '用户名称不能为空', trigger: 'blur' },
    {
      min: 2,
      max: 20,
      message: '用户名称长度必须介于 2 和 20 之间',
      trigger: 'blur',
    },
  ],
  nickName: [{ required: true, message: '用户昵称不能为空', trigger: 'blur' }],
  password: isEdit.value
    ? []
    : [
        { required: true, message: '用户密码不能为空', trigger: 'blur' },
        {
          min: 5,
          max: 20,
          message: '用户密码长度必须介于 5 和 20 之间',
          trigger: 'blur',
        },
        {
          pattern: /^[^<>"'|\\]+$/,
          message: '不能包含非法字符：< > " \' \\ |',
          trigger: 'blur',
        },
      ],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
  ],
  phonenumber: [
    {
      pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
}));

const {
  formProps,
  layoutProps,
  state,
  dialogProps,
  dialogEvents,
  open,
  close,
  setDisabled,
  isDirty,
} = useFormDialog({
  columns: 2,
  title: (data) => (data?.userId ? '修改用户' : '添加用户'),

  okText: computed(() => (state.data.userId ? '保存' : '创建')),
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  onBeforeClose: canDiscard,
  loading: detailLoading,
  defaultData: () => ({
    userId: undefined,
    deptId: undefined,
    userName: '',
    nickName: '',
    password: '',
    phonenumber: '',
    email: '',
    sex: undefined,
    status: '0',
    remark: null,
    postIds: [],
    roleIds: [],
  }),
  onConfirm: async (data) => {
    const scope = editorScope.value;
    if (
      !state.visible ||
      !scope ||
      scope !== queryScope.value ||
      detailLoading.value ||
      loadError.value
    )
      return false;
    const payload = {
      deptId: data.deptId,
      userName: data.userName,
      nickName: data.nickName,
      phonenumber: data.phonenumber,
      email: data.email,
      sex: data.sex,
      status: data.status,
      remark: data.remark,
      postIds: data.postIds,
      roleIds: data.roleIds,
    };
    if (data.userId) {
      await userCommands.updateUser(captureUserCommand({ ...payload, userId: data.userId }, scope));
    } else {
      await userCommands.createUser(
        captureUserCommand({ ...payload, password: data.password }, scope)
      );
    }
    if (scope !== queryScope.value || state.data !== data) return false;
    emit('success');
  },
  // 错误消息已在 http 层统一处理，无需重复显示
});

const isEdit = computed(() => !!state.data.userId);

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);
const editorQuery = useQuery(
  computed(() => {
    const scope = state.visible ? editorScope.value : null;
    return requestedId.value === undefined
      ? userCreateOptions(scope)
      : userDetailOptions(scope, requestedId.value);
  })
);
const departmentQuery = useQuery(() =>
  userDeptTreeOptions(
    state.visible && editorScope.value === queryScope.value ? editorScope.value : null
  )
);
const deptOptions = computed(() => copyUserDeptTree(departmentQuery.data.value ?? []));
const selectedDeptCache = computed(() =>
  selectedDepartment.value && selectedDepartment.value.id === state.data.deptId
    ? [selectedDepartment.value]
    : []
);
function findDepartment(nodes, id) {
  for (const node of nodes) {
    if (String(node.id) === String(id)) return node;
    const found = node.children && findDepartment(node.children, id);
    if (found) return found;
  }
}
watch(
  [() => state.data.deptId, deptOptions],
  ([id, options]) => {
    if (!state.visible) return;
    const current = findDepartment(options, id);
    if (current) selectedDepartment.value = { id, label: current.label };
    else if (selectedDepartment.value?.id !== id) selectedDepartment.value = null;
  },
  { flush: 'sync' }
);
watch(
  queryScope,
  () => {
    cancelRead();
    selectedDepartment.value = null;
    editorScope.value = null;
    state.visible = false;
  },
  { flush: 'sync' }
);

/** 打开对话框；新增也需要本次打开的岗位和角色选项。 */
let openingIntent = 0;
let approvedClose = false;
let discardPending;
function canDiscard() {
  if (approvedClose || !state.visible) return Promise.resolve(true);
  if (state.loading) return Promise.resolve(false);
  if (detailLoading.value || loadError.value) return Promise.resolve(true);
  if (!isDirty.value && remarkRef.value?.validate?.() !== false) return Promise.resolve(true);
  if (discardPending) return discardPending;
  const data = state.data;
  const scope = editorScope.value;
  const decision = ElMessageBox.confirm('用户信息尚未保存，是否放弃本次修改？', '未保存的修改', {
    confirmButtonText: '放弃修改',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
    .then(
      () => state.visible && state.data === data && scope === queryScope.value && !state.loading
    )
    .catch(() => false)
    .finally(() => {
      if (discardPending === decision) discardPending = undefined;
    });
  discardPending = decision;
  return decision;
}
async function openDialog(userId) {
  const intent = ++openingIntent;
  if (state.visible && state.loading) return;
  if (
    state.visible &&
    !detailLoading.value &&
    !loadError.value &&
    (isDirty.value || remarkRef.value?.validate?.() === false) &&
    !(await canDiscard())
  )
    return;
  if (intent !== openingIntent) return;
  const scope = requireQueryScope();
  editorScope.value = scope;
  requestedId.value = userId;
  return runRead(async (read) => {
    open(userId ? { userId } : undefined);
    postOptions.value = [];
    roleOptions.value = [];
    setDisabled(true);
    remarkSession.value++;
    const response = await readUserEditor(scope, userId, read.signal);
    if (!read.isCurrent() || intent !== openingIntent || scope !== queryScope.value) return;
    postOptions.value = response.posts || [];
    roleOptions.value = response.roles || [];
    if (userId) {
      const userData = response.data;
      if (userData.dept?.deptName) {
        selectedDepartment.value = {
          id: userData.deptId,
          label: userData.dept.deptName,
        };
      }
      open({
        userId: userData.userId,
        deptId: userData.deptId,
        userName: userData.userName,
        nickName: userData.nickName,
        phonenumber: userData.phonenumber,
        email: userData.email,
        sex: userData.sex,
        status: userData.status,
        remark: readRemark(userData.remark),
        postIds: [...(response.postIds || [])],
        roleIds: [...(response.roleIds || [])],
      });
    } else {
      open();
    }
    setDisabled(false);
  });
}

async function closeDialog() {
  if (!(await canDiscard())) return;
  ++openingIntent;
  cancelRead();
  approvedClose = true;
  try {
    await close();
  } finally {
    approvedClose = false;
  }
}

function handleRetry() {
  return openDialog(requestedId.value).catch(() => {
    // 当前读取已负责反馈；重试点击只承接拒绝。
  });
}
function retryResource() {
  if (editorQuery.isEnabled.value) {
    void editorQuery.refetch({ cancelRefetch: false, throwOnError: true }).catch(() => {
      // The observer retains the read failure without replacing the draft.
    });
  }
}
function retryDepartments() {
  if (departmentQuery.isEnabled.value) {
    void departmentQuery.refetch({ cancelRefetch: false, throwOnError: true }).catch(() => {
      // The local observer owns the department read failure; the user draft remains editable.
    });
  }
}

defineExpose({ open: openDialog, close: closeDialog });
watch(
  () => state.visible,
  (visible) => {
    if (visible) remarkSession.value++;
  }
);
</script>
