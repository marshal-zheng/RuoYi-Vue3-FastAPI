<template>
  <ZxDialog
    v-bind="dialogProps"
    v-on="dialogEvents"
    data-testid="project-form-dialog"
  >
    <div class="py-4">
      <el-form
        ref="formRef"
        :model="state.data"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="工程名称" prop="projectName">
          <el-input
            v-model="state.data.projectName"
            data-testid="project-form-name"
            aria-label="工程名称"
            placeholder="请输入工程名称"
          />
        </el-form-item>
        <el-form-item label="工程描述" prop="projectDesc">
          <el-input
            v-model="state.data.projectDesc"
            data-testid="project-form-desc"
            aria-label="工程描述"
            type="textarea"
            :rows="4"
            placeholder="请输入工程描述"
          />
        </el-form-item>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup>
import { ref, computed, getCurrentInstance } from "vue";
import { useDialog } from "@zxio/zxui";
import { getProject, addProject, updateProject } from "@/api/project/project";

const emit = defineEmits(["success"]);

const formRef = ref();

const formRules = computed(() => ({
  projectName: [
    { required: true, message: "工程名称不能为空", trigger: "blur" },
  ],
}));

const { state, dialogProps, dialogEvents, open, close, setLoading } = useDialog(
  {
    title: (data) => (data?.projectId ? "编辑工程" : "添加工程"),
    width: "600px",
    okText: computed(() => (state.data.projectId ? "保存" : "下一步")),
    formRef,
    preValidate: true,
    autoScrollToError: true,
    autoResetForm: true,
    defaultData: () => ({
      projectId: null,
      projectName: "",
      projectDesc: "",
    }),
    onConfirm: async (data) => {
      if (data.projectId) {
        const res = await updateProject(data);
        emit("success", { mode: "edit", data: res });
        return res;
      }
      const res = await addProject(data);
      // http 客户端已解包 payload.data，res 直接是项目数据
      const newId = res?.projectId || res?.id || null;
      emit("success", { mode: "create", projectId: newId, data: res });
      return res;
    },
  },
);

async function openDialog(payload) {
  if (
    payload &&
    (payload.projectId ||
      typeof payload === "number" ||
      typeof payload === "string")
  ) {
    const id = payload.projectId || payload;
    setLoading(true);
    try {
      const resp = await getProject(id);
      const detail = resp || {};
      open({
        projectId: detail.projectId,
        projectName: detail.projectName,
        projectDesc: detail.projectDesc,
      });
    } finally {
      setLoading(false);
    }
  } else {
    open();
  }
}

defineExpose({ open: openDialog, close });
</script>

<style scoped></style>
