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
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: ''
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
</script>