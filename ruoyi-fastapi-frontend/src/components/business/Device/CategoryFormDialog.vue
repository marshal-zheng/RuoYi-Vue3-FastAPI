<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="py-4">
      <el-form ref="formRef" :model="state.data" :rules="formRules" label-width="100px" label-position="right">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="state.data.name" placeholder="请输入分类名称" maxlength="50" show-word-limit clearable />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="state.data.remark" type="textarea" placeholder="请输入备注" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FormInstance } from 'element-plus'
import { useDialog } from '@zxio/zxui'
import { addDeviceCategory, updateDeviceCategory, getDeviceCategory } from '@/api/device/category'

const emit = defineEmits<{ success: [data?: any] }>()

const formRef = ref<FormInstance>()

const formRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 2, max: 50, message: '分类名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  remark: [
    { max: 500, message: '备注不能超过 500 个字符', trigger: 'blur' }
  ]
}

const { state, dialogProps, dialogEvents, open, close } = useDialog<any>({
  title: (data) => (data?.device_category_id ? '修改设备分类' : '添加设备分类'),
  width: '600px',
  okText: computed(() => (state.data.device_category_id ? '保存' : '创建')),
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    device_category_id: null,
    name: '',
    remark: ''
  }),
  onConfirm: async (data) => {
    const submitData: any = {
      device_category_id: data.device_category_id,
      name: data.name,
      remark: data.remark
    }
    let res
    if (submitData.device_category_id) {
      res = await updateDeviceCategory(submitData)
    } else {
      res = await addDeviceCategory(submitData)
    }
    emit('success', res)
    return res
  },
  onConfirmError: (_e) => {}
})

const openDialog = async (payload?: { id?: number }) => {
  if (payload?.id) {
    const detail = await getDeviceCategory(payload.id)
    open({
      device_category_id: detail.data?.deviceCategoryId || detail.data?.device_category_id || payload.id,
      name: detail.data?.name || '',
      remark: detail.data?.remark || ''
    })
  } else {
    open()
  }
}

defineExpose({ open: openDialog, close })
</script>