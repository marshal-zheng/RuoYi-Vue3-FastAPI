<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="formRules" label-width="80px">
      <el-row>
        <el-col :span="12">
          <el-form-item label="用户昵称" prop="nickName">
            <el-input v-model="state.data.nickName" placeholder="请输入用户昵称" maxlength="30" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="归属部门" prop="deptId">
            <el-tree-select
              v-model="state.data.deptId"
              :data="deptOptions"
              :props="{ value: 'id', label: 'label', children: 'children' }"
              value-key="id"
              placeholder="请选择归属部门"
              check-strictly
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="12">
          <el-form-item label="手机号码" prop="phonenumber">
            <el-input
              v-model="state.data.phonenumber"
              placeholder="请输入手机号码"
              maxlength="11"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="state.data.email" placeholder="请输入邮箱" maxlength="50" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row v-if="!isEdit">
        <el-col :span="12">
          <el-form-item label="用户名称" prop="userName">
            <el-input v-model="state.data.userName" placeholder="请输入用户名称" maxlength="30" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="用户密码" prop="password">
            <el-input
              v-model="state.data.password"
              placeholder="请输入用户密码"
              type="password"
              maxlength="20"
              show-password
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="12">
          <el-form-item label="用户性别">
            <el-select v-model="state.data.sex" placeholder="请选择" style="width: 100%">
              <el-option
                v-for="dict in sexOptions"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态">
            <el-radio-group v-model="state.data.status">
              <el-radio v-for="dict in statusOptions" :key="dict.value" :value="dict.value">
                {{ dict.label }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="12">
          <el-form-item label="岗位">
            <el-select
              v-model="state.data.postIds"
              multiple
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="item in postOptions"
                :key="item.postId"
                :label="item.postName"
                :value="item.postId"
                :disabled="item.status == 1"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="角色">
            <el-select
              v-model="state.data.roleIds"
              multiple
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="item in roleOptions"
                :key="item.roleId"
                :label="item.roleName"
                :value="item.roleId"
                :disabled="item.status == 1"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="state.data.remark" type="textarea" placeholder="请输入内容" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </ZxDialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useDialog } from '@zxio/zxui';
import { getUser, addUser, updateUser } from '@/api/system/user';

const props = defineProps({
  deptOptions: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  sexOptions: { type: Array, default: () => [] },
});

const emit = defineEmits(['success']);

const formRef = ref();
const postOptions = ref([]);
const roleOptions = ref([]);

const formRules = computed(() => ({
  userName: [
    { required: true, message: '用户名称不能为空', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名称长度必须介于 2 和 20 之间', trigger: 'blur' },
  ],
  nickName: [{ required: true, message: '用户昵称不能为空', trigger: 'blur' }],
  password: isEdit.value
    ? []
    : [
        { required: true, message: '用户密码不能为空', trigger: 'blur' },
        { min: 5, max: 20, message: '用户密码长度必须介于 5 和 20 之间', trigger: 'blur' },
        { pattern: /^[^<>"'|\\]+$/, message: '不能包含非法字符：< > " \' \\ |', trigger: 'blur' },
      ],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }],
  phonenumber: [
    { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' },
  ],
}));

const { state, dialogProps, dialogEvents, open, close, setLoading } = useDialog({
  title: (data) => (data?.userId ? '修改用户' : '添加用户'),
  height: '60%',
  okText: computed(() => (state.data.userId ? '保存' : '创建')),
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
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
    remark: '',
    postIds: [],
    roleIds: [],
  }),
  onConfirm: async (data) => {
    if (data.userId) {
      await updateUser(data);
    } else {
      await addUser(data);
    }
    emit('success');
  },
  // 错误消息已在 http 层统一处理，无需重复显示
});

const isEdit = computed(() => !!state.data.userId);

/** 打开对话框 */
async function openDialog(userId) {
  setLoading(true);
  try {
    const response = await getUser(userId);
    postOptions.value = response.posts || [];
    roleOptions.value = response.roles || [];

    if (userId) {
      const userData = response || {};
      open({
        userId: userData.userId,
        deptId: userData.deptId,
        userName: userData.userName,
        nickName: userData.nickName,
        phonenumber: userData.phonenumber,
        email: userData.email,
        sex: userData.sex,
        status: userData.status,
        remark: userData.remark,
        postIds: response.postIds || [],
        roleIds: response.roleIds || [],
      });
    } else {
      open();
    }
  } finally {
    setLoading(false);
  }
}

defineExpose({ open: openDialog, close });
</script>
