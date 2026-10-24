import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
import * as vue from 'vue';
import type { ComponentCustomProperties } from 'vue';
const { ref } = vue;
import JobPage from '@/views/monitor/job/index.vue';

const api = vi.hoisted(() => ({ get: vi.fn(), add: vi.fn(), edit: vi.fn(), run: vi.fn() }));
vi.mock('@/api/monitor/job', () => ({
  listJob: vi.fn(),
  getJob: api.get,
  addJob: api.add,
  updateJob: api.edit,
  runJob: api.run,
  changeJobStatus: vi.fn(),
  delJob: vi.fn(),
}));
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/components/ui/Crontab/index.vue', () => ({ default: { render: () => null } }));
const mounted: ReturnType<typeof shallowMount>[] = [];
function page() {
  const wrapper = shallowMount(
    { ...JobPage, render: () => null },
    {
      global: {
        config: {
          globalProperties: {
            useDict: () => ({
              sys_job_group: ref([]),
              sys_job_status: ref([]),
              sys_job_executor: ref([]),
            }),
            resetForm: vi.fn(),
            selectDictLabel: (_options: unknown, value: unknown) => value,
            parseTime: (value: unknown) => value,
            $modal: { confirm: () => Promise.resolve() },
          } as unknown as ComponentCustomProperties,
        },
        stubs: {
          ZxDialog: { template: '<section><slot /></section>' },
          ElForm: { template: '<form><slot /></form>', methods: { validate: async () => true } },
        },
      },
    }
  );
  (wrapper.vm as any).$.refs = { jobRef: { validate: async () => true } };
  mounted.push(wrapper);
  return (wrapper.vm as any).$.setupState;
}
beforeEach(() => {
  vi.resetAllMocks();
  api.add.mockResolvedValue({});
  api.edit.mockResolvedValue({});
  api.run.mockResolvedValue({});
  for (const key of [
    'ref',
    'reactive',
    'toRefs',
    'toRef',
    'computed',
    'shallowReactive',
    'getCurrentInstance',
  ])
    vi.stubGlobal(key, vue[key as keyof typeof vue]);
  vi.stubGlobal('useRouter', () => ({ push: vi.fn() }));
  api.get.mockResolvedValue({
    jobId: 42,
    jobName: 'Task',
    invokeTarget: 'module_task.scheduler_test.job',
    cronExpression: '0 0 0 * * ?',
    status: '1',
    createBy: 'admin',
    updateTime: 'read-only',
    type: 'status',
  });
});
afterEach(() => mounted.splice(0).forEach((w) => w.unmount()));
for (const mode of ['add', 'edit']) {
  it(`job ${mode} submits operation fields without response metadata`, async () => {
    const s = page();
    if (mode === 'edit') {
      s.handleUpdate({ jobId: 42 });
      await flushPromises();
    } else s.handleAdd();
    Object.assign(s.form, {
      jobName: 'Task',
      invokeTarget: 'module_task.scheduler_test.job',
      cronExpression: '0 0 0 * * ?',
      createBy: 'forged',
      updateTime: 'forged',
      type: 'status',
    });
    await s.submitForm();
    const payload = (mode === 'edit' ? api.edit : api.add).mock.calls[0][0];
    expect(payload.jobName).toBe('Task');
    for (const key of ['createBy', 'updateTime', 'type']) expect(payload).not.toHaveProperty(key);
    if (mode === 'edit') expect(payload.jobId).toBe(42);
    else expect(payload).not.toHaveProperty('jobId');
  });
}
it('run submits identity without client-supplied group', async () => {
  const s = page();
  await s.handleRun({ jobId: 42, jobGroup: 'forged' });
  expect(api.run).toHaveBeenCalledExactlyOnceWith(42);
});
