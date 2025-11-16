<template>
  <ZxContentWrap title="操作日志">
    <template #header-right>
      <ZxButton
        type="warning"
        icon="Download"
        @click="() => operlogGridRef?.exportCurrent?.()"
        v-hasPermi="['monitor:operlog:export']"
      >导出</ZxButton>
    </template>
    <OperlogGrid 
      ref="operlogGridRef" 
      module="工程管理"
      @selection-change="onSelectionChange" 
    ><template #filters><span></span></template></OperlogGrid>
  </ZxContentWrap>
</template>

<script setup name="ProjectOperlog">
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
