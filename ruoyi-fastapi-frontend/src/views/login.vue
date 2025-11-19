<template>
  <div class="login-container">
    <el-scrollbar class="h-full">
      <div class="relative flex mx-auto min-h-screen">
        <!-- 左侧展示区域 -->
        <div
          class="login-left flex-1 bg-gradient-to-br from-slate-800 to-slate-900 relative p-8 hidden lg:flex"
        >
          <div class="flex justify-center items-center h-full absolute inset-0 p-8">
            <div class="text-center">
              <div class="login-illustration">
                <img src="@/assets/images/login-box-bg.svg" alt="登录插图" class="w-80 mx-auto" />
              </div>
              <div class="text-3xl text-white font-bold mb-4">{{ `欢迎使用${displayTitle}` }}</div>
            </div>
          </div>
        </div>

        <!-- 右侧登录表单区域 -->
        <div class="flex-1 p-6 lg:p-10 bg-gray-50 relative flex items-center">
          <div class="w-full max-w-md mx-auto">
            <div class="bg-white rounded-lg shadow p-6">
              <div class="text-center mb-6">
                <h2 class="text-xl font-bold text-gray-800 mb-1">用户登录</h2>
                <p class="text-gray-500">请输入您的账号和密码</p>
              </div>

              <el-form ref="loginRef" :model="loginForm" :rules="loginRules" class="login-form">
                <el-form-item prop="username">
                  <el-input
                    v-model="loginForm.username"
                    type="text"
                    auto-complete="off"
                    placeholder="账号"
                  >
                    <!-- <template #prefix
                      ><svg-icon icon-class="user" class="el-input__icon input-icon"
                    /></template> -->
                  </el-input>
                </el-form-item>

                <el-form-item prop="password">
                  <el-input
                    v-model="loginForm.password"
                    type="password"
                    auto-complete="off"
                    placeholder="密码"
                    @keyup.enter="handleLogin"
                  >
                    <!-- <template #prefix
                      ><svg-icon icon-class="password" class="el-input__icon input-icon"
                    /></template> -->
                  </el-input>
                </el-form-item>

                <el-form-item prop="code" v-if="captchaEnabled">
                  <div class="flex gap-3">
                    <el-input
                      v-model="loginForm.code"
                      auto-complete="off"
                      placeholder="验证码"
                      @keyup.enter="handleLogin"
                    >
                      <!-- <template #prefix
                        ><svg-icon icon-class="validCode" class="el-input__icon input-icon"
                      /></template> -->
                    </el-input>
                    <div class="cursor-pointer">
                      <img :src="codeUrl" @click="getCode" />
                    </div>
                  </div>
                </el-form-item>

                <div class="flex justify-between items-center mb-4">
                  <el-checkbox v-model="loginForm.rememberMe" class="remember-me">
                    记住密码
                  </el-checkbox>
                </div>

                <el-form-item>
                  <el-button
                    :loading="loading"
                    type="primary"
                    class="login-button w-full"
                    @click.prevent="handleLogin"
                  >
                    <span v-if="!loading">登 录</span>
                    <span v-else>登 录 中...</span>
                  </el-button>
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
import { encrypt, decrypt } from '@/utils/jsencrypt';
import useUserStore from '@/store/modules/user';

const title = import.meta.env.VITE_APP_TITLE;
const displayTitle = computed(() => {
  const t = title ?? '';
  return t.includes('系统') ? t : `${t}系统`;
});
const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const { proxy } = getCurrentInstance();

const loginForm = ref({
  username: 'admin',
  password: 'admin123',
  rememberMe: false,
  code: '',
  uuid: '',
});

const loginRules = {
  username: [{ required: true, trigger: 'blur', message: '请输入您的账号' }],
  password: [{ required: true, trigger: 'blur', message: '请输入您的密码' }],
  code: [{ required: true, trigger: 'change', message: '请输入验证码' }],
};

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
      // 勾选了需要记住密码设置在 cookie 中设置记住用户名和密码
      if (loginForm.value.rememberMe) {
        Cookies.set('username', loginForm.value.username, { expires: 30 });
        Cookies.set('password', encrypt(loginForm.value.password), { expires: 30 });
        Cookies.set('rememberMe', loginForm.value.rememberMe, { expires: 30 });
      } else {
        // 否则移除
        Cookies.remove('username');
        Cookies.remove('password');
        Cookies.remove('rememberMe');
      }
      // 调用action的登录方法
      userStore
        .login(loginForm.value)
        .then(() => {
          const query = route.query;
          const otherQueryParams = Object.keys(query).reduce((acc, cur) => {
            if (cur !== 'redirect') {
              acc[cur] = query[cur];
            }
            return acc;
          }, {});
          router.push({ path: redirect.value || '/', query: otherQueryParams });
        })
        .catch(() => {
          loading.value = false;
          // 重新获取验证码
          if (captchaEnabled.value) {
            getCode();
          }
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
  const password = Cookies.get('password');
  const rememberMe = Cookies.get('rememberMe');
  loginForm.value = {
    username: username === undefined ? loginForm.value.username : username,
    password: password === undefined ? loginForm.value.password : decrypt(password),
    rememberMe: rememberMe === undefined ? false : Boolean(rememberMe),
  };
}

getCode();
getCookie();
</script>

<style scoped></style>
