<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form
      ref="codeTypeForm"
      :model="state.data"
      :rules="rules"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="生成类型" prop="type">
          <el-radio-group v-model="state.data.type">
            <el-radio-button
              v-for="item in typeOptions"
              :key="item.value"
              :value="item.value"
            >
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="showFileName" label="文件名" prop="fileName">
          <zx-input
            v-model="state.data.fileName"
            placeholder="请输入文件名"
            clearable
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup>
import { ref, watch } from "vue";
import { ZxDialog } from "@zxio/zxui/dialog";
import { FormGrid, useFormDialog } from "@/components/ui/FormDialog";

const visible = defineModel();
const props = defineProps({ showFileName: Boolean });
const emit = defineEmits(["confirm"]);
const codeTypeForm = ref();
const rules = {
  fileName: [{ required: true, message: "请输入文件名", trigger: "blur" }],
  type: [{ required: true, message: "生成类型不能为空", trigger: "change" }],
};
const typeOptions = [
  { label: "页面", value: "file" },
  { label: "弹窗", value: "dialog" },
];
const {
  state,
  dialogProps,
  dialogEvents,
  formProps,
  layoutProps,
  open,
  close,
} = useFormDialog({
  columns: 1,
  title: "选择生成类型",
  formRef: codeTypeForm,
  defaultData: () => ({ fileName: "", type: "file" }),
  onOpen(data) {
    if (props.showFileName) data.fileName = `${Date.now()}.vue`;
  },
  onConfirm(data) {
    emit("confirm", { ...data });
  },
});
watch(
  visible,
  (value) => {
    if (value !== state.visible) value ? open() : close();
  },
  { immediate: true },
);
watch(
  () => state.visible,
  (value) => {
    visible.value = value;
  },
);
</script>
