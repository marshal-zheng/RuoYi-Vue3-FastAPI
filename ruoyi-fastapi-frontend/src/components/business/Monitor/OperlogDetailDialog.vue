<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="py-4">
      <el-form :model="state.data" label-width="100px" class="space-y-2">
        <el-row :gutter="16">
          <el-col :span="12" class="space-y-2">
            <el-form-item label="操作模块：">
              <div class="text-gray-800">
                {{ state.data.title }}
                <span class="mx-1 text-gray-400">/</span>
                {{ typeFormat(state.data) }}
              </div>
            </el-form-item>
            <el-form-item label="登录信息：">
              <div class="text-gray-700">
                {{ state.data.operName }}
                <span class="mx-1 text-gray-400">/</span>
                {{ state.data.operIp }}
                <span class="mx-1 text-gray-400">/</span>
                {{ state.data.operLocation }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12" class="space-y-2">
            <el-form-item label="请求地址：">
              <div class="text-gray-700 break-all">{{ state.data.operUrl }}</div>
            </el-form-item>
            <el-form-item label="请求方式：">
              <div class="text-gray-700">{{ state.data.requestMethod }}</div>
            </el-form-item>
          </el-col>
          <el-col :span="24" class="space-y-2">
            <el-form-item label="操作方法：">
              <div class="text-gray-700 break-all">{{ state.data.method }}</div>
            </el-form-item>
          </el-col>
          <el-col :span="24" class="space-y-2">
            <el-form-item label="请求参数：">
              <div
                class="rounded bg-gray-50 dark:bg-gray-800/40 p-3 text-gray-700 text-sm whitespace-pre-wrap break-words max-h-48 overflow-auto"
              >
                {{ state.data.operParam }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="24" class="space-y-2">
            <el-form-item label="返回参数：">
              <div
                class="rounded bg-gray-50 dark:bg-gray-800/40 p-3 text-gray-700 text-sm whitespace-pre-wrap break-words max-h-48 overflow-auto"
              >
                {{ state.data.jsonResult }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8" class="space-y-2">
            <el-form-item label="操作状态：">
              <span
                v-if="state.data.status === 0"
                class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-green-50 text-green-600 ring-1 ring-inset ring-green-200"
                >正常</span
              >
              <span
                v-else-if="state.data.status === 1"
                class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-red-50 text-red-600 ring-1 ring-inset ring-red-200"
                >失败</span
              >
            </el-form-item>
          </el-col>
          <el-col :span="8" class="space-y-2">
            <el-form-item label="消耗时间：">
              <div class="text-gray-700">{{ state.data.costTime }}毫秒</div>
            </el-form-item>
          </el-col>
          <el-col :span="8" class="space-y-2">
            <el-form-item label="操作时间：">
              <div class="text-gray-700">{{ parseTime(state.data.operTime) }}</div>
            </el-form-item>
          </el-col>
          <el-col :span="24" class="space-y-2">
            <el-form-item label="异常信息：" v-if="state.data.status === 1">
              <div
                class="rounded bg-red-50 dark:bg-red-900/30 p-3 text-red-700 dark:text-red-200 text-sm whitespace-pre-wrap break-words"
              >
                {{ state.data.errorMsg }}
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup>
import { computed, getCurrentInstance } from 'vue';
import { useDialog } from '@zxio/zxui';
import { parseTime } from '@/utils/ruoyi';

const { proxy } = getCurrentInstance();
const { sys_oper_type } = proxy.useDict('sys_oper_type');

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  title: () => '操作日志详细',
  width: '800px',
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
