<template>
  <div class="app-container">
    <el-form ref="formRef" :model="formData" :rules="rules" size="default" label-width="100px">
      <el-form-item label="手机号" prop="mobile">
        <zx-input v-model="formData.mobile" placeholder="请输入手机号" :maxlength="11" show-word-limit clearable
          prefix-icon='Cellphone' :style="{width: '100%'}"></zx-input>
      </el-form-item>
      <el-form-item label="单行文本" prop="field101">
        <zx-input v-model="formData.field101" type="text" placeholder="请输入单行文本" clearable
          :style="{width: '100%'}"></zx-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm">提交</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
<script setup>
import {
  ref,
  reactive,
  computed,
  watch
}
from 'vue'
import {
  ElForm,
  ElFormItem,
  ElButton,
  ElRow,
  ElCol
}
from 'element-plus'
import {
  ZxInput
}
from '@zxio/zxui'
const formRef = ref()
const rules = reactive({
  mobile: [{
    required: true,
    message: '请输入手机号',
    trigger: 'blur'
  }, {
    pattern: new RegExp(/^1(3|4|5|7|8|9)\d{9}$/),
    message: '手机号格式错误',
    trigger: 'blur'
  }],
  field101: [{
    required: true,
    message: '请输入单行文本',
    trigger: 'blur'
  }],
})
const formData = reactive({
  mobile: "",
  field101: undefined,
})
async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  // TODO 提交表单。
}

function resetForm() {
  formRef.value.resetFields()
}

</script>
<style>
</style>
