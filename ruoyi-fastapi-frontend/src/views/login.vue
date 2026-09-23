<template>
  <div class="login-container">
    <el-scrollbar class="h-full">
      <div class="relative flex mx-auto min-h-screen">
        <!-- 左侧展示区域 -->
        <div class="login-left flex-1 relative p-8 hidden lg:flex" data-zx-surface="brand">
          <div class="flex justify-center items-center h-full absolute inset-0 p-8">
            <div class="text-center">
              <div class="login-illustration">
                <img
                  class="login-illustration-svg w-80 mx-auto"
                  :src="loginIllustrationSrc"
                  aria-label="登录插图"
                  alt="登录插图"
                />
              </div>
              <div class="text-3xl font-bold mb-4">
                {{ `欢迎使用${displayTitle}` }}
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单区域 -->
        <div class="flex-1 p-6 lg:p-10 relative flex items-center" data-zx-surface="canvas">
          <div class="w-full max-w-md mx-auto">
            <div class="p-8" data-zx-surface="card">
              <Logo :collapse="false" variant="login" class="mb-6" />
              <div class="flex justify-end mb-4">
                <ZxThemePresetSwitch />
              </div>
              <el-form ref="loginRef" :model="loginForm" :rules="loginRules" class="login-form">
                <el-form-item prop="username">
                  <zx-input
                    v-model="loginForm.username"
                    data-testid="demo-login-username"
                    type="text"
                    auto-complete="off"
                    aria-label="账号"
                    placeholder="账号"
                    size="large"
                  >
                    <template #prefix>
                      <ZxIcon
                        icon="User"
                        :size="16"
                        color="var(--el-input-icon-color)"
                        class-name="login-input-icon"
                      />
                    </template>
                  </zx-input>
                </el-form-item>

                <el-form-item prop="password">
                  <zx-input
                    v-model="loginForm.password"
                    data-testid="demo-login-password"
                    :type="showPassword ? 'text' : 'password'"
                    auto-complete="off"
                    aria-label="密码"
                    placeholder="密码"
                    size="large"
                    @keyup.enter="handleLogin"
                  >
                    <template #prefix>
                      <ZxIcon
                        icon="Lock"
                        :size="16"
                        color="var(--el-input-icon-color)"
                        class-name="login-input-icon"
                      />
                    </template>
                    <template #suffix>
                      <ZxIcon
                        :icon="showPassword ? 'View' : 'Hide'"
                        :size="16"
                        color="var(--el-input-icon-color)"
                        class-name="login-input-icon login-input-icon--action"
                        @click="showPassword = !showPassword"
                      />
                    </template>
                  </zx-input>
                </el-form-item>

                <el-form-item prop="code" v-if="captchaEnabled">
                  <div class="flex gap-3">
                    <zx-input
                      v-model="loginForm.code"
                      data-testid="demo-login-captcha"
                      auto-complete="off"
                      aria-label="验证码"
                      placeholder="验证码"
                      size="large"
                      class="flex-1"
                      @keyup.enter="handleLogin"
                    >
                      <template #prefix>
                        <ZxIcon
                          icon="CircleCheck"
                          :size="16"
                          color="var(--el-input-icon-color)"
                          class-name="login-input-icon"
                        />
                      </template>
                    </zx-input>
                    <div
                      class="login-captcha relative cursor-pointer w-[120px] h-[40px] flex items-center justify-center transition-all duration-200 select-none overflow-hidden group active:scale-[0.98]"
                      data-zx-surface="field"
                      @click="getCode"
                      title="点击刷新验证码"
                    >
                      <img :src="codeUrl" class="h-full w-full object-cover" alt="验证码" />
                    </div>
                  </div>
                </el-form-item>

                <div class="flex justify-between items-center mb-4">
                  <el-checkbox v-model="loginForm.rememberMe"> 记住账号 </el-checkbox>
                </div>

                <el-form-item>
                  <ZxButton
                    :loading="loading"
                    data-testid="demo-login-submit"
                    type="primary"
                    size="large"
                    class="w-full !h-11 font-bold tracking-[0.2em] !text-lg"
                    @click="handleLogin"
                  >
                    {{ loading ? '登录中...' : '登录' }}
                  </ZxButton>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { getCodeImg } from '@/api/login';
import Cookies from 'js-cookie';
import useUserStore from '@/store/modules/user';
import Logo from '@/layout/components/Sidebar/Logo.vue';
import loginIllustration from '@/assets/images/login-box-bg.svg?raw';
import ZxThemePresetSwitch from '@/theme/ZxThemePresetSwitch.vue';

const title = import.meta.env.VITE_APP_TITLE;
const displayTitle = computed(() => {
  const t = title ?? '';
  return t.includes('系统') ? t : `${t}系统`;
});
const loginIllustrationSrc = computed(
  () => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(loginIllustration)}`
);
const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const { proxy } = getCurrentInstance();

const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false,
  code: '',
  uuid: '',
});

const showPassword = ref(false);

const loginRules = computed(() => ({
  username: [{ required: true, trigger: 'blur', message: '请输入您的账号' }],
  password: [{ required: true, trigger: 'blur', message: '请输入您的密码' }],
  ...(captchaEnabled.value
    ? { code: [{ required: true, trigger: 'change', message: '请输入验证码' }] }
    : {}),
}));

const codeUrl = ref('');
const loading = ref(false);
// 验证码开关
const captchaEnabled = ref(true);
// 注册开关
const register = ref(false);
const redirect = ref(undefined);

watch(
  route,
  (newRoute) => {
    redirect.value = newRoute.query && newRoute.query.redirect;
  },
  { immediate: true }
);

function handleLogin() {
  proxy.$refs.loginRef.validate((valid) => {
    if (valid) {
      loading.value = true;
      // 仅记住账号，不持久化密码
      if (loginForm.value.rememberMe) {
        Cookies.set('username', loginForm.value.username, { expires: 30 });
        Cookies.set('rememberMe', loginForm.value.rememberMe, { expires: 30 });
      } else {
        // 否则移除
        Cookies.remove('username');
        Cookies.remove('rememberMe');
      }
      // 调用action的登录方法
      userStore
        .login(loginForm.value)
        .then(async () => {
          const query = route.query;
          const otherQueryParams = Object.keys(query).reduce((acc, cur) => {
            if (cur !== 'redirect') {
              acc[cur] = query[cur];
            }
            return acc;
          }, {});
          try {
            await router.push({
              path: redirect.value || '/',
              query: otherQueryParams,
            });
          } catch {
            loading.value = false;
          }
        })
        .catch(() => {
          // 重新获取验证码
          if (captchaEnabled.value) {
            getCode();
          }
        })
        .finally(() => {
          loading.value = false;
        });
    }
  });
}

function getCode() {
  getCodeImg().then((res) => {
    captchaEnabled.value = res.captchaEnabled === undefined ? true : res.captchaEnabled;
    if (captchaEnabled.value) {
      const imgData = res.img || '';
      codeUrl.value = imgData.startsWith('data:') ? imgData : `data:image/gif;base64,${imgData}`;
      loginForm.value.uuid = res.uuid;
    }
  });
}

function getCookie() {
  const username = Cookies.get('username');
  const rememberMe = Cookies.get('rememberMe');
  loginForm.value = {
    ...loginForm.value,
    username: username === undefined ? loginForm.value.username : username,
    rememberMe: rememberMe === undefined ? false : rememberMe === 'true',
  };
}

getCode();
getCookie();
</script>

<style scoped>
.login-left {
  border-radius: 0;
}

.login-captcha:hover {
  border-color: var(--zx-semantic-border-strong);
}

/* Element Plus 深度样式覆盖 - 只处理无法用 Tailwind 实现的部分 */
.login-form :deep(.el-form-item__content) {
  display: block;
}

.login-form :deep(.el-input) {
  height: 40px;
  line-height: 40px;
}

.login-form :deep(.el-input__wrapper) {
  height: 40px;
  min-height: 40px;
  align-items: center;
}

.login-form :deep(.el-input__inner) {
  height: 38px;
  line-height: 38px;
}

.login-form :deep(.el-input__prefix),
.login-form :deep(.el-input__suffix) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-form :deep(.el-input__prefix-inner),
.login-form :deep(.el-input__suffix-inner) {
  display: flex;
  align-items: center;
}

.login-form :deep(.login-input-icon) {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--el-input-icon-color);
  cursor: default;
}

.login-form :deep(.login-input-icon--action) {
  cursor: pointer;
}

.login-form :deep(.el-input.is-active .el-input__wrapper),
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

.login-illustration-svg :deep(svg) {
  display: block;
  width: 100%;
  height: auto;
}
</style>
