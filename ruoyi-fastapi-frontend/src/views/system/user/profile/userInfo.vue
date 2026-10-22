<template>
  <el-form ref="userRef" :model="form" :rules="rules" label-width="80px">
    <el-form-item label="用户昵称" prop="nickName">
      <zx-input v-model="form.nickName" maxlength="30" />
    </el-form-item>
    <el-form-item label="手机号码" prop="phonenumber">
      <zx-input v-model="form.phonenumber" maxlength="11" />
    </el-form-item>
    <el-form-item label="邮箱" prop="email">
      <zx-input v-model="form.email" maxlength="50" />
    </el-form-item>
    <el-form-item label="性别">
      <el-radio-group v-model="form.sex">
        <el-radio value="0">男</el-radio>
        <el-radio value="1">女</el-radio>
      </el-radio-group>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="submit" :loading="submitPending">保存</el-button>
      <el-button @click="close">关闭</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { useOperation } from '@/utils/operation';
import { captureUserCommand, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';

const props = defineProps({
  user: {
    type: Object,
  },
});

const { proxy } = getCurrentInstance();
const profileScope = requireQueryScope();

const form = ref({});
const rules = ref({
  nickName: [{ required: true, message: '用户昵称不能为空', trigger: 'blur' }],
  email: [
    { required: true, message: '邮箱地址不能为空', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] },
  ],
  phonenumber: [
    { required: true, message: '手机号码不能为空', trigger: 'blur' },
    { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' },
  ],
});

/** 提交按钮 */
const { run: submit, pending: submitPending } = useOperation(async () => {
  const scope = profileScope;
  if (scope !== queryScope.value) return;
  const command = captureUserCommand(form.value, scope);
  const valid = await proxy.$refs.userRef.validate().catch(() => false);

  if (valid && scope === queryScope.value) {
    await userCommands.updateProfile(command).then(() => {
      if (scope !== queryScope.value) return;
      props.user.phonenumber = command.input.phonenumber;
      props.user.email = command.input.email;
    });
  }
});

/** 关闭按钮 */
function close() {
  proxy.$tab.closePage();
}

// 回显当前登录用户信息
watch(
  () => props.user,
  (user) => {
    if (user) {
      form.value = {
        nickName: user.nickName,
        phonenumber: user.phonenumber,
        email: user.email,
        sex: user.sex,
      };
    }
  },
  { immediate: true }
);
</script>
