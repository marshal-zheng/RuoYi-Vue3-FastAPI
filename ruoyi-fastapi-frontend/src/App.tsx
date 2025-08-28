import { defineComponent, onMounted, nextTick } from 'vue'
import { RouterView } from 'vue-router'
import useSettingsStore from '@/store/modules/settings'
import { handleThemeStyle } from '@/utils/theme'

export default defineComponent({
  name: 'App',
  setup() {
    onMounted(() => {
      nextTick(() => {
        // 初始化主题样式
        handleThemeStyle(useSettingsStore().theme)
      })
    })

    return () => (
      <RouterView />
    )
  }
})