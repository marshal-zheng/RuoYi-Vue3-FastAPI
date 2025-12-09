<template>
  <el-drawer
    :model-value="visible"
    title="事件触发配置"
    direction="rtl"
    size="400px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="flex flex-col h-full">
      <!-- 事件列表 -->
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="event in events"
          :key="event.eventId"
          class="p-4 mb-3 rounded-lg transition-colors"
          :class="event.status === 'triggered' ? 'bg-success-50 border border-success-200' : 'bg-gray-50'"
        >
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold text-gray-800">{{ event.name }}</span>
            <el-tag :type="getStatusType(event.status)" size="small">
              {{ getStatusText(event.status) }}
            </el-tag>
          </div>
          <div class="text-xs text-gray-500 mb-3 space-y-1">
            <div>条件: {{ getConditionText(event.condition) }}</div>
            <div>动作: {{ getActionText(event.action) }}</div>
          </div>
          <div class="flex gap-2">
            <el-button size="small" @click="$emit('trigger', event.eventId)">手动触发</el-button>
            <el-button size="small" @click="handleEdit(event)">编辑</el-button>
            <el-button size="small" type="danger" @click="$emit('delete', event.eventId)">删除</el-button>
          </div>
        </div>

        <div v-if="events.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-400">
          <el-icon class="text-5xl mb-3"><Lightning /></el-icon>
          <span class="text-sm">暂无事件配置</span>
        </div>
      </div>

      <!-- 添加按钮 -->
      <el-button type="primary" class="mt-4" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加事件
      </el-button>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingEvent ? '编辑事件' : '添加事件'"
      width="500px"
      append-to-body
    >
      <el-form :model="eventForm" label-width="80px">
        <el-form-item label="事件名称">
          <el-input v-model="eventForm.name" placeholder="请输入事件名称" />
        </el-form-item>

        <el-divider>触发条件</el-divider>

        <el-form-item label="条件类型">
          <el-select v-model="eventForm.conditionType" placeholder="选择条件类型">
            <el-option label="时间点" value="time" />
            <el-option label="报文数量" value="message_count" />
            <el-option label="带宽阈值" value="bandwidth_threshold" />
            <el-option label="报文内容" value="message_content" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="eventForm.conditionType === 'time'" label="触发时间">
          <el-input-number v-model="eventForm.conditionValue.time" :min="0" />
          <span class="ml-2 text-gray-500">秒</span>
        </el-form-item>

        <el-form-item v-if="eventForm.conditionType === 'message_count'" label="报文数量">
          <el-input-number v-model="eventForm.conditionValue.count" :min="1" />
        </el-form-item>

        <el-form-item v-if="eventForm.conditionType === 'bandwidth_threshold'" label="阈值">
          <el-input-number v-model="eventForm.conditionValue.threshold" :min="0" :max="100" />
          <span class="ml-2 text-gray-500">%</span>
        </el-form-item>

        <el-divider>触发动作</el-divider>

        <el-form-item label="动作类型">
          <el-select v-model="eventForm.actionType" placeholder="选择动作类型">
            <el-option label="暂停仿真" value="pause" />
            <el-option label="记录日志" value="log" />
            <el-option label="注入故障" value="inject_fault" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="eventForm.actionType === 'log'" label="日志内容">
          <el-input v-model="eventForm.actionParams.message" placeholder="请输入日志内容" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Lightning, Plus } from '@element-plus/icons-vue'
import { CONDITION_TYPE_CONFIG, ACTION_TYPE_CONFIG } from '../composables/useEventTrigger'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  events: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:visible', 'create', 'edit', 'delete', 'trigger'])

const showAddDialog = ref(false)
const editingEvent = ref(null)

const eventForm = reactive({
  name: '',
  conditionType: 'time',
  conditionValue: { time: 10 },
  actionType: 'pause',
  actionParams: {},
})

function getStatusType(status) {
  const map = {
    pending: 'info',
    triggered: 'success',
    disabled: 'warning',
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    pending: '待触发',
    triggered: '已触发',
    disabled: '已禁用',
  }
  return map[status] || status
}

function getConditionText(condition) {
  if (!condition) return '-'
  const config = CONDITION_TYPE_CONFIG[condition.type]
  if (!config) return condition.type
  return `${config.label}: ${JSON.stringify(condition.value)}`
}

function getActionText(action) {
  if (!action) return '-'
  const config = ACTION_TYPE_CONFIG[action.type]
  if (!config) return action.type
  return config.label
}

function handleEdit(event) {
  editingEvent.value = event
  eventForm.name = event.name
  eventForm.conditionType = event.condition?.type || 'time'
  eventForm.conditionValue = { ...event.condition?.value }
  eventForm.actionType = event.action?.type || 'pause'
  eventForm.actionParams = { ...event.action?.params }
  showAddDialog.value = true
}

function handleSave() {
  const config = {
    name: eventForm.name,
    condition: {
      type: eventForm.conditionType,
      value: eventForm.conditionValue,
    },
    action: {
      type: eventForm.actionType,
      params: eventForm.actionParams,
    },
  }

  if (editingEvent.value) {
    emit('edit', editingEvent.value.eventId, config)
  } else {
    emit('create', config)
  }

  showAddDialog.value = false
  resetForm()
}

function resetForm() {
  editingEvent.value = null
  eventForm.name = ''
  eventForm.conditionType = 'time'
  eventForm.conditionValue = { time: 10 }
  eventForm.actionType = 'pause'
  eventForm.actionParams = {}
}

watch(
  () => eventForm.conditionType,
  (type) => {
    switch (type) {
      case 'time':
        eventForm.conditionValue = { time: 10 }
        break
      case 'message_count':
        eventForm.conditionValue = { count: 100 }
        break
      case 'bandwidth_threshold':
        eventForm.conditionValue = { threshold: 80 }
        break
      case 'message_content':
        eventForm.conditionValue = { pattern: '' }
        break
    }
  }
)
</script>
