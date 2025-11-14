<template>
  <ContentDetailWrap 
    :title="`项目详情 - ${projectInfo.projectName || '未知项目'}`"
    :data="compactData"
    headerType="normal"
    :showDivider="false"
  >
    <div class="project-info-page">
      <ZxTabs v-model="activeTab" :items="tabItems" :lazy="true" />
    </div>
  </ContentDetailWrap>
</template>

<script setup name="ProjectInfo">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ZxTabs } from '@zxio/zxui'
import { getProject } from '@/api/project'
import ContentDetailWrap from '@/components/ContentDetailWrap/index'
import { VersionList } from './components'

const route = useRoute()

const activeTab = ref('version')

const projectInfo = ref({
  projectId: null,
  projectName: '',
  description: ''
})

/** 加载项目信息 */
async function loadProjectInfo() {
  const projectId = route.params.projectId
  if (!projectId || projectId === 'new') {
    projectInfo.value = {
      projectId: null,
      projectName: '新项目',
      description: ''
    }
    return
  }

  try {
    const response = await getProject(projectId)
    if (response.data) {
      projectInfo.value = response.data
    }
  } catch (error) {
    console.warn('获取项目信息失败:', error)
    projectInfo.value = {
      projectId: projectId,
      projectName: '未知项目',
      description: ''
    }
  }
}

/** Tab 配置 */
const tabItems = computed(() => [
  {
    key: 'version',
    label: '项目版本',
    component: VersionList,
    props: {
      projectId: projectInfo.value.projectId
    }
  }
])

onMounted(() => {
  loadProjectInfo()
})

/** 模拟项目详情数据 */
const compactData = computed(() => [
  {
    label: '项目ID',
    value: projectInfo.value.projectId || 'DEV-LIB-2024-001',
    prop: 'projectId'
  },
  {
    label: '项目名称',
    value: projectInfo.value.projectName || '无人机设备库管理系统',
    prop: 'projectName'
  },
  {
    label: '项目编码',
    value: 'UAV-DEVICE-LIB-V2.0',
    prop: 'projectCode'
  },
  {
    label: '项目描述',
    value: projectInfo.value.description || '基于Vue3和Spring Boot的无人机设备库管理系统，涵盖核心控制模块（飞控主板、IMU惯导、电调ESC）、定位导航模块（GPS模块、磁罗盘、气压计）、遥控通信模块等设备的统一管理、配置和监控平台',
    prop: 'description',
    span: 3
  }
])
</script>

<style lang="scss" scoped>
.project-info-page {
  :deep(.zx-tabs) {
    height: 100%;
  }
}
</style>

