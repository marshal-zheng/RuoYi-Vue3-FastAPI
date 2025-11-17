<template>
  <div class="w-full">
    <!-- 协议配置表格（所见即所得） -->
    <div class="mb-4">
      <vxe-table
        border
        show-overflow
        :data="configTableData"
        :span-method="configSpanMethod"
        :edit-config="configTableEditConfig"
        class="text-sm"
      >
        <vxe-column
          field="label1"
          title=""
          width="100"
          align="right"
          class-name="!bg-gray-50 !font-medium"
        />
        <vxe-column
          field="value1"
          title=""
          min-width="150"
          :edit-render="configEditRender('value1')"
        />
        <vxe-column
          field="label2"
          title=""
          width="100"
          align="right"
          class-name="!bg-gray-50 !font-medium"
        />
        <vxe-column
          field="value2"
          title=""
          min-width="150"
          :edit-render="configEditRender('value2')"
        />
        <vxe-column
          field="label3"
          title=""
          width="100"
          align="right"
          class-name="!bg-gray-50 !font-medium"
        />
        <vxe-column
          field="value3"
          title=""
          min-width="150"
          :edit-render="configEditRender('value3')"
        />
        <vxe-column
          field="label4"
          title=""
          width="100"
          align="right"
          class-name="!bg-gray-50 !font-medium"
        />
        <vxe-column
          field="value4"
          title=""
          min-width="150"
          :edit-render="configEditRender('value4')"
        />
      </vxe-table>
    </div>

    <!-- 协议字段配置表格 -->
    <div>
      <vxe-toolbar>
        <template #buttons>
          <ZxButton icon="Plus" type="primary" @click="insertRow">新增行</ZxButton>
          <ZxButton
            icon="Delete"
            type="danger"
            plain
            style="margin-left: 10px"
            @click="removeSelectRow"
            >删除</ZxButton
          >
        </template>
      </vxe-toolbar>

      <vxe-table
        ref="tableRef"
        border
        show-overflow
        :data="localConfig.fields"
        :span-method="fieldSpanMethod"
        :edit-config="{ trigger: 'click', mode: 'cell' }"
        :checkbox-config="{ checkField: 'checked' }"
        max-height="500"
        class="text-sm"
      >
        <vxe-column type="checkbox" width="50" align="center" fixed="left" />
        <vxe-column
          field="序号"
          title="序号"
          width="80"
          align="center"
          :edit-render="{ name: 'input' }"
        />
        <vxe-column
          field="信息名称"
          title="信息名称"
          width="150"
          :edit-render="{ name: 'input' }"
        />
        <vxe-column field="字节数" title="字节数" align="center" :edit-render="{ name: 'input' }" />
        <vxe-column
          field="字节序号"
          title="字节序号"
          align="center"
          :edit-render="{ name: 'input' }"
        />
        <vxe-column field="值域及含义" title="值域及含义" :edit-render="{ name: 'input' }" />
        <vxe-column field="量纲" title="量纲" :edit-render="{ name: 'input' }" />
        <vxe-column field="数据类型" title="数据类型" :edit-render="{ name: 'input' }" />
        <vxe-column field="比例尺" title="比例尺" align="center" :edit-render="{ name: 'input' }" />
        <vxe-column field="备注" title="备注" width="150" :edit-render="{ name: 'input' }" />
        <vxe-column title="操作" width="100" align="center" fixed="right">
          <template #default="{ rowIndex }">
            <ZxButton type="danger" icon="Delete" plain @click="removeRow(rowIndex)">删除</ZxButton>
          </template>
        </vxe-column>
      </vxe-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, reactive, computed } from 'vue';
import type { VxeTableInstance } from 'vxe-table';
import { resolveEditorValue } from './fieldUtils';

const props = defineProps<{
  modelValue?: any;
  protocolType?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: any];
}>();

// 表格引用
const tableRef = ref<VxeTableInstance>();

// 默认配置
const defaultConfig = {
  sender: '',
  receiver: '',
  frequency: '',
  speed: '',
  method: '',
  sendDuration: '',
  frameLength: '',
  errorHandle: '',
  fields: [],
};

// 本地配置
const localConfig = reactive({
  ...defaultConfig,
  ...(props.modelValue || {}),
});

// 配置表格数据（将配置项展示为表格形式）
const configTableData = ref([
  {
    label1: '发送方',
    value1: localConfig.sender,
    label2: '接收方',
    value2: localConfig.receiver,
    label3: '传输频率',
    value3: `${localConfig.frequency} ms`,
    label4: '传输速率',
    value4: `${localConfig.speed} bps`,
  },
  {
    label1: '传输方式',
    value1: localConfig.method,
    label2: '发送时长',
    value2: localConfig.sendDuration ? `${localConfig.sendDuration} ms` : '',
    label3: '帧长度',
    value3: `${localConfig.frameLength} Byte`,
    label4: '错误处理',
    value4: localConfig.errorHandle,
  },
]);

const syncConfigTableRows = () => {
  const rows = configTableData.value;
  rows[0].value1 = localConfig.sender;
  rows[0].value2 = localConfig.receiver;
  rows[0].value3 = `${localConfig.frequency} ms`;
  rows[0].value4 = `${localConfig.speed} bps`;
  rows[1].value1 = localConfig.method;
  rows[1].value2 = localConfig.sendDuration ? `${localConfig.sendDuration} ms` : '';
  rows[1].value3 = `${localConfig.frameLength} Byte`;
  rows[1].value4 = localConfig.errorHandle;
};

// 配置表格编辑渲染器（发送方和接收方不允许编辑）
const configEditRender = (field: string) => {
  const stripUnit = (v: any, unit: string) =>
    String(v ?? '')
      .replace(new RegExp(`\\s*${unit}$`, 'i'), '')
      .trim();
  const handleUpdate = (cellParams: any, evtOrValue: any) => {
    const { row } = cellParams;
    const raw = evtOrValue && evtOrValue.target ? evtOrValue.target.value : evtOrValue;
    const nextValue = resolveEditorValue(cellParams, raw);
    if (field === 'value1') {
      if (row.label1 === '传输方式') {
        localConfig.method = nextValue;
      }
    } else if (field === 'value2') {
      if (row.label2 === '发送时长') {
        localConfig.sendDuration = stripUnit(nextValue, 'ms');
      }
    } else if (field === 'value3') {
      if (row.label3 === '传输频率') {
        localConfig.frequency = stripUnit(nextValue, 'ms');
      } else if (row.label3 === '帧长度') {
        localConfig.frameLength = stripUnit(nextValue, 'Byte');
      }
    } else if (field === 'value4') {
      if (row.label4 === '传输速率') {
        localConfig.speed = stripUnit(nextValue, 'bps');
      } else if (row.label4 === '错误处理') {
        localConfig.errorHandle = nextValue;
      }
    }
  };

  return {
    name: 'input',
    attrs: { placeholder: '请输入' },
    events: {
      change: (cellParams: any, evt: any) => handleUpdate(cellParams, evt),
      input: (cellParams: any, evt: any) => handleUpdate(cellParams, evt),
    },
  };
};

const configTableEditConfig = {
  trigger: 'click',
  mode: 'cell',
  activeMethod({ row, column }: any) {
    if (column.field === 'value1' && row.label1 === '发送方') return false;
    if (column.field === 'value2' && row.label2 === '接收方') return false;
    return true;
  },
};

// 配置表格合并单元格方法
const configSpanMethod = () => {
  // 不需要合并，返回默认
  return { rowspan: 1, colspan: 1 };
};

// 字段表格合并单元格方法（合并值域及含义和量纲列）
const fieldSpanMethod = ({ columnIndex }: any) => {
  // 值域及含义列的索引
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
};

// 监听本地配置变化，同步到父组件
watch(
  () => localConfig,
  newVal => {
    syncConfigTableRows();
    emit('update:modelValue', newVal);
  },
  { deep: true }
);

// 监听外部值变化
watch(
  () => props.modelValue,
  newVal => {
    if (newVal && Object.keys(newVal).length > 0) {
      Object.assign(localConfig, newVal);
    }
  },
  { deep: true }
);

// 新增行
const insertRow = async () => {
  // 自动计算下一个序号
  const nextSeqNo =
    localConfig.fields.length > 0
      ? Math.max(...localConfig.fields.map((f: any) => parseInt(f.序号) || 0)) + 1
      : 1;

  const newRow = {
    序号: nextSeqNo.toString(),
    信息名称: '',
    字节数: '',
    字节序号: '',
    值域及含义: '',
    量纲: '',
    数据类型: '',
    比例尺: '1',
    备注: '',
  };
  localConfig.fields.push(newRow);
};

// 删除行
const removeRow = (rowIndex: number) => {
  localConfig.fields.splice(rowIndex, 1);
};

// 删除选中行
const removeSelectRow = async () => {
  const selectRecords = await tableRef.value?.getCheckboxRecords();
  if (selectRecords && selectRecords.length > 0) {
    selectRecords.forEach((row: any) => {
      const index = localConfig.fields.findIndex((item: any) => item === row);
      if (index > -1) {
        localConfig.fields.splice(index, 1);
      }
    });
  }
};
</script>

<style scoped>
/* 最小化样式，主要使用 Tailwind */
</style>
