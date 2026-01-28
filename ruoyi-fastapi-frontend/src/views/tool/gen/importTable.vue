<template>
  <!-- 导入表 -->
  <ZxDialog
    v-model="visible"
    title="导入表"
    width="800px"
    height="600px"
    @confirm="handleImportTable"
  >
    <div class="import-table-content">
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="表名称" prop="tableName">
          <el-input
            v-model="queryParams.tableName"
            placeholder="请输入表名称"
            clearable
            style="width: 180px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="表描述" prop="tableComment">
          <el-input
            v-model="queryParams.tableComment"
            placeholder="请输入表描述"
            clearable
            style="width: 180px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table
        @row-click="clickRow"
        ref="tableRef"
        :data="dbTableList"
        @selection-change="handleSelectionChange"
        height="320px"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column
          prop="tableName"
          label="表名称"
          :show-overflow-tooltip="true"
        />
        <el-table-column
          prop="tableComment"
          label="表描述"
          :show-overflow-tooltip="true"
        />
        <el-table-column prop="createTime" label="创建时间" width="160" />
        <el-table-column prop="updateTime" label="更新时间" width="160" />
      </el-table>
      
      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />
    </div>
  </ZxDialog>
</template>

<script setup>
import { listDbTable, importTable } from '@/api/tool/gen';

const total = ref(0);
const visible = ref(false);
const tables = ref([]);
const dbTableList = ref([]);
const tableRef = ref(null);
const { proxy } = getCurrentInstance();

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  tableName: undefined,
  tableComment: undefined,
});

const emit = defineEmits(['ok']);

/** 查询参数列表 */
function show() {
  queryParams.pageNum = 1;
  queryParams.tableName = undefined;
  queryParams.tableComment = undefined;
  tables.value = [];
  getList();
  visible.value = true;
}

/** 单击选择行 */
function clickRow(row) {
  tableRef.value?.toggleRowSelection(row);
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  tables.value = selection.map((item) => item.tableName);
}

/** 查询表数据 */
function getList() {
  listDbTable(queryParams).then((res) => {
    dbTableList.value = res.rows;
    total.value = res.total;
  });
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.pageNum = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef');
  handleQuery();
}

/** 导入按钮操作 */
function handleImportTable() {
  const tableNames = tables.value.join(',');
  if (tableNames === '') {
    proxy.$modal.msgError('请选择要导入的表');
    return Promise.reject();
  }
  return importTable({ tables: tableNames }).then(() => {
    visible.value = false;
    emit('ok');
  });
}

defineExpose({
  show,
});
</script>

<style scoped>
.import-table-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-form {
  margin-bottom: 16px;
}
</style>
