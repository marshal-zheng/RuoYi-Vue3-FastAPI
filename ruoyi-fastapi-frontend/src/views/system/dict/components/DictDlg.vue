<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="rules" label-width="80px">
      <el-form-item label="字典名称" prop="dictName">
        <el-input v-model="state.data.dictName" placeholder="请输入字典名称" />
      </el-form-item>
      <el-form-item label="字典类型" prop="dictType">
        <el-input v-model="state.data.dictType" placeholder="请输入字典类型" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="state.data.status">
          <el-radio v-for="dict in sysNormalDisable" :key="dict.value" :value="dict.value">
            {{ dict.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="备注" prop="remark">
        <el-input v-model="state.data.remark" type="textarea" placeholder="请输入内容" />
      </el-form-item>
    </el-form>
  </zx-dialog>
</template>

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue'
import { useDialog } from '@zxio/zxui'
import { addType, updateType } from '@/api/system/dict/type'
import { useDict } from '@/utils/dict'

const { proxy } = getCurrentInstance() as any

// 延迟加载字典数据
let sysNormalDisable = ref<any[]>([])
let dictLoaded = false

interface DictForm {
  dictId?: number
  dictName: string
  dictType: string
  status: string
  remark: string
}

const formRef = ref()

const rules = {
  dictName: [{ required: true, message: '字典名称不能为空', trigger: 'blur' }],
  dictType: [{ required: true, message: '字典类型不能为空', trigger: 'blur' }]
}

const { state, dialogProps, dialogEvents, open } = useDialog<DictForm>({
  title: (data: DictForm) => data.dictId ? '修改字典类型' : '添加字典类型',
  width: '500px',
  defaultData: () => ({
    dictId: undefined,
    dictName: '',
    dictType: '',
    status: '0',
    remark: ''
  }),
  onOpen: () => {
    // 只在第一次打开时加载字典
    if (!dictLoaded) {
      const dict = useDict('sys_normal_disable')
      // useDict 返回的键名是原始的 dictType，不是驼峰命名
      sysNormalDisable.value = dict.sys_normal_disable?.value || []
      dictLoaded = true
    }
  },
  onConfirm: async (data: DictForm) => {
    if (data.dictId) {
      await updateType(data)
    } else {
      await addType(data)
    }
    return true
  }
})

defineExpose({ open })
</script>
