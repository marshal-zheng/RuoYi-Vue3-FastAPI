<template>
  <DictSelect
    v-model="selectedValue"
    dict-type="sys_protocol_type"
    placeholder="请选择协议类型"
    clearable
    v-bind="$attrs"
    @change="handleChange"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import DictSelect from '@/components/DictSelect/index.vue'

interface Props {
  modelValue?: string
  busType?: string // 总线类型，用于过滤可选的协议类型
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  busType: ''
})

const emit = defineEmits<Emits>()

const selectedValue = ref(props.modelValue)

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  selectedValue.value = newValue
})

// 处理选择变化
const handleChange = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// Note: 如果需要根据 busType 过滤协议类型，可以在这里添加过滤逻辑
// 目前保持简单，通过字典数据配置来管理协议类型与总线类型的关系
</script>