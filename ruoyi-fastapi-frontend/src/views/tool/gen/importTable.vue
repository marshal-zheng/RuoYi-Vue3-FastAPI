<template>
  <!-- 导入表 -->
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <ZxGridList
      ref="gridListRef"
      :load-data="loadDbTableData"
      :query-transform="queryTransform"
      :load-on-mounted="false"
      class="import-table-grid"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #filters>
            <zx-input
              v-model="query.tableName"
              placeholder="请输入表名称"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <zx-input
              v-model="query.tableComment"
              placeholder="请输入表描述"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
          <template #search>
            <ZxButton
              type="primary"
              icon="Search"
              :loading="loading"
              @click="() => onSearch({ handleRefresh, updateState })"
            >
              搜索
            </ZxButton>
            <ZxButton icon="Refresh" @click="() => onReset({ handleRefresh, updateState })">
              重置
            </ZxButton>
          </template>
        </ZxListToolbar>
      </template>

      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @row-click="clickRow"
          @selection-change="handleSelectionChange"
          height="320px"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="tableName" label="表名称" :show-overflow-tooltip="true" />
          <el-table-column prop="tableComment" label="表描述" :show-overflow-tooltip="true" />
          <el-table-column prop="createTime" label="创建时间" width="160" />
          <el-table-column prop="updateTime" label="更新时间" width="160" />
        </el-table>
      </template>
    </ZxGridList>
  </ZxDialog>
</template>

<script setup>
import { ElMessage } from 'element-plus';
import { listDbTable, importTable } from '@/api/tool/gen';
import { useDialog } from '@zxio/zxui';
import { serializeDateRange } from '@/utils/ruoyi';

const gridListRef = ref(null);
const tables = ref([]);

const emit = defineEmits(['ok']);

const { dialogProps, dialogEvents, open, close } = useDialog({
  dialogSize: 'lg',
  title: '导入表',

  defaultData: () => ({}),
  onConfirm: handleImportTable,
});

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** 加载数据库表数据 */
async function loadDbTableData(params) {
  return await listDbTable(params);
}

/** 查询参数列表 */
function show() {
  tables.value = [];
  // 打开对话框后再加载数据
  open();
  // 延迟加载以确保对话框已打开
  nextTick(() => {
    gridListRef.value?.refresh();
  });
}

/** 单击选择行 */
function clickRow(row) {
  const table = gridListRef.value?.$refs?.tableRef;
  table?.toggleRowSelection(row);
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  tables.value = selection.map((item) => item.tableName);
}

/** 搜索 */
function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}

/** 重置 */
function onReset({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  updateState('query', {});
  handleRefresh();
}

/** 导入按钮操作 */
function handleImportTable() {
  const tableNames = tables.value.join(',');
  if (tableNames === '') {
    ElMessage.error('请选择要导入的表');
    return false; // 返回 false 阻止关闭，不会触发额外的错误处理
  }
  return importTable({ tables: tableNames }).then(() => {
    close();
    emit('ok');
    return true; // 返回 true 表示成功
  });
}

defineExpose({
  show,
});
</script>

<style scoped>
.import-table-grid {
  height: 100%;
}

.import-table-grid :deep(.zx-grid-list__content) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.import-table-grid :deep(.zx-grid-list__table) {
  flex: 1;
  overflow: hidden;
}
</style>
