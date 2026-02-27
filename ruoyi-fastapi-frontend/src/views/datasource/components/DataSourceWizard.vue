<template>
  <el-dialog v-model="visible" :title="step === 1 ? '选择数据源类型' : '配置数据源'" width="640px" :close-on-click-modal="false" @closed="onClosed">
    <!-- Step 1: Type Selection -->
    <div v-if="step === 1" class="type-cards">
      <div
        v-for="item in typeOptions"
        :key="item.value"
        class="type-card"
        :class="{ active: selectedType === item.value }"
        @click="selectedType = item.value"
      >
        <el-icon :size="36"><component :is="item.icon" /></el-icon>
        <span class="type-card__name">{{ item.label }}</span>
      </div>
    </div>

    <!-- Step 2: Config Form -->
    <el-form v-if="step === 2" ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="数据源类型">
        <el-tag>{{ typeNameMap[form.type] }}</el-tag>
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
        <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
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
        <ZxButton :loading="testLoading" @click="handleTestConnection">
          测试连接
        </ZxButton>
        <el-tag v-if="testResult !== null" :type="testResult ? 'success' : 'danger'" style="margin-left: 8px">
          {{ testResult ? '连接成功' : testMessage }}
        </el-tag>
      </el-form-item>
    </el-form>

    <template #footer>
      <ZxButton @click="visible = false">取消</ZxButton>
      <ZxButton v-if="step === 2" @click="step = 1">上一步</ZxButton>
      <ZxButton v-if="step === 1" type="primary" :disabled="!selectedType" @click="goStep2">下一步</ZxButton>
      <ZxButton v-if="step === 2" type="primary" :loading="submitLoading" @click="handleSubmit">保存</ZxButton>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { Coin, Connection, Box, Folder } from '@element-plus/icons-vue';
import { addDataSource, testDataSourceConnection } from '@/api/datasource/datasource';

const emit = defineEmits(['success']);

const typeOptions = [
  { label: 'MySQL', value: 'mysql', icon: Coin },
  { label: 'PostgreSQL', value: 'postgresql', icon: Connection },
  { label: 'MongoDB', value: 'mongodb', icon: Box },
  { label: 'MinIO', value: 'minio', icon: Folder },
];
const typeNameMap: Record<string, string> = {
  mysql: 'MySQL',
  postgresql: 'PostgreSQL',
  mongodb: 'MongoDB',
  minio: 'MinIO',
};
const defaultPorts: Record<string, number> = { mysql: 3306, postgresql: 5432, mongodb: 27017, minio: 9000 };

const visible = ref(false);
const step = ref(1);
const selectedType = ref('');
const formRef = ref<FormInstance>();
const submitLoading = ref(false);
const testLoading = ref(false);
const testResult = ref<boolean | null>(null);
const testMessage = ref('');

const form = reactive<Record<string, any>>({
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

function open() {
  visible.value = true;
  step.value = 1;
  selectedType.value = '';
  resetForm();
}

function resetForm() {
  Object.assign(form, {
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
  testResult.value = null;
  testMessage.value = '';
}

function goStep2() {
  form.type = selectedType.value;
  form.port = defaultPorts[selectedType.value] || 3306;
  form.extraConfig =
    selectedType.value === 'mongodb'
      ? { auth_source: 'admin' }
      : selectedType.value === 'minio'
        ? { use_ssl: false }
        : {};
  step.value = 2;
}

function onClosed() {
  resetForm();
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
    await addDataSource(form);
    ElMessage.success('新增成功');
    visible.value = false;
    emit('success');
  } finally {
    submitLoading.value = false;
  }
}

defineExpose({ open });
</script>

<style scoped>
.type-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 16px 0;
}
.type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  border: 2px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.type-card:hover {
  border-color: var(--el-color-primary-light-3);
}
.type-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.type-card__name {
  font-size: 14px;
  font-weight: 500;
}
</style>
