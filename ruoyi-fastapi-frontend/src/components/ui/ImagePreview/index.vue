<template>
  <el-image
    v-if="realSrc"
    :src="realSrc"
    fit="cover"
    :style="`width:${realWidth};height:${realHeight};`"
    :preview-src-list="realSrcList"
    preview-teleported
    @error="onError"
  >
    <template #error>
      <div class="image-slot">
        <el-icon><picture-filled /></el-icon>
      </div>
    </template>
  </el-image>
</template>

<script setup>
import { computed, ref } from 'vue';
import { assetContentUrl, assetIdOfContentUrl } from '@/api/fileAssets';
import { recoverAsset } from '@/utils/file-assets/image-recovery';

const props = defineProps({
  /** 资产描述（含 contentUrl）、资产ID或稳定内容地址，单个或数组 */
  src: {
    type: [String, Object, Array],
    default: '',
  },
  width: {
    type: [Number, String],
    default: '',
  },
  height: {
    type: [Number, String],
    default: '',
  },
});

const toUrl = (item) => {
  if (!item) return '';
  if (typeof item === 'object')
    return item.contentUrl || (item.assetId ? assetContentUrl(item.assetId) : '');
  return item.startsWith('/file-assets/') ? item : assetContentUrl(item);
};

const reloadKey = ref(0);
const urls = computed(() =>
  (Array.isArray(props.src) ? props.src : [props.src]).map(toUrl).filter(Boolean)
);
// The same URL with a changed fragment forces el-image to reload after a session refresh.
const realSrc = computed(() =>
  urls.value[0] ? `${urls.value[0]}${reloadKey.value ? `#r${reloadKey.value}` : ''}` : undefined
);
const realSrcList = computed(() => (urls.value.length ? urls.value : undefined));
let retried = false;

async function onError() {
  const first = props.src && (Array.isArray(props.src) ? props.src[0] : props.src);
  const assetId = typeof first === 'object' ? first?.assetId : assetIdOfContentUrl(urls.value[0]);
  if (retried || !assetId) return;
  retried = true;
  if (await recoverAsset(assetId)) reloadKey.value += 1;
}

const realWidth = computed(() =>
  typeof props.width == 'string' ? props.width : `${props.width}px`
);

const realHeight = computed(() =>
  typeof props.height == 'string' ? props.height : `${props.height}px`
);
</script>

<style scoped>
.el-image {
  border-radius: 5px;
  background-color: var(--zx-semantic-surface-field-fill);
  box-shadow: var(--zx-semantic-surface-field-inner);
}

.el-image :deep(.el-image__inner) {
  transition: all 0.3s;
  cursor: pointer;
}

.el-image :deep(.el-image__inner:hover) {
  transform: scale(1.2);
}

.el-image :deep(.image-slot) {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: var(--zx-semantic-surface-field-on-text-secondary);
  font-size: 30px;
}
</style>
