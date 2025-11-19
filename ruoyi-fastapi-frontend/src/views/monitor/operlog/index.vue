<template>
  <ZxContentWrap>
    <template #header-right>
      <ZxButton
        type="danger"
        icon="Delete"
        :disabled="multiple"
        @click="() => operlogGridRef?.deleteSelected?.()"
        v-hasPermi="['monitor:operlog:remove']"
      >删除</ZxButton>
      <ZxButton
        type="danger"
        icon="Delete"
        @click="() => operlogGridRef?.cleanAll?.()"
        v-hasPermi="['monitor:operlog:remove']"
      >清空</ZxButton>
      <ZxButton
        type="warning"
        icon="Download"
        @click="() => operlogGridRef?.exportCurrent?.()"
        v-hasPermi="['monitor:operlog:export']"
      >导出</ZxButton>
    </template>
    <OperlogGrid ref="operlogGridRef" @selection-change="onSelectionChange" />
  </ZxContentWrap>
</template>

<script setup name="Operlog">
import { OperlogGrid } from '@/components/business/Monitor'

const operlogGridRef = ref()
const ids = ref([])
const single = ref(true)
const multiple = ref(true)

function onSelectionChange(val) {
  ids.value = val
  single.value = val.length != 1
  multiple.value = !val.length
}
</script>
