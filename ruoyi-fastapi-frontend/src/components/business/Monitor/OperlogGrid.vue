<template>
  <div class="m-operlog-grid" data-zx-fill>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadOperlogData"
      :query-transform="queryTransform"
      :defaults="defaults"
      fill
    >
      <template #form="listForm">
        <template v-if="listForm.mode === 'request'">
          <DictStatus :types="['sys_oper_type', 'sys_common_status']" />
          <ZxListToolbar aria-label="列表操作与筛选">
            <template #filters>
              <slot
                name="filters"
                :draft="listForm.draft"
                :loading="listForm.loading"
                :search="listForm.search"
                :set-draft="listForm.setDraft"
              >
                <zx-input
                  v-model="listForm.draft.title"
                  placeholder="系统模块"
                  clearable
                  style="width: 200px; margin-left: 8px"
                  @keyup.enter="() => listForm.search()"
                />
                <OperTypeSelector
                  v-model="listForm.draft.businessType"
                  placeholder="类型"
                  style="width: 160px; margin-left: 8px"
                  @change="() => listForm.search()"
                />
                <OperStatusSelector
                  v-model="listForm.draft.status"
                  placeholder="状态"
                  style="width: 160px; margin-left: 8px"
                  @change="() => listForm.search()"
                />
                <el-date-picker
                  v-model="listForm.draft.dateRange"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  type="daterange"
                  range-separator="-"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  :default-time="[new Date(2000, 1, 1, 0, 0, 0), new Date(2000, 1, 1, 23, 59, 59)]"
                  style="margin-left: 8px; width: 308px"
                  @change="() => listForm.search()"
                />
              </slot>
            </template>
            <template #search>
              <ZxSearch
                v-model="listForm.draft.operName"
                placeholder="搜索操作人员"
                :loading="listForm.loading"
                search-mode="click"
                @search="() => listForm.search()"
                @clear="() => listForm.search()"
              />
            </template>
          </ZxListToolbar>
        </template>
      </template>

      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="(val) => onSelectionChange(val)"
          ref="sortTableRef"
          @sort-change="onSortChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column label="日志编号" prop="operId" />
          <el-table-column label="系统模块" prop="title" :show-overflow-tooltip="true" />
          <el-table-column label="操作类型" prop="businessType">
            <template #default="scope">
              <dict-tag :options="sys_oper_type" :value="scope.row.businessType" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作人员"
            width="110"
            prop="operName"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          />
          <el-table-column
            label="操作地址"
            prop="operIp"
            width="130"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="操作状态" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_common_status" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作日期"
            prop="operTime"
            width="180"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          >
            <template #default="scope">
              <span>{{ parseTime(scope.row.operTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="消耗时间"
            prop="costTime"
            width="110"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          >
            <template #default="scope">
              <span>{{ scope.row.costTime }}毫秒</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                @click="handleView(scope.row)"
                v-hasPermi="['monitor:operlog:query']"
                >查看</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <OperlogDetailDialog ref="detailDialogRef" />
  </div>
</template>

<script setup>
import { useGridTableSort } from '@/composables/useGridTableSort';
import { ZxGridList } from '@zxio/zxui/grid-list';
import { normalizeGridParams } from '@/utils/grid-params';
import { useOperation } from '@/utils/operation';
import { list, delOperlog, cleanOperlog } from '@/api/monitor/operlog';
import { parseTime, serializeDateRange } from '@/utils/ruoyi';
import { OperTypeSelector, OperStatusSelector } from './selector';
import OperlogDetailDialog from './OperlogDetailDialog.vue';

const { proxy } = getCurrentInstance();
const { sys_oper_type, sys_common_status } = proxy.useDict('sys_oper_type', 'sys_common_status');

const props = defineProps({ module: { type: String, default: '' } });
const gridListRef = ref();
const { sortTableRef, onSortChange } = useGridTableSort(gridListRef);
const ids = ref([]);
const detailDialogRef = ref();

const defaults = computed(() => ({
  query: {
    title: props.module || '',
  },
  sort: [{ field: 'operTime', order: 'desc' }],
}));

function queryTransform(query) {
  return serializeDateRange(query);
}

async function loadOperlogData(params) {
  return list({
    ...params.query,
    sort: params.sort,
    page: params.pager?.page,
    pageSize: params.pager?.size,
  });
}

function onSelectionChange(selection) {
  ids.value = selection.map((item) => item.operId);
  emit('selection-change', ids.value);
}

function handleView(row) {
  detailDialogRef.value && detailDialogRef.value.open(row);
}

const { run: deleteSelected } = useOperation(async () => {
  const operIds = ids.value;
  if (!operIds || operIds.length === 0) return;
  await proxy.$modal
    .confirm('是否确认删除日志编号为"' + operIds + '"的数据项?')
    .then(function () {
      return delOperlog(operIds);
    })
    .then(() => {
      gridListRef.value && gridListRef.value.reload();
    })
    .catch(() => {});
});

const { run: cleanAll } = useOperation(async () => {
  await proxy.$modal
    .confirm('是否确认清空所有操作日志数据项?')
    .then(function () {
      return cleanOperlog();
    })
    .then(() => {
      gridListRef.value && gridListRef.value.reload();
    })
    .catch(() => {});
});

function exportCurrent() {
  const snapshot = gridListRef.value?.applied;
  if (!snapshot) return;
  proxy.download(
    'monitor/operlog/export',
    normalizeGridParams({
      query: queryTransform(snapshot.query),
      sort: snapshot.sort,
    }),
    `operlog_${new Date().getTime()}.xlsx`
  );
}

function refresh() {
  gridListRef.value && gridListRef.value.reload();
}

const emit = defineEmits(['selection-change']);

defineExpose({ refresh, deleteSelected, cleanAll, exportCurrent });
</script>
