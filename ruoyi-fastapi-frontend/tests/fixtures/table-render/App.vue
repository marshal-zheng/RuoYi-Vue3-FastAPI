<script setup lang="ts">
import { ref } from 'vue';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import { zxThemeConfig, setZxThemePreference } from '@/theme/zx-theme-config';
import SelectUser from '@/views/system/role/selectUser.vue';
import ConfigList from '@/views/system/config/components/ConfigList.vue';
import MenuList from '@/views/system/menu/components/MenuList.vue';
import RolePage from '@/views/system/role/index.vue';
import useUserStore from '@/store/modules/user';
import { useRoute } from 'vue-router';
import DeptList from '@/views/system/dept/components/DeptList.vue';
import { setQuerySession } from '@/queries/context';
import { probe } from './transport';
import PerformanceWorkbench from '@table-render-benchmark.vue';
const benchmark = new URLSearchParams(location.search).has('benchmark');
const selector = ref<InstanceType<typeof SelectUser>>();
const active = ref('config');
const route = useRoute();
const readonly = ref(false);
const store = useUserStore();
function togglePermissions() {
  readonly.value = !readonly.value;
  store.permissions = readonly.value ? [] : ['*:*:*'];
  setQuerySession(user, ['admin'], store.permissions);
}
let user = 1;
function switchDomain() {
  user = user === 1 ? 2 : 1;
  setQuerySession(user, ['admin'], store.permissions);
}
</script>
<template>
  <ZxConfigProvider :theme="zxThemeConfig" :locale="zhCn">
    <main class="pilot">
      <PerformanceWorkbench v-if="benchmark" />
      <template v-else>
        <h1>TableRender 真实业务离线试点</h1>
        <p>
          挂载参数配置、角色管理、菜单管理、部门管理和角色选择器原组件，保留 Vue Query
          和业务命令。网络请求终止于本页内存适配器，不连接后端。读取
          {{ probe.reads }} 次，写入 {{ probe.writes }} 次。
        </p>
        <div class="pilot-controls">
          <ZxButton @click="selector?.show()">选择角色用户</ZxButton
          ><ZxButton @click="switchDomain">切换用户域</ZxButton
          ><ZxButton @click="probe.failNext = true">令下一次读取失败</ZxButton>
          <ZxButton @click="togglePermissions">{{
            readonly ? '恢复权限' : '撤销操作权限'
          }}</ZxButton>
        </div>
        <div class="pilot-controls">
          <ZxButton @click="setZxThemePreference({ mode: 'light' })">Light</ZxButton
          ><ZxButton @click="setZxThemePreference({ mode: 'dark' })">Dark</ZxButton>
        </div>
        <nav class="pilot-controls" aria-label="业务页面">
          <ZxButton
            v-for="[key, name] in [
              ['config', '参数配置'],
              ['role', '角色管理'],
              ['menu', '菜单管理'],
              ['dept', '部门管理'],
            ]"
            :key="key"
            :aria-pressed="active === key"
            @click="active = key"
            >{{ name }}</ZxButton
          >
        </nav>
        <p v-if="route.path !== '/'" role="status">业务导航：{{ route.path }}</p>
        <div style="height: 600px; min-width: 0">
          <ConfigList v-if="active === 'config'" />
          <RolePage v-else-if="active === 'role'" />
          <MenuList v-else-if="active === 'menu'" />
          <DeptList v-else />
        </div>
        <details>
          <summary>内存请求记录</summary>
          <pre>{{ JSON.stringify(probe.requests, null, 2) }}</pre>
        </details>
        <SelectUser ref="selector" :role-id="20" />
      </template>
    </main>
  </ZxConfigProvider>
</template>
<style>
body {
  margin: 0;
}
.pilot {
  box-sizing: border-box;
  min-height: 100vh;
  padding: 24px;
  color: var(--el-text-color-primary);
  background: var(--el-bg-color-page);
}
.pilot-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.pilot pre {
  max-width: 100%;
  overflow: auto;
}
</style>
