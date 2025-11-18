<template>
  <div class="message-config-tab">
    <!-- 工具栏 -->
    <div class="table-toolbar flex">
      <slot name="toolbar">
        <div class="toolbar-left flex items-center gap-2">
          <zx-button type="primary" icon="Upload" size="medium" @click="handleImport"
            >导入数据</zx-button
          >
          <zx-button type="primary" icon="Plus" size="medium" @click="handleAddField"
            >添加字段</zx-button
          >
          <zx-button type="danger" icon="Delete" size="medium" @click="handleDeleteSelected"
            >删除选中</zx-button
          >
        </div>
        <div class="toolbar-right flex items-center">
          <ProtocolTemplateSelector
            style="width: 200px"
            v-model="selectedProtocolId"
            :protocolType="portInfo?.interfaceType?.toLowerCase()"
            placeholder="选择协议"
            clearable
            size="medium"
            @entity="handleProtocolChange"
          />
        </div>
      </slot>
    </div>

    <!-- VXE Table - 包含基本信息和字段列表 -->
    <div class="message-table-wrapper">
      <vxe-table
        border
        show-overflow
        :data="configTableData"
        :span-method="configSpanMethod"
        :edit-config="configTableEditConfig"
      >
        <vxe-column field="label1" title="" align="center" />
        <vxe-column
          field="value1"
          title=""
          min-width="160"
          :edit-render="getEditRender('value1')"
        />
        <vxe-column field="label2" title="" align="center" />
        <vxe-column
          field="value2"
          title=""
          min-width="160"
          :edit-render="getEditRender('value2')"
        />
        <vxe-column field="label3" title="" align="center" />
        <vxe-column
          field="value3"
          title=""
          min-width="160"
          :edit-render="getEditRender('value3')"
        />
        <vxe-column field="label4" title="" align="center" />
        <vxe-column
          field="value4"
          title=""
          min-width="160"
          :edit-render="getEditRender('value4')"
        />
      </vxe-table>

      <!-- 字段列表表格 -->
      <vxe-table
        ref="tableRef"
        border
        resizable
        show-overflow
        keep-source
        :data="displayFields"
        :tree-config="{ transform: true, rowField: 'id', parentField: 'parentId' }"
        :edit-config="{ trigger: 'click', mode: 'cell' }"
        :checkbox-config="{ checkField: 'checked' }"
        :span-method="fieldSpanMethod"
        class="fields-table"
      >
        <vxe-column type="checkbox" fixed="left" />
        <vxe-column type="seq" title="序号" tree-node />

        <vxe-column field="fieldName" title="信息名称" :edit-render="{ name: 'input' }" />

        <vxe-column
          field="byteCount"
          title="字节数"
          :edit-render="{ name: 'input', props: { type: 'number' } }"
        />

        <vxe-column
          field="byteSequence"
          title="字节序号"
          :edit-render="{ name: 'input', props: { placeholder: '0~3' } }"
        />

        <vxe-column field="valueRange" title="值域及含义" :edit-render="{ name: 'textarea' }" />

        <vxe-column field="unit" title="量纲" :edit-render="{ name: 'input' }" />

        <vxe-column
          field="dataType"
          title="数据类型"
          :edit-render="{
            name: 'select',
            options: [
              { value: 'UINT8', label: 'UINT8' },
              { value: 'UINT16', label: 'UINT16' },
              { value: 'UINT32', label: 'UINT32' },
              { value: 'INT8', label: 'INT8' },
              { value: 'INT16', label: 'INT16' },
              { value: 'INT32', label: 'INT32' },
              { value: 'FLOAT', label: 'FLOAT' },
              { value: 'DOUBLE', label: 'DOUBLE' },
              { value: 'STRING', label: 'STRING' },
            ],
          }"
        >
          <template #default="slotProps">
            <el-tag
              v-if="slotProps?.row?.dataType"
              :type="getDataTypeTagType(slotProps.row.dataType)"
              size="small"
            >
              {{ slotProps.row.dataType }}
            </el-tag>
          </template>
        </vxe-column>

        <vxe-column field="scale" title="比例尺" :edit-render="{ name: 'input' }" />

        <vxe-column field="remark" title="备注" :edit-render="{ name: 'input' }" />

        <vxe-column title="操作" fixed="right">
          <template #default="slotProps">
            <el-button
              v-if="slotProps?.row"
              link
              type="danger"
              size="small"
              @click="handleDelete(slotProps.row)"
            >
              删除
            </el-button>
          </template>
        </vxe-column>
      </vxe-table>
    </div>

    <!-- 导入文件对话框 -->
    <ImportFileDialog ref="importDialogRef" @confirm="handleImportConfirm" />
  </div>
</template>

<script setup name="MessageConfigTab">
import { ref, reactive, onMounted, watch, computed } from 'vue';
import ProtocolTemplateSelector from '../Protocol/selector/ProtocolTemplateSelector.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ImportFileDialog } from './index';
import { resolveEditorValue } from '../Protocol/templates/fieldUtils';

const props = defineProps({
  portInfo: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['update:modelValue']);

// 表格引用
const tableRef = ref();

// 导入对话框引用
const importDialogRef = ref();

// 默认报文头信息
const getDefaultHeader = () => ({
  sender: '',
  receiver: '',
  frequency: '',
  baudRate: '',
  method: '',
  duration: null,
  frameLength: null,
  errorHandling: '',
});

// 默认报文字段数据
const getDefaultFields = () => [];

// 报文头信息
const messageHeader = reactive(getDefaultHeader());

// 报文字段数据
const messageFields = ref(getDefaultFields());

const displayFields = computed(() => messageFields.value);
const selectedProtocolId = ref();

// 头部配置表格数据
const configTableData = ref([
  {
    label1: '发送方',
    value1: '',
    label2: '接收方',
    value2: '',
    label3: '传输频率',
    value3: '',
    label4: '传输速率',
    value4: '',
  },
  {
    label1: '传输方式',
    value1: '',
    label2: '发送时长',
    value2: '',
    label3: '帧长度',
    value3: '',
    label4: '错误处理',
    value4: '',
  },
]);

function syncConfigRows() {
  const rows = configTableData.value;
  rows[0].value1 = messageHeader.sender;
  rows[0].value2 = messageHeader.receiver;
  rows[0].value3 = messageHeader.frequency;
  rows[0].value4 = messageHeader.baudRate;
  rows[1].value1 = messageHeader.method;
  rows[1].value2 = messageHeader.duration;
  rows[1].value3 = messageHeader.frameLength;
  rows[1].value4 = messageHeader.errorHandling;
}

const configTableEditConfig = {
  trigger: 'click',
  mode: 'cell',
  activeMethod({ column, row }) {
    if (column.field === 'value1' && row.label1 === '发送方') return false;
    if (column.field === 'value2' && row.label2 === '接收方') return false;
    return true;
  },
};

function configSpanMethod() {
  return { rowspan: 1, colspan: 1 };
}

function getEditRender(field) {
  const handleUpdate = (cellParams, evtOrValue) => {
    const { row } = cellParams;
    const raw = evtOrValue && evtOrValue.target ? evtOrValue.target.value : evtOrValue;
    const nextValue = resolveEditorValue(cellParams, raw);
    if (field === 'value1') {
      if (row.label1 === '发送方') {
        messageHeader.sender = nextValue;
      } else if (row.label1 === '传输方式') {
        messageHeader.method = nextValue;
      }
    } else if (field === 'value2') {
      if (row.label2 === '接收方') {
        return;
      } else if (row.label2 === '发送时长') {
        messageHeader.duration = nextValue;
      }
    } else if (field === 'value3') {
      if (row.label3 === '传输频率') {
        messageHeader.frequency = nextValue;
      } else if (row.label3 === '帧长度') {
        messageHeader.frameLength = nextValue;
      }
    } else if (field === 'value4') {
      if (row.label4 === '传输速率') {
        messageHeader.baudRate = nextValue;
      } else if (row.label4 === '错误处理') {
        messageHeader.errorHandling = nextValue;
      }
    }
    syncConfigRows();
  };

  return {
    name: 'input',
    attrs: ({ row }) => {
      if (field === 'value1' && row.label1 === '发送方') return { disabled: true };
      if (field === 'value2' && row.label2 === '接收方') return { disabled: true };
      if (
        (field === 'value4' && row.label4 === '传输速率') ||
        (field === 'value2' && row.label2 === '发送时长') ||
        (field === 'value3' && row.label3 === '帧长度')
      ) {
        return { type: 'number' };
      }
      return { placeholder: '请输入' };
    },
    events: {
      change: (cellParams, evt) => handleUpdate(cellParams, evt),
      input: (cellParams, evt) => handleUpdate(cellParams, evt),
    },
  };
}

// 数据类型标签颜色
function getDataTypeTagType(dataType) {
  const typeMap = {
    UINT8: 'success',
    UINT16: 'success',
    UINT32: 'success',
    INT8: 'warning',
    INT16: 'warning',
    INT32: 'warning',
    FLOAT: 'info',
    DOUBLE: 'info',
    STRING: '',
  };
  return typeMap[dataType] || '';
}

// 字段表格合并单元格方法（合并值域及含义和量纲列）
function fieldSpanMethod({ columnIndex }) {
  // 值域及含义列的索引 (第4列，索引为3，考虑checkbox和seq)
  const valueFieldColIndex = 5; // 值域及含义列
  const unitColIndex = 6; // 量纲列

  if (columnIndex === valueFieldColIndex) {
    // 值域及含义列，合并量纲列
    return { rowspan: 1, colspan: 2 };
  } else if (columnIndex === unitColIndex) {
    // 量纲列被合并，不显示
    return { rowspan: 0, colspan: 0 };
  }

  return { rowspan: 1, colspan: 1 };
}

const DATA_TYPE_CANONICAL = [
  'UINT8',
  'UINT16',
  'UINT32',
  'INT8',
  'INT16',
  'INT32',
  'FLOAT',
  'DOUBLE',
  'STRING',
];
const DATA_TYPE_ALIASES = {
  uint8: 'UINT8',
  u8: 'UINT8',
  byte: 'UINT8',
  无符号8位: 'UINT8',
  无符号字节: 'UINT8',
  uint16: 'UINT16',
  u16: 'UINT16',
  无符号16位: 'UINT16',
  uint32: 'UINT32',
  u32: 'UINT32',
  无符号32位: 'UINT32',
  int8: 'INT8',
  i8: 'INT8',
  有符号8位: 'INT8',
  int16: 'INT16',
  i16: 'INT16',
  有符号16位: 'INT16',
  int32: 'INT32',
  i32: 'INT32',
  有符号32位: 'INT32',
  float: 'FLOAT',
  单精度: 'FLOAT',
  f32: 'FLOAT',
  double: 'DOUBLE',
  双精度: 'DOUBLE',
  dbl: 'DOUBLE',
  f64: 'DOUBLE',
  string: 'STRING',
  文本: 'STRING',
  字符串: 'STRING',
  str: 'STRING',
  text: 'STRING',
};
function normalizeDataType(val) {
  if (!val) return 'STRING';
  const raw = String(val).trim();
  const upper = raw.toUpperCase();
  if (DATA_TYPE_CANONICAL.includes(upper)) return upper;
  const lower = raw.toLowerCase();
  return DATA_TYPE_ALIASES[lower] || DATA_TYPE_ALIASES[raw] || 'STRING';
}
function toNumberOr(defaultValue, v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : defaultValue;
}
const FIELD_KEYS = {
  fieldName: ['信息名称', 'name', 'fieldName'],
  byteCount: ['字节数', 'byteCount'],
  byteSequence: ['字节序号', 'byteSequence'],
  valueRange: ['值域及含义', 'valueRange', 'meaning'],
  unit: ['量纲', 'unit'],
  dataType: ['数据类型', 'dataType', 'type'],
  scale: ['比例尺', 'scale'],
  remark: ['备注', 'remark', 'note'],
};
function pickVal(obj, keys) {
  for (const k of keys) {
    const v = obj[k];
    if (v !== undefined && v !== null && String(v).length > 0) return v;
  }
  return undefined;
}
function normalizeField(f) {
  return {
    id: Date.now().toString() + Math.random(),
    parentId: null,
    fieldName: pickVal(f, FIELD_KEYS.fieldName) ?? '',
    byteCount: toNumberOr(1, pickVal(f, FIELD_KEYS.byteCount)),
    byteSequence: pickVal(f, FIELD_KEYS.byteSequence) ?? '',
    valueRange: pickVal(f, FIELD_KEYS.valueRange) ?? '',
    unit: pickVal(f, FIELD_KEYS.unit) ?? '',
    dataType: normalizeDataType(pickVal(f, FIELD_KEYS.dataType)),
    scale: String(pickVal(f, FIELD_KEYS.scale) ?? ''),
    remark: String(pickVal(f, FIELD_KEYS.remark) ?? ''),
  };
}

// 打开导入对话框
function handleImport() {
  importDialogRef.value?.open?.();
}

// 处理导入确认
function handleImportConfirm(data) {
  if (data.fields && data.fields.length > 0) {
    // 替换当前字段数据
    messageFields.value = data.fields.map(field => ({
      ...field,
      id: field.id || Date.now().toString() + Math.random(),
      parentId: field.parentId || null,
    }));
  }

  // 如果有表头信息，也更新表头
  if (data.header) {
    Object.assign(messageHeader, data.header);
  }
  syncConfigRows();
}

function handleProtocolChange(entity) {
  if (!entity) return;
  selectedProtocolId.value = entity.protocolId ?? selectedProtocolId.value;
  const cfg = entity.protocolConfig || {};
  messageHeader.sender = cfg.sender || '';
  messageHeader.receiver = cfg.receiver || '';
  messageHeader.frequency = cfg.frequency || '';
  messageHeader.baudRate = cfg.speed || '';
  messageHeader.method = cfg.method || '';
  messageHeader.duration = cfg.sendDuration || '';
  messageHeader.frameLength = cfg.frameLength || '';
  messageHeader.errorHandling = cfg.errorHandle || '';
  const list = Array.isArray(cfg.fields) ? cfg.fields : [];
  messageFields.value = list.map(f => normalizeField(f));
  syncConfigRows();
}

// 添加字段
function handleAddField() {
  const newId = Date.now().toString();
  messageFields.value.push({
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
}

// 添加子项
function handleAddChild(row) {
  const newId = `${row.id}-${Date.now()}`;
  messageFields.value.push({
    id: newId,
    parentId: row.id,
    fieldName: '子字段',
    byteCount: 1,
    byteSequence: '',
    valueRange: '',
    unit: '',
    dataType: 'UINT8',
    scale: '1',
    remark: '',
  });
  ElMessage.success('子字段已添加');
}

// 删除字段
function handleDelete(row) {
  const index = messageFields.value.findIndex(item => item.id === row.id);
  if (index > -1) {
    messageFields.value = messageFields.value.filter(
      item => item.id !== row.id && item.parentId !== row.id
    );
    ElMessage.success('删除成功');
  }
}

// 删除选中
function handleDeleteSelected() {
  const selectRecords = tableRef.value.getCheckboxRecords();
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
      const deleteIds = selectRecords.map(item => item.id);
      messageFields.value = messageFields.value.filter(
        item => !deleteIds.includes(item.id) && !deleteIds.includes(item.parentId)
      );
      ElMessage.success('删除成功');
    })
    .catch(() => {});
}

// 获取表单数据
function getFormData() {
  return {
    header: { ...messageHeader },
    fields: messageFields.value,
    protocolId: selectedProtocolId.value,
  };
}

// 验证表单
async function validate() {
  // 简单验证
  if (!messageHeader.sender) {
    ElMessage.error('请输入发送方');
    return false;
  }
  // if (!messageHeader.receiver) {
  //   ElMessage.error('请输入接收方')
  //   return false
  // }
  return true;
}

// 清除验证
function clearValidate() {
  // VXE Table 不需要清除验证
}

// 初始化数据
function initializeData() {
  if (props.portInfo.messageConfig) {
    // 加载已有配置（深拷贝避免引用问题）
    Object.assign(messageHeader, JSON.parse(JSON.stringify(props.portInfo.messageConfig.header)));
    messageFields.value = JSON.parse(JSON.stringify(props.portInfo.messageConfig.fields || []));
  } else {
    // 重置为默认值
    Object.assign(messageHeader, getDefaultHeader());
    messageFields.value = getDefaultFields();
  }

  // 自动填充发送方为设备名称
  if (props.portInfo.deviceName) {
    messageHeader.sender = props.portInfo.deviceName;
  }

  syncConfigRows();
}

// 监听 portInfo 变化，每次打开不同端口时重新加载数据
watch(
  () => props.portInfo,
  () => {
    initializeData();
  },
  { deep: true, immediate: true }
);

watch(
  () => messageHeader,
  () => {
    syncConfigRows();
  },
  { deep: true }
);

onMounted(() => {});

// 暴露方法
defineExpose({
  getFormData,
  validate,
  clearValidate,
  handleAddField,
  handleDeleteSelected,
  handleProtocolChange,
});
</script>

<style lang="less" scoped>
.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.message-table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

// 报文基本信息表格样式
.message-header-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: -1px; // 与下方表格边框重叠
  background: white;
  font-size: 14px;

  td {
    border: 1px solid #e8eaec;
    padding: 8px 12px;
    line-height: 1.5;
  }

  .header-label {
    background-color: #f8f8f9;
    font-weight: 500;
    color: #515a6e;
    width: 120px;
    text-align: right;
    white-space: nowrap;
  }

  .header-value {
    background-color: white;

    :deep(.el-input),
    :deep(.el-select),
    :deep(.el-input-number) {
      width: 100%;
    }

    :deep(.el-input__wrapper),
    :deep(.el-input-number__wrapper) {
      box-shadow: none;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
    }

    :deep(.el-input__inner) {
      height: 28px;
      line-height: 28px;
    }
  }
}

// 字段列表表格样式
.fields-table {
  flex: 1;

  :deep(.vxe-table) {
    border-top: none; // 与上方表格连接
  }

  :deep(.vxe-body--row.row--hover) {
    background-color: #f5f7fa;
  }

  :deep(.vxe-cell) {
    padding: 4px 8px;
  }

  :deep(.vxe-input),
  :deep(.vxe-select),
  :deep(.vxe-textarea) {
    width: 100%;
  }

  :deep(.vxe-tree--indent) {
    width: 16px;
  }
}
</style>
.toolbar-left { column-gap: 8px; display: flex; align-items: center; } .toolbar-right { column-gap:
8px; display: flex; align-items: center; }
