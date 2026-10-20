<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    @close="handleClose"
  >
    <ZxTabs v-model="activeTab" :items="tabItems" class="port-config-tabs" lazy>
      <template #params>
        <ParamsConfigTab
          ref="paramsConfigTabRef"
          :port-info="portInfo"
          v-model="paramsForm"
        />
      </template>

      <template #message>
        <MessageConfigTab
          ref="messageConfigTabRef"
          :port-info="portInfo"
          :device-mode="true"
        />
      </template>
    </ZxTabs>
  </ZxDrawer>
</template>

<script setup name="PortConfigDrawer">
import { submitCurrentPortTab } from "./port-params-policy";
import { ref, reactive, computed, watch } from "vue";
import { useDrawer } from "@zxio/zxui/hooks";
import ParamsConfigTab from "./ParamsConfigTab.vue";
import MessageConfigTab from "./MessageConfigTab.vue";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "端口配置" },
  portInfo: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(["update:modelValue", "close", "submit"]);

const drawer = useDrawer({
  divider: true,
  title: () => title.value,
  size: "75%",
  placement: "right",
  okText: "确定",
  preValidate: false,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({}),
  onConfirm: async () => {
    const payload = await submitCurrentPortTab(
      props.portInfo,
      activeTab.value,
      {
        params: paramsConfigTabRef.value,
        message: messageConfigTabRef.value,
      },
    );
    if (payload === false) return false;
    if (payload) emit("submit", payload);
    handleClose();
    return true;
  },
});

const title = computed(() => props.title);

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      drawer.open();
    } else {
      drawer.close();
      handleClose();
    }
  },
);

// 当前激活的 Tab
const activeTab = ref("params");

// ZxTabs 配置
const tabItems = [
  { key: "params", label: "参数配置" },
  { key: "message", label: "报文配置" },
];

// 表单引用
const paramsConfigTabRef = ref();
const messageConfigTabRef = ref();

// 参数配置表单数据（用于与ParamsConfigTab组件通信）
const paramsForm = reactive({});

function handleClose() {
  activeTab.value = "params";
  paramsConfigTabRef.value?.clearValidate();
  messageConfigTabRef.value?.clearValidate();
  emit("close");
  emit("update:modelValue", false);
  drawer.close();
}

defineExpose({
  open: () => drawer.open(),
  close: () => handleClose(),
});
</script>

<style lang="less" scoped>
:deep(.zx-tabs__content) {
  padding: 30px 0;
}
</style>
