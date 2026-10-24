<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="py-4">
      <DictStatus :types="['sys_oper_type']" />
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作模块：">
          <div class="text-zx-text-primary">
            {{ state.data.title }}
            <span class="mx-1 text-zx-text-secondary">/</span>
            {{ typeFormat(state.data) }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="登录信息：">
          <div class="text-zx-text-primary">
            {{ state.data.operName }}
            <span class="mx-1 text-zx-text-secondary">/</span>
            {{ state.data.operIp }}
            <span class="mx-1 text-zx-text-secondary">/</span>
            {{ state.data.operLocation }}
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="请求地址：">
          <div class="text-zx-text-primary break-all">
            {{ state.data.operUrl }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="请求方式：">
          <div class="text-zx-text-primary">{{ state.data.requestMethod }}</div>
        </el-descriptions-item>

        <el-descriptions-item label="操作方法：">
          <div class="text-zx-text-primary break-all">
            {{ state.data.method }}
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="请求参数：">
          <div
            class="rounded bg-zx-surface-canvas-fill p-3 text-zx-surface-canvas-on-text text-sm whitespace-pre-wrap break-words max-h-48 overflow-auto"
          >
            {{ state.data.operParam }}
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="返回参数：">
          <div
            class="rounded bg-zx-surface-canvas-fill p-3 text-zx-surface-canvas-on-text text-sm whitespace-pre-wrap break-words max-h-48 overflow-auto"
          >
            {{ state.data.jsonResult }}
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="操作状态：">
          <span
            v-if="state.data.status === 0"
            class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-zx-status-success-tint-9 text-zx-status-success-on-surface"
            >正常</span
          >
          <span
            v-else-if="state.data.status === 1"
            class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-zx-status-danger-tint-9 text-zx-status-danger-on-surface"
            >失败</span
          >
        </el-descriptions-item>

        <el-descriptions-item label="消耗时间：">
          <div class="text-zx-text-primary">{{ state.data.costTime }}毫秒</div>
        </el-descriptions-item>

        <el-descriptions-item label="操作时间：">
          <div class="text-zx-text-primary">
            {{ parseTime(state.data.operTime) }}
          </div>
        </el-descriptions-item>

        <el-descriptions-item label="异常信息：" v-if="state.data.status === 1">
          <div
            class="rounded bg-zx-status-danger-tint-9 p-3 text-zx-status-danger-on-surface text-sm whitespace-pre-wrap break-words"
          >
            {{ state.data.errorMsg }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </ZxDialog>
</template>

<script setup>
import { computed, getCurrentInstance } from 'vue';
import { useDialog } from '@zxio/zxui/hooks';
import { parseTime } from '@/utils/ruoyi';

const { proxy } = getCurrentInstance();

const { sys_oper_type } = proxy.useDict('sys_oper_type');

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  dialogSize: 'lg',
  title: () => '操作日志详细',

  okText: computed(() => '关闭'),
  defaultData: () => ({
    operId: null,
    title: '',
    businessType: undefined,
    operName: '',
    operIp: '',
    operLocation: '',
    operUrl: '',
    requestMethod: '',
    method: '',
    operParam: '',
    jsonResult: '',
    status: 0,
    costTime: 0,
    operTime: '',
    errorMsg: '',
  }),
  onConfirm: async () => {
    close();
    return state.data;
  },
});

function typeFormat(row) {
  return proxy.selectDictLabel(sys_oper_type.value, row.businessType);
}

function openDialog(payload) {
  open(payload || {});
}

defineExpose({ open: openDialog, close });
</script>

<style scoped></style>
