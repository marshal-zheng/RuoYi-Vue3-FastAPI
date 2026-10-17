<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form
      ref="treeNodeForm"
      :model="state.data"
      :rules="rules"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="选项名" prop="label">
          <zx-input
            v-model="state.data.label"
            placeholder="请输入选项名"
            clearable
          />
        </el-form-item>
        <el-form-item label="选项值" prop="value">
          <zx-input
            v-model="state.data.value"
            placeholder="请输入选项值"
            clearable
          >
            <template #append>
              <el-select v-model="dataType" style="width: 100px">
                <el-option
                  v-for="item in dataTypeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </template>
          </zx-input>
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
const emit = defineEmits(["commit"]);
const treeNodeForm = ref();
const rules = {
  label: [{ required: true, message: "请输入选项名", trigger: "blur" }],
  value: [{ required: true, message: "请输入选项值", trigger: "blur" }],
};
const dataType = ref("string");
const dataTypeOptions = [
  { label: "字符串", value: "string" },
  { label: "数字", value: "number" },
];
let id = 100;
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
  title: "添加选项",
  closeOnClickModal: false,
  formRef: treeNodeForm,
  defaultData: () => ({ label: "", value: "" }),
  onConfirm(data) {
    emit("commit", {
      ...data,
      value:
        dataType.value === "number"
          ? Number.parseFloat(data.value)
          : data.value,
      id: id++,
    });
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
