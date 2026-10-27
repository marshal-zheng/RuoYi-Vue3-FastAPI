<template>
  <DictStatus :types="['sys_normal_disable']" :queries="[typeQuery]" />
  <ZxContentWrap fill>
    <el-alert
      v-if="listStatus.error"
      :title="listStatus.hasData ? '字典数据列表刷新失败，保留上次结果' : '字典数据列表加载失败'"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="refreshList">重试读取</el-button>
    </el-alert>
    <span v-else-if="listStatus.loading && listStatus.hasData" aria-live="polite"
      >正在刷新字典数据列表…</span
    >
    <ZxGridList
      v-if="defaultDictType"
      :key="queryScope?.key"
      ref="gridListRef"
      :load-data="loadDictData"
      :initial-state="initialState"
      fill
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:dict:add']"
              >新增</ZxButton
            >
            <ZxButton
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:dict:edit']"
              >修改</ZxButton
            >
            <ZxButton
              plain
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:dict:remove']"
              :loading="handleDeletePending"
              >删除</ZxButton
            >
            <ZxButton icon="Download" @click="handleExport" v-hasPermi="['system:dict:export']"
              >导出</ZxButton
            >
            <ZxButton icon="Close" @click="handleClose">关闭</ZxButton>
          </template>
          <template #filters>
            <DictTypeSelect
              v-model="query.dictType"
              placeholder="字典名称"
              style="width: 200px"
              @change="(v) => onFilterChange('dictType', v, { handleRefresh, updateState })"
            />
            <DictSelect
              v-model="query.status"
              dict-type="sys_normal_disable"
              placeholder="数据状态"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="query.dictLabel"
              placeholder="搜索字典标签"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
      </template>

      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <template #empty>{{ listStatus.error ? '字典数据列表加载失败' : '暂无数据' }}</template>
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="字典编码" align="center" prop="dictCode" />
          <el-table-column label="字典标签" align="center" prop="dictLabel">
            <template #default="scope">
              <span
                v-if="
                  (scope.row.listClass == '' || scope.row.listClass == 'default') &&
                  (scope.row.cssClass == '' || scope.row.cssClass == null)
                "
                >{{ scope.row.dictLabel }}</span
              >
              <el-tag
                v-else
                :type="scope.row.listClass == 'primary' ? '' : scope.row.listClass"
                :class="scope.row.cssClass"
                >{{ scope.row.dictLabel }}</el-tag
              >
            </template>
          </el-table-column>
          <el-table-column label="字典键值" align="center" prop="dictValue" />
          <el-table-column label="字典排序" align="center" prop="dictSort" />
          <el-table-column label="状态" align="center" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="备注"
            align="center"
            prop="remarkText"
            :show-overflow-tooltip="true"
            ><template #default="scope"
              ><RemarkDisplay
                :value="scope.row.remark"
                :text="scope.row.remarkText"
                summary /></template
          ></el-table-column>
          <el-table-column label="创建时间" align="center" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            align="center"
            width="160"
            fixed="right"
            class-name="small-padding fixed-width"
          >
            <template #default="scope">
              <ZxButton
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:dict:edit']"
                >修改</ZxButton
              >
              <ZxButton
                type="danger"
                link
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:dict:remove']"
                :loading="handleDeletePending"
                >删除</ZxButton
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>

  <!-- 添加或修改参数配置对话框 -->
  <ZxDialog
    v-bind="dataDialog.dialogProps.value"
    v-on="dataDialog.dialogEvents.value"
    :draggable="false"
    :show-full-screen="false"
    :destroy-on-close="false"
    :close-on-click-modal="true"
  >
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="dataRef"
      :model="form"
      :rules="rules"
      v-bind="dataDialog.formProps"
      ><FormGrid v-bind="dataDialog.layoutProps">
        <el-form-item label="字典类型">
          <zx-input v-model="form.dictType" :disabled="true" />
        </el-form-item>
        <el-form-item label="数据标签" prop="dictLabel">
          <zx-input v-model="form.dictLabel" placeholder="请输入数据标签" />
        </el-form-item>
        <el-form-item label="数据键值" prop="dictValue">
          <zx-input v-model="form.dictValue" placeholder="请输入数据键值" />
        </el-form-item>
        <el-form-item label="样式属性" prop="cssClass">
          <zx-input v-model="form.cssClass" placeholder="请输入样式属性" />
        </el-form-item>
        <el-form-item label="显示排序" prop="dictSort">
          <el-input-number v-model="form.dictSort" controls-position="right" :min="0" />
        </el-form-item>
        <el-form-item label="回显样式" prop="listClass">
          <el-select v-model="form.listClass">
            <el-option
              v-for="item in listClassOptions"
              :key="item.value"
              :label="item.label + '(' + item.value + ')'"
              :value="item.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <DictStatus :types="['sys_normal_disable']" />
          <el-radio-group v-model="form.status">
            <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">{{
              dict.label
            }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item data-form-full label="备注" prop="remark">
          <RemarkEditor v-if="open" ref="remarkRef" :key="remarkSession" v-model="form.remark" />
        </el-form-item> </FormGrid
    ></el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button
          type="primary"
          @click="submitForm"
          :loading="submitFormPending"
          :disabled="detailLoading || !!loadError"
          >确 定</el-button
        >
        <el-button @click="cancel">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup name="Data">
import { useAIContextHost } from '@/ai-context/host';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import RemarkDisplay from '@/components/ui/Remark/RemarkDisplay.vue';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import { readRemark } from '@/components/ui/Remark/contract';
import { ref, reactive, computed, toRef, toRefs, getCurrentInstance, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessageBox } from 'element-plus';
import { useEditorRead } from '@/utils/editor-read';
import { useOperation } from '@/utils/operation';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

import { useDictManagement, useDictManagementList } from '@/queries/system/dict-management';
import { queryScope } from '@/queries/context';
import DictSelect from '@/components/business/DictSelect/index.vue';
import DictTypeSelect from '@/components/business/DictTypeSelect/index.vue';
import { useDictTypeDetailQuery } from '@/queries/system/use-dict-query';
import { listData, getData } from '@/api/system/dict/data';

const { proxy } = getCurrentInstance();
const { remarkRef, remarkRule } = useRemarkField();
const remarkSession = ref(0);
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const gridListRef = ref();
const {
  createItem: addData,
  updateItem: updateData,
  deleteItems: delData,
} = useDictManagement(refreshList);
const initialState = ref({ query: {} });

const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const title = ref('');
const route = useRoute();
const { query: typeQuery } = useDictTypeDetailQuery(() => route.params.dictId);
const defaultDictType = computed(() => typeQuery.data.value?.dictType ?? '');
// 数据标签回显样式
const listClassOptions = ref([
  { value: 'default', label: '默认' },
  { value: 'primary', label: '主要' },
  { value: 'success', label: '成功' },
  { value: 'info', label: '信息' },
  { value: 'warning', label: '警告' },
  { value: 'danger', label: '危险' },
]);

const data = reactive({
  rules: {
    remark: [remarkRule],
    dictLabel: [{ required: true, message: '数据标签不能为空', trigger: 'blur' }],
    dictValue: [{ required: true, message: '数据键值不能为空', trigger: 'blur' }],
    dictSort: [{ required: true, message: '数据顺序不能为空', trigger: 'blur' }],
  },
});

const { rules } = toRefs(data);
const dataRef = ref();
const detailLoading = ref(false);
let requestedId;
let editorScope = queryScope.value;
const dataDialog = useFormDialog({
  columns: 1,
  onBeforeClose: canDiscard,
  loading: detailLoading,
  formRef: dataRef,
  title: computed(() => title.value),
  closeOnClickModal: true,
  destroyOnClose: false,
  preValidate: false,
  autoResetForm: false,
  defaultData: () => ({}),
});
const form = toRef(dataDialog.state, 'data');
const open = toRef(dataDialog.state, 'visible');
const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => open.value, detailLoading);

/** GridList 数据加载 */
const { loadData: loadDictData, status: listStatus } = useDictManagementList(
  async (params, options) => {
    const response = await listData(
      {
        ...params.query,
        page: params.pager?.page,
        pageSize: params.pager?.size,
      },
      options
    );
    return response;
  }
);

// Type changes (including rename invalidation) drive this request-mode list's filter once.
watch(
  defaultDictType,
  (type) => {
    if (!type) return;
    initialState.value = {
      ...initialState.value,
      query: { ...initialState.value.query, dictType: type },
    };
    gridListRef.value?.updateState('query.dictType', type);
    refreshList();
  },
  { immediate: true }
);

/** 取消按钮 */
let opening = 0;
let discardPending;
function canDiscard() {
  if (submitFormPending.value) return Promise.resolve(false);
  if (!dataDialog.isDirty.value && remarkRef.value?.validate() !== false)
    return Promise.resolve(true);
  if (discardPending) return discardPending;
  const data = form.value;
  const decision = ElMessageBox.confirm('字典数据尚未保存，是否放弃本次修改？', '未保存的修改', {
    confirmButtonText: '放弃修改',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
    .then(() => data === form.value && !submitFormPending.value)
    .catch(() => false)
    .finally(() => {
      if (discardPending === decision) discardPending = undefined;
    });
  discardPending = decision;
  return decision;
}
async function cancel() {
  opening++;
  if (!(await canDiscard())) return;
  retireEditor();
}
function retireEditor() {
  cancelRead();
  open.value = false;
  reset();
}
/** 表单重置 */
function reset() {
  form.value = {
    dictCode: undefined,
    dictLabel: undefined,
    dictValue: undefined,
    cssClass: undefined,
    listClass: 'default',
    dictSort: 0,
    status: '0',
    remark: null,
  };
  proxy.resetForm('dataRef');
}
/** 刷新列表 */
function refreshList() {
  return gridListRef.value?.refresh();
}

/** 筛选变化 */
function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState(`query.${key}`, value);
  handleRefresh();
}

/** 搜索 */
function onSearch({ handleRefresh }) {
  handleRefresh();
}

/** 返回按钮操作 */
function handleClose() {
  const obj = { path: '/system/dict' };
  proxy.$tab.closeOpenPage(obj);
}
/** 新增按钮操作 */
function handleAdd() {
  return openEditor().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}
/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.dictCode);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 修改按钮操作 */
function handleUpdate(row) {
  const id = row?.dictCode || ids.value[0];
  if (!id) return;
  return openEditor(id).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}
async function openEditor(id) {
  const intent = ++opening;
  if (open.value && !(await canDiscard())) return;
  if (intent !== opening) return;
  remarkSession.value++;
  editorScope = queryScope.value;
  requestedId = id;
  return runRead(async (read) => {
    reset();
    form.value = {
      ...form.value,
      dictCode: id,
      dictType: defaultDictType.value,
    };
    title.value = id ? '修改字典数据' : '添加字典数据';
    open.value = true;
    dataDialog.setDisabled(true);
    if (!id) {
      dataDialog.setDisabled(false);
      return;
    }
    const detail = await getData(id, {
      signal: read.signal,
      silentError: true,
    });
    if (!read.isCurrent()) return;
    form.value = { ...detail, remark: readRemark(detail.remark) };
    dataDialog.setDisabled(false);
  });
}
function handleRetry() {
  return openEditor(requestedId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}
/** 提交按钮 */
const { run: submitForm, pending: submitFormPending } = useOperation(async () => {
  if (
    detailLoading.value ||
    loadError.value ||
    form.value.dictCode !== requestedId ||
    editorScope !== queryScope.value
  )
    return false;
  const valid = await proxy.$refs['dataRef'].validate().catch(() => false);

  if (valid && editorScope === queryScope.value) {
    const scope = queryScope.value;
    const payload = { ...form.value };
    delete payload.remarkText;
    if (form.value.dictCode != undefined) {
      await updateData(payload).then(() => {
        if (scope === queryScope.value) open.value = false;
      });
    } else {
      await addData(payload).then(() => {
        if (scope === queryScope.value) open.value = false;
      });
    }
  }
});
/** 删除按钮操作 */
const { run: handleDelete, pending: handleDeletePending } = useOperation(async (row) => {
  const scope = queryScope.value;
  const dictCodes = row.dictCode || ids.value;
  await proxy.$modal
    .confirm('是否确认删除字典编码为"' + dictCodes + '"的数据项？')
    .then(function () {
      return scope === queryScope.value ? delData(dictCodes) : undefined;
    })
    .catch(() => {});
});
/** 导出按钮操作 */
function handleExport() {
  const snapshot = gridListRef.value?.getStateSnapshot();
  if (!snapshot) return;
  proxy.download(
    'system/dict/data/export',
    snapshot.query,
    `dict_data_${new Date().getTime()}.xlsx`
  );
}

watch(
  queryScope,
  () => {
    opening++;
    retireEditor();
    gridListRef.value?.updateState('list', []);
    ids.value = [];
    single.value = true;
    multiple.value = true;
  },
  { flush: 'sync' }
);

useAIContextHost('dictData', {
  instanceKey: () => remarkSession.value,
  revisionSource: () => [form.value, typeQuery.data.value],
  bindings: {
    dictName: { value: () => typeQuery.data.value?.dictName },
    dictType: { value: () => form.value.dictType },
    dictLabel: { value: () => form.value.dictLabel },
    dictValue: { value: () => form.value.dictValue },
    status: { value: () => (form.value.status === '0' ? '正常' : '停用') },
  },
});
</script>
