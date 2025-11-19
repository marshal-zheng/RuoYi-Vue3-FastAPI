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
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ZxTabs } from '@zxio/zxui';
import { getProject } from '@/api/project/project';
import ContentDetailWrap from '@/components/ContentDetailWrap/index';
import { VersionList } from './components';

const route = useRoute();

const activeTab = ref('version');

const projectInfo = ref({
  projectId: null,
  projectName: '',
  projectCode: '',
  projectDesc: '',
});

/** 加载项目信息 */
async function loadProjectInfo() {
  const projectId = route.params.projectId;
  if (!projectId || projectId === 'new') {
    projectInfo.value = {
      projectId: null,
      projectName: '新项目',
      description: '',
    };
    return;
  }

  try {
    const response = await getProject(projectId);
    if (response.data) {
      projectInfo.value = response.data;
    }
  } catch (error) {
    console.warn('获取项目信息失败:', error);
    projectInfo.value = {
      projectId: projectId,
      projectName: '未知项目',
      description: '',
    };
  }
}

/** Tab 配置 */
const tabItems = computed(() => [
  {
    key: 'version',
    label: '项目版本',
    component: VersionList,
    props: {
      projectId: projectInfo.value.projectId,
    },
  },
]);

onMounted(() => {
  loadProjectInfo();
});

/** 项目详情数据 */
const compactData = computed(() => [
  {
    label: '项目ID',
    value: projectInfo.value.projectId || '-',
    prop: 'projectId',
  },
  {
    label: '项目名称',
    value: projectInfo.value.projectName || '-',
    prop: 'projectName',
  },
  {
    label: '项目编码',
    value: projectInfo.value.projectCode || '-',
    prop: 'projectCode',
  },
  {
    label: '项目描述',
    value: projectInfo.value.projectDesc || '-',
    prop: 'projectDesc',
    span: 3,
  },
]);
</script>

<style lang="less" scoped>
.project-info-page {
  :deep(.zx-tabs) {
    height: 100%;
  }
}
</style>
