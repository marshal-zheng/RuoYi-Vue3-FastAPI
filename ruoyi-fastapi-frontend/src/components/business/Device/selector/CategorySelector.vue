<template>
  <el-select 
    :model-value="modelValue"
    @update:model-value="handleChange"
    :placeholder="placeholder"
    :style="{ width: '100%', ...customStyle }"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
    :loading="loading"
  >
    <el-option 
      v-for="option in categoryOptions" 
      :key="option.value"
      :label="option.label" 
      :value="option.value" 
    />
  </el-select>
</template>

<script setup name="CategorySelector">
import { ref, onMounted } from 'vue'
import { getDeviceCategoryOptions } from '@/api/device/category'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择设备分类'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  },
  size: {
    type: String,
    default: 'default'
  },
  customStyle: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change'])

// 数据
const loading = ref(false)
const categoryOptions = ref([])

// 加载分类列表
async function loadCategories() {
  loading.value = true
  try {
    // 使用业务类型 9999 获取分类列表
    const response = await getDeviceCategoryOptions('9999')
    // 根据后端返回的数据格式处理
    const categories = response.data || response.rows || []
    
    // 转换为选项格式
    categoryOptions.value = categories.map(item => ({
      label: item.category_name || item.name || item.categoryName,
      value: item.category_name || item.name || item.categoryName
    }))
    
    // 如果没有数据,提供默认分类
    if (categoryOptions.value.length === 0) {
      categoryOptions.value = [
        { label: '核心控制', value: '核心控制' },
        { label: '定位导航', value: '定位导航' },
        { label: '遥控通信', value: '遥控通信' },
        { label: '传感器', value: '传感器' },
        { label: '执行器', value: '执行器' },
        { label: '其他', value: '其他' }
      ]
    }
  } catch (error) {
    console.error('加载设备分类失败:', error)
    ElMessage.error('加载设备分类失败')
    // 提供默认分类
    categoryOptions.value = [
      { label: '核心控制', value: '核心控制' },
      { label: '定位导航', value: '定位导航' },
      { label: '遥控通信', value: '遥控通信' },
      { label: '传感器', value: '传感器' },
      { label: '执行器', value: '执行器' },
      { label: '其他', value: '其他' }
    ]
  } finally {
    loading.value = false
  }
}

// 处理值变化
const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 组件挂载时加载分类
onMounted(() => {
  loadCategories()
})
</script>

<style lang="less" scoped>
// 可以在这里添加自定义样式
</style>

