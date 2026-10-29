<template>
  <div class="user-info-head" @click="editCropper()">
    <img :src="options.img" title="点击上传头像" class="user-info-avatar" @error="onAvatarError" />
    <ZxDialog
      dialog-size="lg"
      :draggable="false"
      :show-full-screen="false"
      :destroy-on-close="false"
      :close-on-click-modal="true"
      :footer="false"
      :title="title"
      v-model="open"
      @opened="modalOpened"
      @close="closeDialog"
    >
      <el-row>
        <el-col :xs="24" :md="12" :style="{ height: '350px' }">
          <vue-cropper
            ref="cropper"
            :img="options.img"
            :info="true"
            :autoCrop="options.autoCrop"
            :autoCropWidth="options.autoCropWidth"
            :autoCropHeight="options.autoCropHeight"
            :fixedBox="options.fixedBox"
            :outputType="options.outputType"
            @realTime="realTime"
            v-if="visible"
          />
        </el-col>
        <el-col :xs="24" :md="12" :style="{ height: '350px' }">
          <div class="avatar-upload-preview">
            <img :src="options.previews.url" :style="options.previews.img" />
          </div>
        </el-col>
      </el-row>
      <br />
      <el-row>
        <el-col :lg="2" :md="2">
          <el-upload
            action="#"
            :http-request="requestUpload"
            :show-file-list="false"
            :before-upload="beforeUpload"
          >
            <el-button>
              选择
              <el-icon class="el-icon--right"><Upload /></el-icon>
            </el-button>
          </el-upload>
        </el-col>
        <el-col :lg="{ span: 1, offset: 2 }" :md="2">
          <el-button icon="Plus" @click="changeScale(1)"></el-button>
        </el-col>
        <el-col :lg="{ span: 1, offset: 1 }" :md="2">
          <el-button icon="Minus" @click="changeScale(-1)"></el-button>
        </el-col>
        <el-col :lg="{ span: 1, offset: 1 }" :md="2">
          <el-button icon="RefreshLeft" @click="rotateLeft()"></el-button>
        </el-col>
        <el-col :lg="{ span: 1, offset: 1 }" :md="2">
          <el-button icon="RefreshRight" @click="rotateRight()"></el-button>
        </el-col>
        <el-col :lg="{ span: 2, offset: 6 }" :md="2">
          <el-button type="primary" @click="uploadImg()" :loading="uploadImgPending"
            >提 交</el-button
          >
        </el-col>
      </el-row>
    </ZxDialog>
  </div>
</template>

<script setup>
import { useOperation } from '@/utils/operation';
import 'vue-cropper/dist/index.css';
import { ElMessage } from 'element-plus';
import { VueCropper } from 'vue-cropper';
import { captureUserCommand, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { retryAssetImage } from '@/utils/file-assets/image-recovery';
import useUserStore from '@/store/modules/user';

const userStore = useUserStore();
const { proxy } = getCurrentInstance();

const open = ref(false);
const visible = ref(false);
const title = ref('修改头像');
let editorScope;
let editorGeneration = 0;
watch(queryScope, closeDialog, { flush: 'sync' });

//图片裁剪数据
const options = reactive({
  img: userStore.avatar, // 裁剪图片的地址
  autoCrop: true, // 是否默认生成截图框
  autoCropWidth: 200, // 默认生成截图框宽度
  autoCropHeight: 200, // 默认生成截图框高度
  fixedBox: true, // 固定截图框大小 不允许改变
  outputType: 'png', // 默认生成截图为PNG格式（服务端再规范化为 ≤512 像素 PNG）
  previews: {}, //预览数据
});

/** 编辑头像 */
function editCropper() {
  editorScope = requireQueryScope();
  editorGeneration++;
  open.value = true;
}
/** 打开弹出层结束时的回调 */
function modalOpened() {
  visible.value = true;
}
/** 覆盖默认上传行为 */
function requestUpload() {}
/** 向左旋转 */
function rotateLeft() {
  proxy.$refs.cropper.rotateLeft();
}
/** 向右旋转 */
function rotateRight() {
  proxy.$refs.cropper.rotateRight();
}
/** 图片缩放 */
function changeScale(num) {
  num = num || 1;
  proxy.$refs.cropper.changeScale(num);
}
/** 上传预处理 */
function beforeUpload(file) {
  if (file.type.indexOf('image/') == -1) {
    ElMessage.error('文件格式错误，请上传图片类型,如：JPG，PNG后缀的文件。');
  } else {
    const scope = editorScope;
    const generation = editorGeneration;
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      if (scope !== queryScope.value || generation !== editorGeneration) return;
      options.img = reader.result;
    };
  }
}
/** 上传图片 */
const { run: uploadImg, pending: uploadImgPending } = useOperation(async () => {
  const scope = editorScope;
  const generation = editorGeneration;
  if (!scope || scope !== queryScope.value) return;
  const data = await new Promise((resolve) => proxy.$refs.cropper.getCropBlob(resolve));
  if (scope !== queryScope.value || generation !== editorGeneration) return;
  let formData = new FormData();
  // The cropper always produces PNG; the name must match the content the server decodes.
  formData.append('avatarfile', data, 'avatar.png');
  try {
    const response = await userCommands.uploadAvatar(captureUserCommand(formData, scope));
    if (scope !== queryScope.value) return;
    // The replacement is committed and the old asset is released: the store must follow it even when
    // the dialog was closed or reopened while the request was in flight.
    userStore.avatar = response.avatarUrl;
    if (generation === editorGeneration) {
      open.value = false;
      visible.value = false;
      options.img = response.avatarUrl;
    } else if (!open.value) {
      options.img = response.avatarUrl;
    }
  } catch (error) {
    // A lost response may hide a committed replacement: re-read the profile to know the truth.
    if (scope === queryScope.value && !isDefinitiveRejection(error)) {
      await userStore.getInfo().catch(() => undefined);
      if (scope === queryScope.value) options.img = userStore.avatar;
    }
    throw error;
  }
});
/** 4xx answers prove the replacement did not commit; anything else may have. */
function isDefinitiveRejection(error) {
  const status = error?.status ?? error?.response?.status;
  return typeof status === 'number' && status >= 400 && status < 500;
}
let avatarRetried = false;
/** The stable avatar URL is authorized per request: recover once after a session refresh. */
async function onAvatarError(event) {
  if (avatarRetried || !String(options.img || '').startsWith('/file-assets/')) return;
  avatarRetried = true;
  await retryAssetImage(event.target);
}
/** 实时预览 */
function realTime(data) {
  options.previews = data;
}
/** 关闭窗口 */
function closeDialog() {
  editorGeneration++;
  open.value = false;
  visible.value = false;
  options.img = userStore.avatar;
}
</script>

<style scoped>
.user-info-head {
  position: relative;
  display: inline-block;
  width: 120px;
  height: 120px;
}

.user-info-avatar {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.user-info-head:hover:after {
  content: '+';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  color: #eee;
  background: rgba(0, 0, 0, 0.5);
  font-size: 24px;
  font-style: normal;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  cursor: pointer;
  line-height: 110px;
  border-radius: 50%;
}
</style>
