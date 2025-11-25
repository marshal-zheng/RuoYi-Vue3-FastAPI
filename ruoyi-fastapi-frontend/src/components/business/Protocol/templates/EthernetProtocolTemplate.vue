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
    {{ configTableData }}
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
      :edit-config="{ trigger: 'click', mode: 'cell' }"
      :checkbox-config="{ checkField: 'checked' }"
      :span-method="fieldSpanMethod"
      max-height="500"
      class="fields-table text-sm"
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

      <vxe-column
        field="byteSequence"
        title="字节序号"
        width="120"
        :edit-render="{ name: 'input', props: { placeholder: '0~3' } }"
      />

      <vxe-column field="valueRange" title="值域及含义" :edit-render="{ name: 'textarea' }" />

      <vxe-column field="unit" title="量纲" width="100" :edit-render="{ name: 'input' }" />

      <vxe-column
        field="dataType"
        title="数据类型"
        width="140"
        :edit-render="{
          name: 'DictAutocomplete',
          props: { dictType: 'sys_protocol_data_type', placeholder: '请输入或选择' },
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, toRefs } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { VxeTableInstance } from 'vxe-table';
import { useDict } from '@/utils/dict';

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
  fields: [],
};

const localConfig = reactive({
  ...defaultConfig,
  ...(props.modelValue || {}),
});

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
    syncConfigTableRows();
    emit('update:modelValue', newVal);
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
    fieldName: '',
    byteCount: 1,
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
    })
    .catch(() => {});
};

defineExpose({
  insertRow,
  removeSelectRow,
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
