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
        <el-button
          v-if="row"
          link
          type="danger"
          size="small"
          @click="removeRow(row)"
        >
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
      <el-input
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
import type { VxeTableInstance } from 'vxe-table';
import { useDict } from '@/utils/dict';
import {
  useVxeTableValidation,
  VxeValidationPanel,
  required,
} from '@/components/VxeTableValidation';
import VxeSchemaTable from '@/components/VxeSchemaTable/index.vue';
import { createProtocolFieldColumns, createProtocolConfigColumns } from './vxeColumns';

const props = defineProps<{
  modelValue?: any;
  protocolType?: string;
  deviceMode?: boolean; // 设备模式：发送方/接收方禁用
  senderEditable?: boolean;
  receiverEditable?: boolean;
  protocolLabel?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: any];
}>();

const tableRef = shallowRef<VxeTableInstance>();
const schemaTableHooks = {
  onTableReady: (table: VxeTableInstance) => {
    tableRef.value = table;
  },
  onEditClosed: handleEditClosed,
};
const configColumns = computed(() => createProtocolConfigColumns(configEditRender));
const fieldSchemaColumns = computed(() => [
  ...createProtocolFieldColumns({
    dataTypeProps: { uppercaseLabel: true },
  }),
  {
    field: '__actions',
    title: '操作',
    width: 100,
    fixed: 'right',
    slot: 'actions',
  },
]);

// 获取字典数据
const {
  sys_protocol_method_rs422,
  sys_protocol_frequency,
  sys_protocol_speed_rs422,
  sys_protocol_error_handling,
} = useDict(
  'sys_protocol_method_rs422',
  'sys_protocol_frequency',
  'sys_protocol_speed_rs422',
  'sys_protocol_error_handling'
);

// 初始化校验框架
const {
  issues: validationIssues,
  errorCount,
  validate,
  getRowClassName,
  getCellClassName,
  getCellTooltip,
  toVxeEditRules,
  vxeValidConfig,
} = useVxeTableValidation({
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
const tooltipConfig = {
  showAll: true,
  contentMethod: ({ row, column, rowIndex }: any) => {
    return getCellTooltip(rowIndex, column?.field);
  },
};

// 数据类型对应的字节长度映射
const DATA_TYPE_BYTE_LENGTH_MAP: Record<string, number> = {
  UINT8: 1,
  INT8: 1,
  UINT16: 2,
  INT16: 2,
  UINT32: 4,
  INT32: 4,
  FLOAT: 4,
  DOUBLE: 8,
  BOOL: 1,
};

// 默认配置
const defaultConfig = {
  sender: '',
  receiver: '',
  frequency: '',
  frequencyLabel: '',
  speed: '',
  speedLabel: '',
  method: '',
  methodLabel: '',
  sendDuration: '',
  frameLength: '',
  errorHandle: '',
  errorHandleLabel: '',
  notes: '',
  fields: [],
};

// 本地配置
const localConfig = reactive({
  ...defaultConfig,
  ...(props.modelValue || {}),
});

// 解析为正整数
const parsePositiveInt = (val: any): number | null => {
  const num = Number(val);
  if (!Number.isFinite(num)) return null;
  if (num <= 0) return null;
  return Math.floor(num);
};

const inferStringByteLength = (field: any): number | null => {
  const manual = parsePositiveInt(field.byteCount);
  if (manual !== null) return manual;
  if (typeof field.valueRange === 'string') {
    const match = field.valueRange.match(/"([^"]+)"/);
    if (match && match[1]) return match[1].length;
  }
  return null;
};

const getByteLengthByType = (field: any): number | null => {
  if (typeof field.dataType === 'string' && field.dataType) {
    const key = field.dataType.toUpperCase();
    if (key === 'STRING') return inferStringByteLength(field);
    const typeLen = DATA_TYPE_BYTE_LENGTH_MAP[key];
    if (typeLen) return typeLen;
  }
  return null;
};

// 根据数据类型和字节数计算每个字段的字节长度
const getFieldByteLength = (field: any): number => {
  const typeLen = getByteLengthByType(field);
  if (typeLen !== null) {
    field.byteCount = typeLen;
    return typeLen;
  }

  const fromCount = parsePositiveInt(field.byteCount);
  if (fromCount !== null) return fromCount;

  field.byteCount = '';
  return 0;
};

const ensureByteCountSync = () => {
  if (!Array.isArray(localConfig.fields)) return;
  localConfig.fields.forEach((field: any) => {
    getFieldByteLength(field);
  });
};

// 根据数据类型/字节数自动计算「字节序号」，从 0 开始，受上一行变动影响
const recalcByteSequence = () => {
  if (!Array.isArray(localConfig.fields)) return;

  let offset = 0;
  localConfig.fields.forEach((field: any) => {
    const length = getFieldByteLength(field);
    if (!length) {
      field.byteSequence = '';
      return;
    }

    const start = offset;
    const end = offset + length - 1;
    field.byteSequence = start === end ? String(start) : `${start}-${end}`;
    offset = end + 1;
  });
};

// 配置表格数据
const protocolLabel = computed(() => props.protocolLabel || 'RS422');

const configTableData = ref([
  {
    protocolName: protocolLabel.value,
    label1: '发送方',
    value1: localConfig.sender,
    label2: '',
    value2: '',
  },
  {
    protocolName: protocolLabel.value,
    label1: '接收方',
    value1: localConfig.receiver,
    label2: '',
    value2: '',
  },
  {
    protocolName: protocolLabel.value,
    label1: '传输频率',
    value1: localConfig.frequency,
    label2: '传输速率/bps',
    value2: localConfig.speed,
  },
  {
    protocolName: protocolLabel.value,
    label1: '传输方式',
    value1: localConfig.method,
    label2: '发送时长/ms',
    value2: localConfig.sendDuration,
  },
  {
    protocolName: protocolLabel.value,
    label1: '帧长度/Byte',
    value1: localConfig.frameLength,
    label2: '错误处理',
    value2: localConfig.errorHandle,
  },
]);

// 辅助函数：根据字典获取 label
const getLabel = (dict: any[], value: string, fallbackLabel: string = '') => {
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
    sys_protocol_speed_rs422.value,
    localConfig.speed,
    localConfig.speedLabel
  );

  // 传输方式
  rows[3].value1 = getLabel(
    sys_protocol_method_rs422.value,
    localConfig.method,
    localConfig.methodLabel
  );

  rows[3].value2 = localConfig.sendDuration;
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
    sys_protocol_method_rs422,
    sys_protocol_frequency,
    sys_protocol_speed_rs422,
    sys_protocol_error_handling,
  ],
  () => {
    syncConfigTableRows();
  }
);

function configEditRender(field: 'value1' | 'value2') {
  const getDictType = (row: Record<string, string>) => {
    if (field === 'value1' && row.label1 === '传输方式') return 'sys_protocol_method_rs422';
    if (field === 'value1' && row.label1 === '传输频率') return 'sys_protocol_frequency';
    if (field === 'value2' && row.label2 === '传输速率/bps') return 'sys_protocol_speed_rs422';
    if (field === 'value2' && row.label2 === '错误处理') return 'sys_protocol_error_handling';
    return '';
  };

  const isNumberField = (row: Record<string, string>) => {
    if (field === 'value2' && row.label2 === '发送时长/ms') return true;
    if (field === 'value1' && row.label1 === '帧长度/Byte') return true;
    return false;
  };

  const isDeviceLockField = (row: Record<string, string>) => {
    const senderLocked = props.deviceMode || props.senderEditable === false;
    const receiverLocked = props.deviceMode || props.receiverEditable === false;
    if (field === 'value1' && row.label1 === '发送方') return senderLocked;
    if (field === 'value2' && row.label2 === '接收方') return receiverLocked;
    return false;
  };

  const extractValue = (evtOrValue: any) => {
    if (evtOrValue && typeof evtOrValue === 'object') {
      if ('value' in evtOrValue) return evtOrValue.value;
      if ('target' in evtOrValue && 'value' in evtOrValue.target) return evtOrValue.target.value;
    }
    return evtOrValue;
  };

  const normalizeValLabel = (raw: any) => {
    if (raw && typeof raw === 'object') {
      return {
        value: 'value' in raw ? raw.value : raw,
        label: 'label' in raw ? raw.label : '',
      };
    }
    return { value: raw, label: '' };
  };

  const handleUpdate = (cellParams: any, evtOrValue: any) => {
    const { row } = cellParams;
    const { value: nextValue, label: nextLabel } = normalizeValLabel(
      extractValue(evtOrValue ?? cellParams?.value)
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
      } else if (row.label1 === '帧长度/Byte') {
        localConfig.frameLength = nextValue;
      }
    } else if (field === 'value2') {
      if (row.label2 === '传输速率/bps') {
        localConfig.speed = nextValue;
        localConfig.speedLabel = nextLabel || localConfig.speedLabel;
      } else if (row.label2 === '发送时长/ms') {
        localConfig.sendDuration = nextValue;
      } else if (row.label2 === '错误处理') {
        localConfig.errorHandle = nextValue;
        localConfig.errorHandleLabel = nextLabel || localConfig.errorHandleLabel;
      }
    }
    syncConfigTableRows();
  };

  return {
    name: 'DictAutocomplete',
    props: ({ row }: any) => {
      const dictType = getDictType(row);
      return {
        dictType,
        placeholder: dictType ? '请输入或选择' : '请输入',
        disabled: isDeviceLockField(row),
        inputType: isNumberField(row) ? 'number' : 'text',
      };
    },
    events: {
      change: (cellParams: any, value: any) => handleUpdate(cellParams, value),
      input: (cellParams: any, value: any) => handleUpdate(cellParams, value),
    },
  };
};

const configTableEditConfig = {
  trigger: 'click',
  mode: 'cell',
  activeMethod({ row, column }: any) {
    if (column.field !== 'value1') return true;
    const senderLocked = props.deviceMode || props.senderEditable === false;
    const receiverLocked = props.deviceMode || props.receiverEditable === false;
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

// 字段表格合并单元格方法
const fieldSpanMethod = ({ columnIndex }: any) => {
  const valueFieldColIndex = 5;
  const unitColIndex = 6;

  if (columnIndex === valueFieldColIndex) {
    return { rowspan: 1, colspan: 2 };
  } else if (columnIndex === unitColIndex) {
    return { rowspan: 0, colspan: 0 };
  }

  return { rowspan: 1, colspan: 1 };
};

// 监听本地配置变化
watch(
  () => localConfig,
  (newVal) => {
    ensureByteCountSync();
    recalcByteSequence();
    syncConfigTableRows();
    emit('update:modelValue', newVal);
    // 自动校验
    if (Array.isArray(localConfig.fields) && localConfig.fields.length > 0) {
      validate(localConfig.fields);
    }
  },
  { deep: true, immediate: true }
);

// 监听外部值变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && Object.keys(newVal).length > 0) {
      Object.assign(localConfig, newVal);
      ensureByteCountSync();
      recalcByteSequence();
      syncConfigTableRows();
    }
  },
  { deep: true }
);

watch(
  protocolLabel,
  (val) => {
    configTableData.value.forEach((row) => {
      row.protocolName = val;
    });
  },
  { immediate: true }
);

// 新增行
const insertRow = () => {
  const newId = Date.now().toString();
  localConfig.fields.push({
    id: newId,
    parentId: null,
    fieldName: '',
    byteCount: '',
    byteSequence: '',
    valueRange: '',
    unit: '',
    dataType: '',
    scale: '1',
    remark: '',
  });
};

// 删除行
const removeRow = (row: any) => {
  const index = localConfig.fields.findIndex((item: any) => item.id === row.id);
  if (index > -1) {
    localConfig.fields = localConfig.fields.filter(
      (item: any) => item.id !== row.id && item.parentId !== row.id
    );
    ElMessage.success('删除成功');
  }
};

// 删除选中
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
      const deleteIds = selectRecords.map((item: any) => item.id);
      localConfig.fields = localConfig.fields.filter(
        (item: any) => !deleteIds.includes(item.id) && !deleteIds.includes(item.parentId)
      );
      ElMessage.success('删除成功');
    })
    .catch(() => {});
};

// 编辑完成后自动校验
function handleEditClosed({ row, column }: any) {
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
const handleIssueClick = (issue: any) => {
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
  :deep(.vxe-body--row.row--hover) {
    background-color: #f5f7fa;
  }

  :deep(.vxe-cell) {
    padding: 4px 8px;
  }

  :deep(.vxe-tree--indent) {
    width: 16px;
  }
}
</style>
