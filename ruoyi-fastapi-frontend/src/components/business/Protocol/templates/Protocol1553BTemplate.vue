<template>
  <div class="protocol-template-wrapper">
    <!-- 工具栏 -->
    <div class="table-toolbar flex mb-3">
      <slot name="toolbar">
        <div class="toolbar-left flex items-center gap-2">
          <zx-button type="primary" icon="Plus" size="medium" @click="insertRow"
            >添加字段</zx-button
          >
          <zx-button type="danger" icon="Delete" size="medium" @click="removeSelectRow"
            >删除选中</zx-button
          >
        </div>
      </slot>
    </div>

    <!-- 协议配置表格 -->
    <vxe-table
      border
      show-overflow
      :data="configTableData"
      :span-method="configSpanMethod"
      :edit-config="configTableEditConfig"
      class="text-sm"
    >
      <vxe-column v-for="column in configColumns" :key="column.field" v-bind="column" />
    </vxe-table>

    <!-- 字段列表表格 -->
    <VxeSchemaTable
      class="fields-table text-sm"
      :data="localConfig.fields"
      :columns="fieldSchemaColumns"
      :edit-config="{ trigger: 'click', mode: 'cell' }"
      :edit-rules="vxeEditRules"
      :table-props="{
        border: true,
        resizable: true,
        showOverflow: true,
        keepSource: true,
        treeConfig: { transform: true, rowField: 'id', parentField: 'parentId' },
        checkboxConfig: { checkField: 'checked' },
        spanMethod: fieldSpanMethod,
        rowClassName: getRowClassName,
        cellClassName: getCellClassName,
        tooltipConfig,
        validConfig: vxeValidConfig,
        maxHeight: 500,
      }"
      :hooks="schemaTableHooks"
    >
      <template #actions="{ row }">
        <el-button v-if="row" link type="danger" size="small" @click="removeRow(row)">
          删除
        </el-button>
      </template>
    </VxeSchemaTable>

    <!-- 校验诊断面板 -->
    <VxeValidationPanel
      :issues="validationIssues"
      :auto-expand="true"
      @issue-click="handleIssueClick"
    />

    <!-- 附注区域 -->
    <div class="notes-section mt-4">
      <div class="notes-label font-medium mb-2">附注</div>
      <zx-input
        v-model="localConfig.notes"
        type="textarea"
        :rows="3"
        placeholder="请输入附注信息"
        class="notes-input"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, computed, shallowRef } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type {
  VxeTableInstance,
  VxeTableDefines,
  VxeTablePropTypes,
  VxeTableProps,
} from 'vxe-table';
import type { DictItem } from '@/utils/dict';
import type { ValidationIssue } from '@/components/ui/VxeTableValidation/types';
import type {
  DictAutocompleteCellParams,
  DictAutocompleteRenderOptions,
  DictEditorValue,
} from '@/components/business/VxeDictAutocomplete/types';
import { normalizeConfigEditorValue } from './editorTypes';
import type {
  Protocol1553BConfig,
  ProtocolEditorField,
  ProtocolConfigTableRow,
} from './editorTypes';
import { useDict } from '@/utils/dict';
import {
  useVxeTableValidation,
  VxeValidationPanel,
  required,
} from '@/components/ui/VxeTableValidation';
import VxeSchemaTable from '@/components/ui/VxeSchemaTable/index.vue';
import { createProtocolFieldColumns, createProtocolConfigColumns } from './vxeColumns';

const props = defineProps<{
  modelValue?: Partial<Protocol1553BConfig>;
  protocolType?: string;
  deviceMode?: boolean;
  senderEditable?: boolean;
  receiverEditable?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: Protocol1553BConfig];
}>();

const tableRef = shallowRef<VxeTableInstance<ProtocolEditorField>>();
const schemaTableHooks = {
  onTableReady: (table: VxeTableInstance<ProtocolEditorField>) => {
    tableRef.value = table;
  },
  onEditClosed: handleEditClosed,
};
const configColumns = computed(() => createProtocolConfigColumns(configEditRender));
const fieldSchemaColumns = computed(() => [
  ...createProtocolFieldColumns(),
  {
    field: '__actions',
    title: '操作',
    width: 100,
    fixed: 'right' as const,
    slot: 'actions',
  },
]);

// 获取字典数据
const {
  sys_protocol_method_1553b,
  sys_protocol_frequency,
  sys_protocol_speed_1553b,
  sys_protocol_error_handling,
} = useDict(
  'sys_protocol_method_1553b',
  'sys_protocol_frequency',
  'sys_protocol_speed_1553b',
  'sys_protocol_error_handling'
);

// 初始化校验框架
const {
  issues: validationIssues,
  validate,
  getRowClassName,
  getCellClassName,
  getCellTooltip,
  toVxeEditRules,
  vxeValidConfig,
} = useVxeTableValidation<ProtocolEditorField>({
  rules: {
    fieldName: [required('信息名称不能为空')],
  },
  fieldLabels: {
    fieldName: '信息名称',
    byteCount: '字节数',
    byteSequence: '字节序号',
    valueRange: '值域及含义',
    unit: '量纲',
    dataType: '数据类型',
    scale: '比例尺',
    remark: '备注',
  },
});

const vxeEditRules = computed(toVxeEditRules);

// tooltip 配置：当单元格有校验错误时显示错误提示
const tooltipConfig: VxeTablePropTypes.TooltipConfig<ProtocolEditorField> = {
  showAll: true,
  contentMethod: ({ column, rowIndex }) => {
    return getCellTooltip(rowIndex, column?.field);
  },
};

const defaultConfig: Protocol1553BConfig = {
  sender: '',
  receiver: '',
  frequency: '',
  frequencyLabel: '',
  speed: '',
  speedLabel: '',
  method: '',
  methodLabel: '',
  subAddress: '',
  frameLength: '',
  errorHandle: '',
  errorHandleLabel: '',
  notes: '',
  fields: [],
};

const localConfig = reactive<Protocol1553BConfig>({
  ...defaultConfig,
  ...(props.modelValue || {}),
});

const configTableData = ref<ProtocolConfigTableRow[]>([
  {
    protocolName: '1553B',
    label1: '发送方',
    value1: localConfig.sender,
    label2: '',
    value2: '',
  },
  {
    protocolName: '1553B',
    label1: '接收方',
    value1: localConfig.receiver,
    label2: '',
    value2: '',
  },
  {
    protocolName: '1553B',
    label1: '传输频率',
    value1: localConfig.frequency,
    label2: '传输速率/bps',
    value2: localConfig.speed,
  },
  {
    protocolName: '1553B',
    label1: '传输方式',
    value1: localConfig.method,
    label2: '子地址',
    value2: localConfig.subAddress,
  },
  {
    protocolName: '1553B',
    label1: '帧长度/word',
    value1: localConfig.frameLength,
    label2: '错误处理',
    value2: localConfig.errorHandle,
  },
]);

// 辅助函数：根据字典获取 label
const getLabel = (dict: DictItem[], value: string, fallbackLabel: string = '') => {
  if (!value) return '';
  const found = dict?.find((item) => item.value === value);
  return found ? found.label : fallbackLabel || value;
};

const syncConfigTableRows = () => {
  const rows = configTableData.value;
  rows[0].value1 = localConfig.sender;
  rows[1].value1 = localConfig.receiver;

  // 传输频率
  rows[2].value1 = getLabel(
    sys_protocol_frequency.value,
    localConfig.frequency,
    localConfig.frequencyLabel
  );

  // 传输速率
  rows[2].value2 = getLabel(
    sys_protocol_speed_1553b.value,
    localConfig.speed,
    localConfig.speedLabel
  );

  // 传输方式
  rows[3].value1 = getLabel(
    sys_protocol_method_1553b.value,
    localConfig.method,
    localConfig.methodLabel
  );

  rows[3].value2 = localConfig.subAddress;
  rows[4].value1 = localConfig.frameLength;

  // 错误处理
  rows[4].value2 = getLabel(
    sys_protocol_error_handling.value,
    localConfig.errorHandle,
    localConfig.errorHandleLabel
  );
};

// 监听字典加载完成，重新同步显示
watch(
  [
    sys_protocol_method_1553b,
    sys_protocol_frequency,
    sys_protocol_speed_1553b,
    sys_protocol_error_handling,
  ],
  () => {
    syncConfigTableRows();
  }
);

function configEditRender(
  field: 'value1' | 'value2'
): DictAutocompleteRenderOptions<ProtocolConfigTableRow> {
  const getDictType = (row: Record<string, string>) => {
    if (field === 'value1' && row.label1 === '传输方式') return 'sys_protocol_method_1553b';
    if (field === 'value1' && row.label1 === '传输频率') return 'sys_protocol_frequency';
    if (field === 'value2' && row.label2 === '传输速率/bps') return 'sys_protocol_speed_1553b';
    if (field === 'value2' && row.label2 === '错误处理') return 'sys_protocol_error_handling';
    return '';
  };

  const isNumberField = (row: Record<string, string>) => {
    if (field === 'value2' && row.label2 === '子地址') return true;
    if (field === 'value1' && row.label1 === '帧长度/word') return true;
    return false;
  };

  const isDeviceLockField = (row: Record<string, string>) => {
    const senderLocked = props.deviceMode || props.senderEditable === false;
    const receiverLocked = props.deviceMode || props.receiverEditable === false;
    if (field === 'value1' && row.label1 === '发送方') return senderLocked;
    if (field === 'value2' && row.label2 === '接收方') return receiverLocked;
    return false;
  };

  const handleUpdate = (
    cellParams: DictAutocompleteCellParams<ProtocolConfigTableRow>,
    evtOrValue?: DictEditorValue
  ) => {
    const { row } = cellParams;
    const { value: nextValue, label: nextLabel } = normalizeConfigEditorValue(
      evtOrValue ?? cellParams.value
    );

    if (field === 'value1') {
      if (row.label1 === '发送方') {
        localConfig.sender = nextValue;
      } else if (row.label1 === '接收方') {
        localConfig.receiver = nextValue;
      } else if (row.label1 === '传输频率') {
        localConfig.frequency = nextValue;
        localConfig.frequencyLabel = nextLabel || localConfig.frequencyLabel;
      } else if (row.label1 === '传输方式') {
        localConfig.method = nextValue;
        localConfig.methodLabel = nextLabel || localConfig.methodLabel;
      } else if (row.label1 === '帧长度/word') {
        localConfig.frameLength = nextValue;
      }
    } else if (field === 'value2') {
      if (row.label2 === '传输速率/bps') {
        localConfig.speed = nextValue;
        localConfig.speedLabel = nextLabel || localConfig.speedLabel;
      } else if (row.label2 === '子地址') {
        localConfig.subAddress = nextValue;
      } else if (row.label2 === '错误处理') {
        localConfig.errorHandle = nextValue;
        localConfig.errorHandleLabel = nextLabel || localConfig.errorHandleLabel;
      }
    }
    syncConfigTableRows();
  };

  return {
    name: 'DictAutocomplete',
    props: ({ row }) => {
      const dictType = getDictType(row);
      return {
        dictType,
        placeholder: dictType ? '请输入或选择' : '请输入',
        disabled: isDeviceLockField(row),
        inputType: isNumberField(row) ? 'number' : 'text',
      };
    },
    events: {
      change: (cellParams, value) => handleUpdate(cellParams, value),
      input: (cellParams, value) => handleUpdate(cellParams, value),
    },
  };
}

const configTableEditConfig: VxeTablePropTypes.EditConfig<ProtocolConfigTableRow> = {
  trigger: 'click',
  mode: 'cell',
  activeMethod({ row, column }) {
    const senderLocked = props.deviceMode || props.senderEditable === false;
    const receiverLocked = props.deviceMode || props.receiverEditable === false;
    if (column.field !== 'value1') return true;
    if (row.label1 === '发送方' && senderLocked) return false;
    if (row.label1 === '接收方' && receiverLocked) return false;
    return true;
  },
};

const configSpanMethod = ({ rowIndex, columnIndex }: { rowIndex: number; columnIndex: number }) => {
  if (columnIndex === 0) {
    if (rowIndex === 0) {
      return { rowspan: configTableData.value.length, colspan: 1 };
    }
    return { rowspan: 0, colspan: 0 };
  }

  if ((rowIndex === 0 || rowIndex === 1) && columnIndex === 2) {
    return { rowspan: 1, colspan: 3 };
  }

  if ((rowIndex === 0 || rowIndex === 1) && (columnIndex === 3 || columnIndex === 4)) {
    return { rowspan: 0, colspan: 0 };
  }

  return { rowspan: 1, colspan: 1 };
};

const fieldSpanMethod: VxeTableProps<ProtocolEditorField>['spanMethod'] = ({ columnIndex }) => {
  const valueFieldColIndex = 5;
  const unitColIndex = 6;

  if (columnIndex === valueFieldColIndex) {
    return { rowspan: 1, colspan: 2 };
  } else if (columnIndex === unitColIndex) {
    return { rowspan: 0, colspan: 0 };
  }

  return { rowspan: 1, colspan: 1 };
};

watch(
  () => localConfig,
  (newVal) => {
    syncConfigTableRows();
    emit('update:modelValue', newVal);
    // 自动校验
    if (Array.isArray(localConfig.fields) && localConfig.fields.length > 0) {
      validate(localConfig.fields);
    }
  },
  { deep: true }
);

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && Object.keys(newVal).length > 0) {
      Object.assign(localConfig, newVal);
      syncConfigTableRows();
    }
  },
  { deep: true }
);

const insertRow = () => {
  const newId = Date.now().toString();
  localConfig.fields.push({
    id: newId,
    parentId: null,
    fieldName: '新字段',
    byteCount: 1,
    byteSequence: '',
    valueRange: '',
    unit: '',
    dataType: 'UINT8',
    scale: '1',
    remark: '',
  });
};

const removeRow = (row: ProtocolEditorField) => {
  const index = localConfig.fields.findIndex((item: ProtocolEditorField) => item.id === row.id);
  if (index > -1) {
    localConfig.fields = localConfig.fields.filter(
      (item: ProtocolEditorField) => item.id !== row.id && item.parentId !== row.id
    );
    // message-governance-allow-local: 协议字段编辑器内的本地删除反馈
    ElMessage.success('删除成功');
  }
};

const removeSelectRow = async () => {
  const selectRecords = tableRef.value?.getCheckboxRecords();
  if (!selectRecords || selectRecords.length === 0) {
    ElMessage.warning('请先选择要删除的字段');
    return;
  }

  ElMessageBox.confirm(`确定要删除选中的 ${selectRecords.length} 个字段吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      const deleteIds = selectRecords.map((item: ProtocolEditorField) => item.id);
      localConfig.fields = localConfig.fields.filter(
        (item: ProtocolEditorField) =>
          !deleteIds.includes(item.id) &&
          (item.parentId === null || !deleteIds.includes(item.parentId))
      );
      // message-governance-allow-local: 协议字段编辑器内的本地删除反馈
      ElMessage.success('删除成功');
    })
    .catch(() => {});
};

// 编辑完成后自动校验
function handleEditClosed({
  row,
  column,
}: VxeTableDefines.EditClosedEventParams<ProtocolEditorField>) {
  setTimeout(async () => {
    // 先清除该单元格的 VxeTable 内置校验状态
    if (row && column?.field) {
      await tableRef.value?.clearValidate(row, column.field);
    }
    // 然后运行自定义校验
    if (Array.isArray(localConfig.fields) && localConfig.fields.length > 0) {
      validate(localConfig.fields);
    }
  }, 100);
}

// 点击问题项跳转到对应单元格
const handleIssueClick = (issue: ValidationIssue) => {
  if (issue.rowIndex < 0) return;
  const $table = tableRef.value;
  if (!$table) return;
  const row = localConfig.fields[issue.rowIndex];
  if (!row) return;
  $table.scrollToRow(row);
  $table.setCurrentRow(row);
  if (issue.field) {
    $table.setEditCell(row, issue.field);
  }
};

/**
 * 校验数据（供父组件在保存前调用）
 */
const validateBeforeSave = async (): Promise<boolean> => {
  if (!localConfig.fields || localConfig.fields.length === 0) {
    return true;
  }
  const result = await validate(localConfig.fields);
  if (!result.valid) {
    ElMessage.error(`校验失败：发现 ${result.errorCount} 个错误，请修正后再保存`);
    return false;
  }
  return true;
};

defineExpose({
  insertRow,
  removeSelectRow,
  validateBeforeSave,
  validationIssues,
});
</script>

<style lang="less" scoped>
.protocol-template-wrapper {
  width: 100%;
}

.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  column-gap: 8px;
  display: flex;
  align-items: center;
}

.fields-table {
  :deep(.vxe-cell) {
    padding: 4px 8px;
  }

  :deep(.vxe-tree--indent) {
    width: 16px;
  }
}
</style>
