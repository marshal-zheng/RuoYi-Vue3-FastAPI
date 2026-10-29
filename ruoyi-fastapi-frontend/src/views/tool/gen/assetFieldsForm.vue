<template>
  <div>
    <el-alert type="info" :closable="false" show-icon>
      文件字段是逻辑关系字段，不是表中的物理列：生成代码保存资产ID数组，在同一事务内绑定与释放，并按菜单权限读取。
      类型只能从已登记类型中选择；同一表单所有文件字段的“数量 ×
      单个上限”之和须在用户草稿配额内（服务端校验）。 当前合计：{{ totalCount }} 个 /
      {{ totalMb }} MB。
    </el-alert>
    <el-table :data="fields" class="asset-fields">
      <el-table-column label="字段名" min-width="150">
        <template #default="{ row }">
          <zx-input v-model="row.fieldName" placeholder="camelCase，如 attachments" />
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="120">
        <template #default="{ row }">
          <zx-input v-model="row.label" />
        </template>
      </el-table-column>
      <el-table-column label="种类" min-width="110">
        <template #default="{ row }">
          <el-select v-model="row.assetKind" @change="onKindChange(row)">
            <el-option label="图片" value="image" />
            <el-option label="文件" value="file" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="允许类型" min-width="220">
        <template #default="{ row }">
          <el-select v-model="row.allowedTypeIds" multiple collapse-tags placeholder="至少选择一项">
            <el-option
              v-for="option in typeOptions(row.assetKind)"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="单个上限(MB)" min-width="140">
        <template #default="{ row }">
          <el-input-number
            :model-value="row.maxBytes / MIB"
            :min="0.01"
            :max="ceilingMb(row.assetKind)"
            :precision="2"
            :step="1"
            controls-position="right"
            @update:model-value="(value) => (row.maxBytes = Math.round((value || 0) * MIB))"
          />
        </template>
      </el-table-column>
      <el-table-column label="数量" min-width="110">
        <template #default="{ row }">
          <el-input-number v-model="row.maxCount" :min="1" :max="50" controls-position="right" />
        </template>
      </el-table-column>
      <el-table-column label="必填" min-width="60">
        <template #default="{ row }"><el-checkbox v-model="row.required" /></template>
      </el-table-column>
      <el-table-column label="列表" min-width="60">
        <template #default="{ row }"><el-checkbox v-model="row.showInList" /></template>
      </el-table-column>
      <el-table-column label="操作" min-width="70">
        <template #default="{ $index }">
          <el-button link type="danger" @click="fields.splice($index, 1)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-button class="asset-fields__add" type="primary" plain icon="Plus" @click="addField">
      添加文件字段
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import registry from '@/utils/file-assets/types.generated.json';

const props = defineProps({
  /** 生成配置（info.assetFields 为逻辑文件字段声明数组） */
  info: { type: Object, required: true },
});

const MIB = 1024 * 1024;
// The edit page always loads the declaration as an array (empty when none is declared).
const fields = computed(() => props.info.assetFields);
const totalCount = computed(() =>
  fields.value.reduce((sum, field) => sum + (field.maxCount || 0), 0)
);
const totalMb = computed(() =>
  (
    fields.value.reduce((sum, field) => sum + (field.maxCount || 0) * (field.maxBytes || 0), 0) /
    MIB
  ).toFixed(1)
);

function typeOptions(kind) {
  return Object.entries(registry.types)
    .filter(([, type]) => (kind === 'image' ? type.family === 'image' : true))
    .map(([value, type]) => ({ value, label: `${value}（${type.extensions.join('/')}）` }));
}
function ceilingMb(kind) {
  return (kind === 'image' ? registry.maxImageBytes : registry.maxAttachmentBytes) / MIB;
}
function onKindChange(row) {
  // Types are a declaration, never a default "everything" set: switching kind drops incompatible ones.
  const allowed = new Set(typeOptions(row.assetKind).map((option) => option.value));
  row.allowedTypeIds = row.allowedTypeIds.filter((typeId) => allowed.has(typeId));
  row.maxBytes = Math.min(row.maxBytes, ceilingMb(row.assetKind) * MIB);
}
function addField() {
  fields.value.push({
    fieldName: '',
    label: '',
    assetKind: 'file',
    allowedTypeIds: [],
    maxBytes: 10 * MIB,
    maxCount: 5,
    required: false,
    showInList: false,
  });
}
</script>

<style scoped>
.asset-fields {
  margin-top: 12px;
}
.asset-fields__add {
  margin-top: 12px;
}
</style>
