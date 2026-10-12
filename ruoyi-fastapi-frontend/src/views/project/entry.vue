<template>
  <div class="project-entry">
    <div v-if="!errorTitle" class="project-entry__loading" data-zx-surface="card">
      <el-icon class="project-entry__icon is-loading"><Loading /></el-icon>
      <div class="project-entry__text">
        <h3>{{ loadingTitle }}</h3>
        <p>{{ loadingDescription }}</p>
      </div>
    </div>

    <el-result v-else icon="warning" :title="errorTitle" :sub-title="errorDescription">
      <template #extra>
        <el-button type="primary" @click="goProjectList">打开工程列表</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';

import { listProject } from '@/api/project/project';
import { listProjectVersion } from '@/api/project/version';

type ProjectEntryTarget = 'detail' | 'topology' | 'simulation';

interface ProjectSummary {
  projectId: number;
  projectName?: string;
}

interface ProjectVersionSummary {
  versionId: number;
  versionName?: string;
}

interface PageResult<T> {
  items?: T[];
}

const route = useRoute();
const router = useRouter();
const errorTitle = ref('');
const errorDescription = ref('');

const entryTarget = computed<ProjectEntryTarget>(() => {
  const rawTarget = route.meta.entryTarget;
  return rawTarget === 'topology' || rawTarget === 'simulation' ? rawTarget : 'detail';
});

const loadingTitle = computed(() => {
  if (entryTarget.value === 'detail') {
    return '正在打开工程详情';
  }
  if (entryTarget.value === 'topology') {
    return '正在打开拓扑设计';
  }
  return '正在打开版本仿真';
});

const loadingDescription = computed(() => {
  if (entryTarget.value === 'detail') {
    return '正在定位当前场景可用的工程入口。';
  }
  return '正在定位当前场景可用的工程和版本入口。';
});

function normalizeId(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function getFirstRow<T>(page: PageResult<T> | undefined): T | undefined {
  return Array.isArray(page?.items) ? page.items[0] : undefined;
}

async function resolveFirstProject(): Promise<ProjectSummary | null> {
  const page = (await listProject({ page: 1, pageSize: 1 })) as PageResult<ProjectSummary>;
  const project = getFirstRow(page);
  const projectId = normalizeId((project as Record<string, unknown> | undefined)?.projectId);

  if (!project || projectId === null) {
    return null;
  }

  return {
    ...project,
    projectId,
  };
}

async function resolveFirstVersion(projectId: number): Promise<ProjectVersionSummary | null> {
  const page = (await listProjectVersion({
    projectId,
    page: 1,
    pageSize: 1,
  })) as PageResult<ProjectVersionSummary>;
  const version = getFirstRow(page);
  const versionId = normalizeId((version as Record<string, unknown> | undefined)?.versionId);

  if (!version || versionId === null) {
    return null;
  }

  return {
    ...version,
    versionId,
  };
}

function setError(title: string, description: string) {
  errorTitle.value = title;
  errorDescription.value = description;
}

async function openProjectEntry() {
  try {
    const project = await resolveFirstProject();

    if (!project) {
      setError('暂无可用工程', '当前场景没有可打开的工程，请先进入工程列表创建或导入工程。');
      return;
    }

    if (entryTarget.value === 'detail') {
      await router.replace(`/project/project-detail/index/${project.projectId}`);
      return;
    }

    const version = await resolveFirstVersion(project.projectId);
    if (!version) {
      setError(
        '暂无可用版本',
        `工程“${project.projectName || project.projectId}”下还没有可用版本，请先进入工程详情创建版本。`
      );
      return;
    }

    const targetPath =
      entryTarget.value === 'topology'
        ? `/project/topo/index/${project.projectId}`
        : `/project/simulation/index/${project.projectId}`;

    await router.replace({
      path: targetPath,
      query: {
        versionId: String(version.versionId),
      },
    });
  } catch (error) {
    console.error('[project-entry] failed to open target page:', error);
    setError('入口打开失败', '当前场景入口解析失败，请先进入工程列表确认数据状态。');
    ElMessage.error('入口打开失败，请稍后重试');
  }
}

function goProjectList() {
  router.replace('/project/project');
}

onMounted(() => {
  void openProjectEntry();
});
</script>

<style scoped>
.project-entry {
  min-height: calc(100vh - 84px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.project-entry__loading {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 28px;
  border-radius: 16px;
}

.project-entry__icon {
  font-size: 28px;
  color: var(--zx-semantic-accent-base);
}

.project-entry__text h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
}

.project-entry__text p {
  margin: 0;
  color: var(--zx-semantic-surface-card-on-text-secondary);
}
</style>
