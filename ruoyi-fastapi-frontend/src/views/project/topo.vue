<template>
<ZxContentWrap class="home">
  <XflowDAG
    ref="dagRef"
    :operators="operators"
    :operators-loading="loading"
    :layout="layoutMode"
    :dnd-config="dndConfig"
    @node-dblclick="handleNodeDblclick"
  />
  
  <!-- 节点编辑抽屉 -->
  <NodeEditDrawer
    v-model="drawerVisible"
    :node-data="currentNode"
    @submit="handleNodeUpdate"
  />
  </ZxContentWrap>
</template>

<script setup name="Index">
import { ref, onMounted } from 'vue'
import XflowDAG from "@/components/business/Dag/index.vue"
import { NodeEditDrawer } from './components'
import { listDevice, getDevice } from '@/api/device/device'
import { ElMessage } from 'element-plus'

const version = ref('3.9.0')

// DAG 组件配置 - 设备列表（从后端获取）
const operators = ref([])
const loading = ref(false)
const layoutMode = ref('horizontal') // 'vertical' | 'horizontal'

// DAG 组件引用
const dagRef = ref(null)

// 节点编辑抽屉
const drawerVisible = ref(false)
const currentNode = ref(null)

// 可配置的文案和设置
const dndConfig = {
  title: '设备库',
  searchPlaceholder: '搜索设备...',
  textConfig: {
    loadingText: '正在加载设备库...',
    emptySearchText: '没有找到匹配的设备',
    emptySearchDesc: '请尝试使用其他关键词搜索',
    emptyDataText: '暂无可用设备',
    emptyDataDesc: '请先添加设备数据'
  }
}

/**
 * 根据总线类型获取端口颜色
 * @param {String} busType - 总线类型
 * @returns {String} 颜色值
 */
function getBusTypeColor(busType) {
  const colorMap = {
    'RS422': '#f59e0b',  // 琥珀色 - 串口通信
    'RS485': '#f97316',  // 橙色 - 工业串口
    'CAN': '#3b82f6',    // 蓝色 - CAN总线
    'LAN': '#10b981',    // 绿色 - 以太网
    '1553B': '#8b5cf6'   // 紫色 - 军用总线
  }
  return colorMap[busType] || '#6b7280'  // 默认灰色
}

/**
 * 获取设备的端口信息（从后端获取）
 * @param {Number} deviceId - 设备ID
 * @returns {Promise<Array>} 端口列表
 */
async function getDevicePorts(deviceId) {
  try {
    const response = await getDevice(deviceId)
    const deviceData = response.data || response
    const interfaces = deviceData.interfaces || []
    
    // 将接口数据转换为端口格式
    return interfaces.map((intf, index) => {
      // 根据接口类型确定端口类型
      let interfaceType = 'bidirectional' // 默认双向
      if (intf.interfaceType === '输入' || intf.interfaceType === 'input') {
        interfaceType = 'input'
      } else if (intf.interfaceType === '输出' || intf.interfaceType === 'output') {
        interfaceType = 'output'
      }
      
      // 根据索引分配到不同的组（位置）
      // 只分配到左右两侧
      const groups = ['left', 'right']
      const group = groups[index % 2]
      
      return {
        id: `port-${intf.interfaceId || index}`,
        interfaceId: intf.interfaceId,
        interfaceName: intf.interfaceName || `端口${index + 1}`,
        interfaceType: interfaceType,
        group: group,
        description: intf.remark || '',
        busType: intf.busType || 'RS422',  // 总线类型
        color: getBusTypeColor(intf.busType || 'RS422'),  // 根据总线类型计算颜色
        dataRate: intf.dataRate || '',
        protocolType: intf.protocolType || ''
      }
    })
  } catch (error) {
    console.error(`获取设备${deviceId}的接口信息失败:`, error)
    return []
  }
}

/**
 * 从后端加载设备列表数据
 */
async function loadDeviceList() {
  loading.value = true
  try {
    // 从后端获取设备列表
    const response = await listDevice({})
    const devices = response.data?.rows || []
    
    if (devices.length === 0) {
      ElMessage.warning('暂无设备数据，请先添加设备')
      operators.value = []
      return
    }
    // 并发获取所有设备的端口信息
    const devicesWithPorts = await Promise.all(
      devices.map(async (device) => {
        const ports = await getDevicePorts(device.deviceId)
        
        return {
          // DAG组件需要的字段
          name: device.deviceName,
          value: device.remark || device.deviceDesc || '设备',
          category: device.categoryName || device.category || '未分类',
          
          // 设备原始数据（用于节点创建时使用）
          deviceId: device.deviceId,
          deviceType: device.deviceType,
          busType: device.busType,
          manufacturer: device.manufacturer,
          model: device.model,
          version: device.version,
          
          // 端口信息（用于连接桩）
          ports: ports,
          
          // 节点类型标识
          nodeType: 'device-port-node'
        }
      })
    )
    
    operators.value = devicesWithPorts
    
    console.log('设备列表加载成功:', {
      total: devicesWithPorts.length,
      devices: devicesWithPorts
    })
    
  } catch (error) {
    console.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败，请稍后重试')
    operators.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 处理节点双击事件
 * @param {Object} params - 包含 node, event, type
 */
function handleNodeDblclick({ node, event, type }) {
  console.log('节点双击:', { node, event, type })
  
  // 保存当前节点数据
  currentNode.value = node
  
  // 打开抽屉
  drawerVisible.value = true
}

/**
 * 处理节点更新
 * @param {Object} params - 包含 nodeId, node, name
 */
function handleNodeUpdate({ nodeId, node, name }) {
  console.log('更新节点:', { nodeId, node, name })
  
  // 获取图实例
  const graph = dagRef.value?.getGraph()
  if (!graph) {
    console.error('图实例不存在')
    ElMessage.error('更新失败：图实例不存在')
    return
  }
  
  // 通过节点ID获取节点实例
  const cellNode = graph.getCellById(nodeId)
  if (!cellNode) {
    ElMessage.error('更新失败：节点不存在')
    return
  }
  
  // 获取当前节点数据
  const currentData = cellNode.getData() || {}
  
  // 更新节点数据（包含 label 和 name 字段）
  const updatedData = {
    ...currentData,
    name: name,
    label: name
  }
  
  // 如果存在 properties.content 结构，也更新里面的 label
  if (currentData.properties?.content) {
    updatedData.properties = {
      ...currentData.properties,
      content: {
        ...currentData.properties.content,
        label: name
      }
    }
  }
  
  // 使用 setData 方法更新节点数据
  // 节点组件会通过 watch 监听数据变化并自动重新渲染
  cellNode.setData(updatedData, { overwrite: false })
  
  // 如果需要更新到后端，可以在这里调用 API
  // await updateNodeName(nodeId, name)
    
}

// 页面加载时获取设备列表
onMounted(() => {
  loadDeviceList()
})

function goTarget(url) {
  window.open(url, '__blank')
}
</script>

<style lang="less">
.home {
  height: calc(100vh - 84px);
  display: flex;
  flex-direction: column;
  &.v-content-wrap .el-card__body {
    height: 100%;
  }
}
</style>
