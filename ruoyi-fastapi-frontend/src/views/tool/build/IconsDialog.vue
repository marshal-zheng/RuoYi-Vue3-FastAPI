<template>
  <div class="icon-dialog">
    <ZxDialog
      v-model="value"
      title="选择图标"
      dialog-size="xl"
      :footer="false"
      :close-on-click-modal="false"
      @open="onOpen"
      @close="onClose"
    >
      <template #headerLeft>
        <zx-input
          v-model="key"
          size="small"
          :style="{ width: '260px' }"
          placeholder="请输入图标名称"
          prefix-icon="Search"
          clearable
        />
      </template>
      <ul class="icon-ul">
        <li
          v-for="icon in iconList"
          :key="icon"
          :class="active === icon ? 'active-item' : ''"
          @click="onSelect(icon)"
        >
          <div>
            <el-icon :size="30">
              <component :is="icon" />
            </el-icon>
            <div>{{ icon }}</div>
          </div>
        </li>
      </ul>
    </ZxDialog>
  </div>
</template>
<script setup>
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import { watch, ref } from "vue";
import { ZxDialog } from "@zxio/zxui";

const iconList = ref([]);
const originList = [];
const key = ref("");
const active = ref("");
const emit = defineEmits(["select"]);
const value = defineModel();
for (const [key] of Object.entries(ElementPlusIconsVue)) {
  iconList.value.push(key);
  originList.push(key);
}

function onOpen() {}
function onClose() {}
function onSelect(icon) {
  active.value = icon;
  emit("select", icon);
  value.value = false;
}

watch(key, (val) => {
  if (val) {
    iconList.value = originList.filter((name) => name.indexOf(val) > -1);
  } else {
    iconList.value = originList;
  }
});
</script>
<style scoped>
.icon-ul {
  margin: 0;
  padding: 0;
  font-size: 0;
}

.icon-ul li {
  list-style-type: none;
  text-align: center;
  font-size: 14px;
  display: inline-flex;
  width: 16.66%;
  box-sizing: border-box;
  height: 108px;
  padding: 6px 6px 6px 6px;
  cursor: pointer;
  overflow: hidden;
  align-items: center;
  justify-content: center;
}

.icon-ul li:hover {
  background: var(--zx-semantic-surface-sunken);
}

.icon-ul li.active-item {
  background: var(--zx-semantic-surface-elevated);
  color: var(--zx-semantic-text-primary);
}

.icon-ul li i {
  font-size: 30px;
  line-height: 50px;
  margin-bottom: 10px;
}
</style>
