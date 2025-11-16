<template>
  <div class="selector-test">
    <h3>选择器组件测试</h3>
    
    <div class="test-section">
      <h4>总线类型选择器</h4>
      <InterfaceTypeSelector
        v-model="interfaceType"
        @change="onInterfaceTypeChange"
      />
      <p>当前选择：{{ interfaceType }}</p>
    </div>
    
    <div class="test-section">
      <h4>端口位置选择器</h4>
      <PositionSelector
        v-model="position"
        @change="onPositionChange"
      />
      <p>当前选择：{{ position }}</p>
    </div>
    
    <div class="test-section">
      <h4>自定义选项的总线类型选择器</h4>
      <InterfaceTypeSelector
        v-model="customInterfaceType"
        :options="customInterfaceOptions"
        @change="onCustomInterfaceTypeChange"
      />
      <p>当前选择：{{ customInterfaceType }}</p>
    </div>
  </div>
</template>

<script setup name="SelectorTest">
import { ref } from 'vue'
import { InterfaceTypeSelector, PositionSelector } from './index'

// 测试数据
const interfaceType = ref('RS422')
const position = ref('right')
const customInterfaceType = ref('')

// 自定义选项
const customInterfaceOptions = [
  { label: 'USB', value: 'USB' },
  { label: 'HDMI', value: 'HDMI' },
  { label: 'VGA', value: 'VGA' }
]

// 事件处理
const onInterfaceTypeChange = (value) => {
  console.log('总线类型变化:', value)
}

const onPositionChange = (value) => {
  console.log('位置变化:', value)
}

const onCustomInterfaceTypeChange = (value) => {
  console.log('自定义总线类型变化:', value)
}
</script>

<style lang="scss" scoped>
.selector-test {
  padding: 20px;
  max-width: 600px;
  
  .test-section {
    margin-bottom: 30px;
    padding: 15px;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    
    h4 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #303133;
    }
    
    p {
      margin-top: 10px;
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>