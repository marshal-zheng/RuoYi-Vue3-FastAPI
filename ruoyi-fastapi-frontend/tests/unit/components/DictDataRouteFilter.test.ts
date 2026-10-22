import { afterEach, expect, it, vi } from 'vitest';
import { defineComponent, h, onMounted, reactive, ref, type App } from 'vue';
import { flushPromises, shallowMount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import DictData from '@/views/system/dict/data.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { dictTypeDetailOptions } from '@/queries/system/dict';
import { listData } from '@/api/system/dict/data';

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { dictId: '1' } }),
}));
vi.mock('@/api/system/dict/data', () => ({
  listData: vi.fn(),
  getData: vi.fn(),
}));
vi.mock('@/api/system/dict/type', () => ({ getType: vi.fn() }));
vi.mock('@/components/ui/FormDialog', () => ({
  FormGrid: {},
  useFormDialog: () => ({
    state: reactive({ data: {}, visible: false }),
    dialogProps: ref({}),
    dialogEvents: ref({}),
  }),
}));
const Slot = defineComponent({
  setup:
    (_, { slots }) =>
    () =>
      h('section', slots.default?.()),
});
const Grid = defineComponent({
  props: ['initialState', 'loadData'],
  setup(props) {
    onMounted(() =>
      props.loadData({
        query: props.initialState.query,
        pager: { page: 1, size: 10 },
      })
    );
    return () => h('div');
  },
});
let wrapper: ReturnType<typeof shallowMount> | undefined;
afterEach(() => {
  wrapper?.unmount();
  endQuerySession();
  queryClient.clear();
});

it('includes the route dictionary filter in the first list request when type metadata is already cached', async () => {
  const scope = setQuerySession(1, ['admin'], ['*:*:*']);
  queryClient.setQueryData(dictTypeDetailOptions(scope, 1).queryKey, {
    remarkText: '', dictId: 1,
    dictType: 'sys_user_sex',
    dictName: '用户性别',
  });
  vi.mocked(listData).mockResolvedValue({
    items: [],
    total: 0,
    page: 1,
    pageSize: 10,
  });
  wrapper = shallowMount(DictData, {
    global: {
      plugins: [
        [VueQueryPlugin, { queryClient }],
        (app: App) => {
          app.config.globalProperties.useDict = () => ({ sys_normal_disable: ref([]) });
        },
      ],
      directives: { hasPermi: () => {}, loading: () => {} },
      stubs: {
        ...Object.fromEntries(
          [
            'ElButton',
            'ElAlert',
            'ZxButton',
            'ZxSearch',
            'ZxListToolbar',
            'ElTableColumn',
            'ElTag',
            'DictTag',
            'ElTable',
            'ZxInput',
            'ElFormItem',
            'ElInputNumber',
            'ElOption',
            'ElSelect',
            'ElRadio',
            'ElRadioGroup',
            'ElForm',
          ].map((name) => [name, true])
        ),
        ZxContentWrap: Slot,
        ZxGridList: Grid,
        DictStatus: true,
        ZxDialog: true,
      },
    },
  });
  await flushPromises();
  expect(listData).toHaveBeenCalledWith(
    expect.objectContaining({
      dictType: 'sys_user_sex',
      page: 1,
      pageSize: 10,
    }),
    expect.any(Object)
  );
});
