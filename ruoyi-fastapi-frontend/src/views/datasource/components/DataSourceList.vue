<template>
  <ZxContentWrap>
    <div class="zx-grid-form-bar">
      <div class="zx-grid-form-bar__left">
        <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['datasource:add']">新增</ZxButton>
        <ZxButton type="danger" icon="Delete" :disabled="multiple" @click="handleBatchDelete" v-hasPermi="['datasource:remove']">删除</ZxButton>
      </div>
      <div class="zx-grid-form-bar__filters">
        <el-input v-model="queryParams.name" placeholder="数据源名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
        <el-select v-model="queryParams.type" placeholder="数据源类型" clearable style="width: 150px">
          <el-option label="MySQL" value="mysql" />
          <el-option label="PostgreSQL" value="postgresql" />
          <el-option label="MongoDB" value="mongodb" />
          <el-option label="MinIO" value="minio" />
        </el-select>
        <el-select v-model="queryParams.status" placeholder="连接状态" clearable style="width: 130px">
          <el-option label="正常" value="online" />
          <el-option label="异常" value="offline" />
        </el-select>
        <ZxButton type="primary" icon="Search" @click="handleQuery">搜索</ZxButton>
        <ZxButton icon="Refresh" @click="resetQuery">重置</ZxButton>
      </div>
    </div>

    <el-table v-loading="loading" :data="dataList" @selection-change="handleSelectionChange" style="width: 100%">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="名称" prop="name" min-width="140" show-overflow-tooltip />
      <el-table-column label="类型" prop="type" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="typeTagMap[row.type]">{{ typeNameMap[row.type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="连接地址" min-width="180">
        <template #default="{ row }">{{ row.host }}:{{ row.port }}</template>
      </el-table-column>
      <el-table-column label="连接状态" prop="status" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'online' ? 'success' : 'danger'" size="small">
            {{ row.status === 'online' ? '正常' : '异常' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <ZxButton link type="primary" icon="Edit" @click="handleEdit(row)" v-hasPermi="['datasource:edit']">编辑</ZxButton>
          <ZxButton link type="primary" icon="Connection" :loading="row._testing" @click="handleTest(row)" v-hasPermi="['datasource:query']">测试</ZxButton>
          <ZxButton link type="danger" icon="Delete" @click="handleDelete(row)" v-hasPermi="['datasource:remove']">删除</ZxButton>
        </template>
      </el-table-column>
    </el-table>

    <Pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />

    <DataSourceWizard ref="wizardRef" @success="getList" />
    <DataSourceForm ref="formRef" @success="getList" />
  </ZxContentWrap>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { listDataSource, delDataSource, testSavedDataSource } from '@/api/datasource/datasource';
import DataSourceWizard from './DataSourceWizard.vue';
import DataSourceForm from './DataSourceForm.vue';

const typeTagMap: Record<string, string> = { mysql: '', postgresql: 'success', mongodb: 'warning', minio: 'info' };
const typeNameMap: Record<string, string> = { mysql: 'MySQL', postgresql: 'PostgreSQL', mongodb: 'MongoDB', minio: 'MinIO' };

const loading = ref(false);
const dataList = ref<any[]>([]);
const total = ref(0);
const ids = ref<number[]>([]);
const multiple = ref(true);
const wizardRef = ref();
const formRef = ref();

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  name: undefined as string | undefined,
  type: undefined as string | undefined,
  status: undefined as string | undefined,
});

function getList() {
  loading.value = true;
  listDataSource(queryParams)
    .then((res: any) => {
      dataList.value = res.rows || [];
      total.value = res.total || 0;
    })
    .finally(() => {
      loading.value = false;
    });
}

function handleQuery() {
  queryParams.pageNum = 1;
  getList();
}

function resetQuery() {
  queryParams.name = undefined;
  queryParams.type = undefined;
  queryParams.status = undefined;
  handleQuery();
}

function handleSelectionChange(selection: any[]) {
  ids.value = selection.map((item: any) => item.id);
  multiple.value = !selection.length;
}

function handleAdd() {
  wizardRef.value?.open();
}

function handleEdit(row: any) {
  formRef.value?.open(row.id);
}

function handleDelete(row: any) {
  ElMessageBox.confirm(`确认删除数据源"${row.name}"？`, '提示', { type: 'warning' })
    .then(() => {
      return delDataSource(row.id);
    })
    .then(() => {
      getList();
      ElMessage.success('删除成功');
    });
}

function handleBatchDelete() {
  ElMessageBox.confirm(`确认删除选中的${ids.value.length}个数据源？`, '提示', { type: 'warning' })
    .then(() => {
      return delDataSource(ids.value.join(','));
    })
    .then(() => {
      getList();
      ElMessage.success('删除成功');
    });
}

function handleTest(row: any) {
  row._testing = true;
  testSavedDataSource(row.id)
    .then((res: any) => {
      if (res.data?.success) {
        ElMessage.success('连接成功');
      } else {
        ElMessage.error(res.data?.message || '连接失败');
      }
      getList();
    })
    .finally(() => {
      row._testing = false;
    });
}

onMounted(() => {
  getList();
});
</script>
