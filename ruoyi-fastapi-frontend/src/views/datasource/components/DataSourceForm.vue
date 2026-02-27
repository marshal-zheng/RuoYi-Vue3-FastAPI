<template>
  <el-dialog v-model="visible" title="编辑数据源" width="600px" :close-on-click-modal="false">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" v-loading="detailLoading">
      <el-form-item label="数据源类型">
        <el-tag>{{ typeNameMap[form.type] || form.type }}</el-tag>
      </el-form-item>
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入数据源名称" />
      </el-form-item>
      <el-form-item label="主机" prop="host">
        <el-input v-model="form.host" placeholder="请输入主机地址" />
      </el-form-item>
      <el-form-item label="端口" prop="port">
        <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="form.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
      </el-form-item>
      <el-form-item v-if="form.type === 'mysql' || form.type === 'postgresql'" label="数据库名">
        <el-input v-model="form.databaseName" placeholder="请输入数据库名" />
      </el-form-item>
      <el-form-item v-if="form.type === 'mongodb'" label="数据库名">
        <el-input v-model="form.databaseName" placeholder="请输入数据库名" />
      </el-form-item>
      <el-form-item v-if="form.type === 'mongodb'" label="认证源">
        <el-input v-model="(form.extraConfig as any).auth_source" placeholder="默认 admin" />
      </el-form-item>
      <el-form-item v-if="form.type === 'minio'" label="存储桶">
        <el-input v-model="form.databaseName" placeholder="请输入存储桶名称" />
      </el-form-item>
      <el-form-item v-if="form.type === 'minio'" label="SSL">
        <el-switch v-model="(form.extraConfig as any).use_ssl" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" placeholder="请输入描述" :rows="2" />
      </el-form-item>
      <el-form-item>
        <ZxButton :loading="testLoading" @click="handleTestConnection">测试连接</ZxButton>
        <el-tag v-if="testResult !== null" :type="testResult ? 'success' : 'danger'" style="margin-left: 8px">
          {{ testResult ? '连接成功' : testMessage }}
        </el-tag>
      </el-form-item>
    </el-form>
    <template #footer>
      <ZxButton @click="visible = false">取消</ZxButton>
      <ZxButton type="primary" :loading="submitLoading" @click="handleSubmit">保存</ZxButton>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { getDataSource, updateDataSource, testDataSourceConnection } from '@/api/datasource/datasource';

const emit = defineEmits(['success']);
const typeNameMap: Record<string, string> = {
  mysql: 'MySQL',
  postgresql: 'PostgreSQL',
  mongodb: 'MongoDB',
  minio: 'MinIO',
};

const visible = ref(false);
const detailLoading = ref(false);
const submitLoading = ref(false);
const testLoading = ref(false);
const testResult = ref<boolean | null>(null);
const testMessage = ref('');
const formRef = ref<FormInstance>();

const form = reactive<Record<string, any>>({
  id: undefined,
  name: '',
  type: '',
  host: '',
  port: 3306,
  username: '',
  password: '',
  databaseName: '',
  description: '',
  extraConfig: {},
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入数据源名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
};

async function open(id: number) {
  visible.value = true;
  testResult.value = null;
  testMessage.value = '';
  detailLoading.value = true;
  try {
    const res: any = await getDataSource(id);
    const data = res.data;
    Object.assign(form, {
      id: data.id,
      name: data.name,
      type: data.type,
      host: data.host,
      port: data.port,
      username: data.username,
      password: '',
      databaseName: data.databaseName,
      description: data.description,
      extraConfig: data.extraConfig || {},
    });
  } finally {
    detailLoading.value = false;
  }
}

async function handleTestConnection() {
  testLoading.value = true;
  testResult.value = null;
  try {
    const res: any = await testDataSourceConnection({
      type: form.type,
      host: form.host,
      port: form.port,
      username: form.username,
      password: form.password,
      databaseName: form.databaseName,
      extraConfig: form.extraConfig,
    });
    testResult.value = res.data?.success ?? false;
    testMessage.value = res.data?.message || '连接失败';
  } catch {
    testResult.value = false;
    testMessage.value = '请求失败';
  } finally {
    testLoading.value = false;
  }
}

async function handleSubmit() {
  await formRef.value?.validate();
  submitLoading.value = true;
  try {
    await updateDataSource(form);
    ElMessage.success('修改成功');
    visible.value = false;
    emit('success');
  } finally {
    submitLoading.value = false;
  }
}

defineExpose({ open });
</script>
