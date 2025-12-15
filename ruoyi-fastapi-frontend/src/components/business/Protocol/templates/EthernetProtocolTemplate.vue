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
        <div class="toolbar-right flex items-center gap-2">
          <zx-button
            :type="validationIssues.length > 0 ? 'warning' : 'success'"
            icon="Aim"
            size="medium"
            @click="runValidation"
          >
            校验诊断
            <el-badge
              v-if="errorCount > 0"
              :value="errorCount"
              type="danger"
              class="ml-1"
            />
          </zx-button>
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
      <vxe-column field="protocolName" title="" width="80" align="center" />
      <vxe-column field="label1" title="" width="120" align="center" />
      <vxe-column
        field="value1"
        title=""
        min-width="200"
        :edit-render="configEditRender('value1')"
      />
      <vxe-column field="label2" title="" width="140" align="center" />
      <vxe-column
        field="value2"
        title=""
        min-width="200"
        :edit-render="configEditRender('value2')"
      />
    </vxe-table>

    <!-- 字段列表表格 -->
    <vxe-table
      ref="tableRef"
      border
      resizable
      show-overflow
      keep-source
      :data="localConfig.fields"
      :tree-config="{ transform: true, rowField: 'id', parentField: 'parentId' }"
      :edit-config="{ trigger: 'click', mode: 'cell', showStatus: true }"
      :checkbox-config="{ checkField: 'checked' }"
      :span-method="fieldSpanMethod"
      :row-class-name="getRowClassName"
      :cell-class-name="getCellClassName"
      max-height="500"
      class="fields-table text-sm"
      @edit-closed="handleEditClosed"
    >
      <vxe-column type="checkbox" fixed="left" width="50" />
      <vxe-column type="seq" title="序号" tree-node width="80" />

      <vxe-column field="fieldName" title="信息名称" :edit-render="{ name: 'input' }" />

      <vxe-column
        field="byteCount"
        title="字节数"
        width="100"
        :edit-render="{ name: 'input', props: { type: 'number' } }"
      />

      <vxe-column field="byteSequence" title="字节序号" width="120" />

      <vxe-column field="valueRange" title="值域及含义" :edit-render="{ name: 'textarea' }" />

      <vxe-column field="unit" title="量纲" width="100" :edit-render="{ name: 'input' }" />

      <vxe-column
        field="dataType"
        title="数据类型"
        width="140"
        :edit-render="{
          name: 'DictAutocomplete',
          props: {
            dictType: 'sys_protocol_data_type',
            placeholder: '请输入或选择',
            uppercaseLabel: true,
          },
        }"
      />

      <vxe-column field="scale" title="比例尺" width="100" :edit-render="{ name: 'input' }" />

      <vxe-column field="remark" title="备注" :edit-render="{ name: 'input' }" />

      <vxe-column title="操作" width="80" fixed="right">
        <template #default="slotProps">
          <zx-button
            v-if="slotProps?.row"
            link
            type="danger"
            icon="Delete"
            size="small"
            @click="removeRow(slotProps.row)"
          >
            删除
          </zx-button>
        </template>
      </vxe-column>
    </vxe-table>

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

    <!-- 校验诊断面板 - 使用通用组件 -->
    <VxeValidationPanel
      :issues="validationIssues"
      :auto-expand="true"
      @issue-click="handleIssueClick"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { VxeTableInstance } from 'vxe-table';
import { useDict } from '@/utils/dict';
// 使用通用校验框架
import {
  useVxeTableValidation,
  VxeValidationPanel,
  required,
  positiveInteger,
  scale as scaleValidator,
  warning,
  lengthRange,
  createBandwidthValidator,
  createFrameLengthValidator,
  createValueRangeValidator,
  parseNumber,
} from '@/components/VxeTableValidation';

const props = defineProps<{
  modelValue?: any;
  protocolType?: string;
  deviceMode?: boolean;
  senderEditable?: boolean;
  receiverEditable?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: any];
}>();

// 获取字典数据
const {
  sys_protocol_method_ethernet,
  sys_protocol_frequency,
  sys_protocol_speed_ethernet,
  sys_protocol_error_handling,
} = useDict(
  'sys_protocol_method_ethernet',
  'sys_protocol_frequency',
  'sys_protocol_speed_ethernet',
  'sys_protocol_error_handling'
);

const tableRef = ref<VxeTableInstance>();

// ==================== 使用通用校验框架 ====================
// 数据类型对应的值范围（用于溢出检测）
const DATA_TYPE_VALUE_RANGES: Record<string, { min: number; max: number }> = {
  UINT8: { min: 0, max: 255 },
  INT8: { min: -128, max: 127 },
  UINT16: { min: 0, max: 65535 },
  INT16: { min: -32768, max: 32767 },
  UINT32: { min: 0, max: 4294967295 },
  INT32: { min: -2147483648, max: 2147483647 },
  FLOAT: { min: -3.4e38, max: 3.4e38 },
  DOUBLE: { min: -1.8e308, max: 1.8e308 },
  BOOL: { min: 0, max: 1 },
};

// 计算帧总长度的辅助函数
const calculateFrameLength = (fields: any[]): number => {
  if (!Array.isArray(fields)) return 0;
  return fields.reduce((sum, field) => {
    const bytes = parseNumber(field.byteCount);
    return sum + (bytes || 0);
  }, 0);
};

// 解析速率为 bps
const parseDataRate = (rate: string): number => {
  if (!rate) return 0;
  const match = rate.replace(/\s/g, '').toLowerCase().match(/^(\d+(?:\.\d+)?)(g|m|k)?bps$/i);
  if (!match) return 0;
  const value = parseFloat(match[1]);
  const unit = (match[2] || '').toLowerCase();
  const multipliers: Record<string, number> = { g: 1e9, m: 1e6, k: 1e3, '': 1 };
  return value * (multipliers[unit] || 1);
};

// 初始化自定义校验框架（通过面板 + 高亮显示校验结果）
const {
  issues: validationIssues,
  errorCount,
  hasErrors,
  validate,
  validateOrThrow,
  isValid,
  getRowClassName,
  getCellClassName,
  setContext,
} = useVxeTableValidation({
  // 字段校验规则 - 类似 Element Plus 的配置方式
  rules: {
    fieldName: [
      required('信息名称不能为空'),
    ],
    byteCount: [
      // 条件校验：只在没有数据类型时要求手动填写
      {
        when: (row) => !row.dataType,
        validator: (value) => {
          if (!value) return true; // 非必填
          const num = parseNumber(value);
          return num !== null && num > 0;
        },
        message: '字节数必须为正整数',
        level: 'warning',
      },
      {
        type: 'integer',
        max: 65535,
        message: '字节数不能超过 65535',
      },
    ],
    scale: [
      scaleValidator('比例尺不能为0'),
    ],
    remark: [
      warning(lengthRange(0, 500, '备注建议不超过500字')),
    ],
  },
  // 字段显示名称映射
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
  // 全局校验器
  globalValidators: [
    // 数值范围溢出校验
    createValueRangeValidator({
      dataTypeField: 'dataType',
      valueRangeField: 'valueRange',
      typeRanges: DATA_TYPE_VALUE_RANGES,
    }),
    // 带宽校验
    createBandwidthValidator({
      getFrameLength: calculateFrameLength,
      getFrequency: (ctx) => parseNumber(ctx?.frequency) || 1,
      getBandwidthLimit: (ctx) => parseDataRate(ctx?.speed) || 1e9,
    }),
    // 帧长度校验
    createFrameLengthValidator({
      getActualLength: calculateFrameLength,
      getConfiguredLimit: (ctx) => parseNumber(ctx?.frameLength) || undefined,
      busLimits: { Ethernet: 1500 },
      getBusType: () => 'Ethernet',
    }),
  ],
});

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

const defaultConfig = {
  sender: '',
  receiver: '',
  frequency: '',
  frequencyLabel: '',
  speed: '',
  speedLabel: '',
  method: '',
  methodLabel: '',
  port: '',
  frameLength: '',
  errorHandle: '',
  errorHandleLabel: '',
  notes: '',
  fields: [],
};

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

const configTableData = ref([
  {
    protocolName: '以太网',
    label1: '发送方',
    value1: localConfig.sender,
    label2: '',
    value2: '',
  },
  {
    protocolName: '以太网',
    label1: '接收方',
    value1: localConfig.receiver,
    label2: '',
    value2: '',
  },
  {
    protocolName: '以太网',
    label1: '传输频率',
    value1: localConfig.frequency,
    label2: '传输速率/bps',
    value2: localConfig.speed,
  },
  {
    protocolName: '以太网',
    label1: '传输方式',
    value1: localConfig.method,
    label2: '端口号',
    value2: localConfig.port,
  },
  {
    protocolName: '以太网',
    label1: '帧长度/Byte',
    value1: localConfig.frameLength,
    label2: '错误处理',
    value2: localConfig.errorHandle,
  },
]);

// 辅助函数：根据字典获取 label
const getLabel = (dict: any[], value: string, fallbackLabel: string = '') => {
  if (!value) return '';
  // 如果已有 label 且不为空，优先使用（但这里为了修复显示问题，我们优先查字典）
  // 实际上，如果 dictValue 是英文，我们想显示中文 label
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
    sys_protocol_speed_ethernet.value,
    localConfig.speed,
    localConfig.speedLabel
  );

  // 传输方式
  rows[3].value1 = getLabel(
    sys_protocol_method_ethernet.value,
    localConfig.method,
    localConfig.methodLabel
  );

  rows[3].value2 = localConfig.port;
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
    sys_protocol_method_ethernet,
    sys_protocol_frequency,
    sys_protocol_speed_ethernet,
    sys_protocol_error_handling,
  ],
  () => {
    syncConfigTableRows();
  }
);

const configEditRender = (field: string) => {
  const getDictType = (row: Record<string, string>) => {
    if (field === 'value1' && row.label1 === '传输方式') return 'sys_protocol_method_ethernet';
    if (field === 'value1' && row.label1 === '传输频率') return 'sys_protocol_frequency';
    if (field === 'value2' && row.label2 === '传输速率/bps') return 'sys_protocol_speed_ethernet';
    if (field === 'value2' && row.label2 === '错误处理') return 'sys_protocol_error_handling';
    return '';
  };

  const isNumberField = (row: Record<string, string>) => {
    if (field === 'value2' && row.label2 === '端口号') return true;
    if (field === 'value1' && row.label1 === '帧长度/Byte') return true;
    return false;
  };

  const isDeviceLockField = (row: Record<string, string>) => {
    const senderLocked = props.deviceMode || props.senderEditable === false;
    const receiverLocked = props.deviceMode || props.receiverEditable === false;
    if (field !== 'value1') return false;
    if (row.label1 === '发送方') return senderLocked;
    if (row.label1 === '接收方') return receiverLocked;
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
      } else if (row.label2 === '端口号') {
        localConfig.port = nextValue;
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

watch(
  () => localConfig,
  (newVal) => {
    ensureByteCountSync();
    recalcByteSequence();
    syncConfigTableRows();
    emit('update:modelValue', newVal);
  },
  { deep: true, immediate: true }
);

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

const removeRow = (row: any) => {
  const index = localConfig.fields.findIndex((item: any) => item.id === row.id);
  if (index > -1) {
    localConfig.fields = localConfig.fields.filter(
      (item: any) => item.id !== row.id && item.parentId !== row.id
    );
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
      const deleteIds = selectRecords.map((item: any) => item.id);
      localConfig.fields = localConfig.fields.filter(
        (item: any) => !deleteIds.includes(item.id) && !deleteIds.includes(item.parentId)
      );
      ElMessage.success('删除成功');
      // 删除后重新校验
      runValidation();
    })
    .catch(() => {});
};

// 运行校验 - 使用通用框架
const runValidation = async () => {
  // 更新校验上下文
  setContext({
    busType: 'Ethernet',
    speed: localConfig.speed,
    frameLength: localConfig.frameLength,
    frequency: localConfig.frequency,
  });

  // 执行校验
  const result = await validate(localConfig.fields);

  if (result.valid && result.warningCount === 0) {
    ElMessage.success('校验通过，配置正确');
  } else {
    const parts = [];
    if (result.errorCount > 0) parts.push(`${result.errorCount} 个错误`);
    if (result.warningCount > 0) parts.push(`${result.warningCount} 个警告`);
    ElMessage.warning(`发现 ${parts.join('，')}，请检查配置`);
  }
};

// 编辑完成后自动校验
const handleEditClosed = () => {
  // 延迟执行，确保数据已更新
  setTimeout(() => {
    runValidation();
  }, 100);
};

// 点击问题项跳转到对应单元格
const handleIssueClick = (issue: any) => {
  if (issue.rowIndex < 0) return;

  const $table = tableRef.value;
  if (!$table) return;

  const row = localConfig.fields[issue.rowIndex];
  if (!row) return;

  // 滚动到对应行
  $table.scrollToRow(row);

  // 高亮该行
  $table.setCurrentRow(row);

  // 如果有字段信息，尝试激活编辑
  if (issue.field) {
    $table.setEditCell(row, issue.field);
  }
};

/**
 * 校验数据并返回结果（供父组件在保存前调用）
 * @returns Promise<boolean> - true 表示校验通过，可以保存
 */
const validateBeforeSave = async (): Promise<boolean> => {
  // 更新上下文
  setContext({
    busType: 'Ethernet',
    speed: localConfig.speed,
    frameLength: localConfig.frameLength,
    frequency: localConfig.frequency,
  });

  // 执行校验
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
  runValidation,
  validationIssues,
  // 供父组件阻断保存使用
  validateBeforeSave,  // 推荐：返回 boolean
  validate,            // 返回完整结果
  validateOrThrow,     // 失败时抛出错误
  isValid,             // 简化版
  hasErrors,           // 是否有错误
});
</script>

<style lang="less" scoped>
// 注意：validation.less 已在 main.ts 中全局引入，不要在 scoped 中重复导入
// 否则会因为 scoped hash 导致 tooltip 样式失效

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

.toolbar-right {
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
