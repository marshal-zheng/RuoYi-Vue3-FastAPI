import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import * as vue from 'vue';
import UserInfo from '@/views/system/user/profile/userInfo.vue';
import ResetPwd from '@/views/system/user/profile/resetPwd.vue';
import UserAvatar from '@/views/system/user/profile/userAvatar.vue';
import { updateUserProfile, updateUserPwd, uploadAvatar } from '@/api/system/user';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

const store = vi.hoisted(() => ({ avatar: 'initial-avatar' }));
vi.mock('@/store/modules/user', () => ({ default: () => store }));
vi.mock('@/api/system/user', () => ({
  updateUserProfile: vi.fn(),
  updateUserPwd: vi.fn(),
  uploadAvatar: vi.fn(),
}));
vi.mock('vue-cropper', () => ({ VueCropper: { name: 'VueCropper', render: () => null } }));
const validate = vi.fn<() => Promise<boolean>>();
let crop!: (blob: Blob) => void;
const Slot = { template: '<div><slot /></div>' };
const Form = vue.defineComponent({
  setup(_, { expose, slots }) {
    expose({ validate: () => validate() });
    return () => vue.h('form', slots.default?.());
  },
});
const Cropper = vue.defineComponent({
  setup(_, { expose }) {
    expose({
      getCropBlob: (callback: typeof crop) => {
        crop = callback;
      },
    });
    return () => null;
  },
});
const mounted: ReturnType<typeof mount>[] = [];
function component(target: vue.Component, props: Record<string, unknown> = {}) {
  const wrapper = mount(target, {
    props,
    global: {
      config: {
        globalProperties: {
          $tab: { closePage: vi.fn() },
        } as unknown as vue.ComponentCustomProperties,
      },
      stubs: {
        ElForm: Form,
        ElFormItem: Slot,
        ElButton: Slot,
        ZxInput: true,
        ElRadio: true,
        ElRadioGroup: Slot,
        ZxDialog: Slot,
        ElRow: Slot,
        ElCol: Slot,
        ElUpload: Slot,
        ElIcon: Slot,
        VueCropper: Cropper,
      },
    },
  });
  mounted.push(wrapper);
  return { wrapper, state: (wrapper.vm as any).$.setupState };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, [], []);
  vi.clearAllMocks();
  validate.mockResolvedValue(true);
  vi.mocked(updateUserProfile).mockResolvedValue({ data: null, postGroup: '', roleGroup: '' });
  vi.mocked(updateUserPwd).mockResolvedValue(null);
  vi.mocked(uploadAvatar).mockResolvedValue({ imgUrl: '/avatar.png' });
  store.avatar = 'initial-avatar';
  for (const key of ['ref', 'reactive', 'watch', 'getCurrentInstance', 'nextTick'])
    vi.stubGlobal(key, vue[key as keyof typeof vue]);
});
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

it.each([UserInfo, ResetPwd])(
  'captures profile scope before asynchronous validation',
  async (target) => {
    const validation = deferred<boolean>();
    validate.mockReturnValueOnce(validation.promise);
    const { state } = component(
      target,
      target === UserInfo ? { user: { userId: 1, nickName: 'Alice' } } : {}
    );
    const pending = state.submit();
    await flushPromises();
    setQuerySession(2, [], []);
    validation.resolve(true);
    await pending;
    expect(updateUserProfile).not.toHaveBeenCalled();
    expect(updateUserPwd).not.toHaveBeenCalled();
  }
);

it('does not apply an old profile write result to a new scope', async () => {
  const response = deferred<Awaited<ReturnType<typeof updateUserProfile>>>();
  vi.mocked(updateUserProfile).mockReturnValueOnce(response.promise);
  const user = { userId: 1, nickName: 'Alice', phonenumber: 'before', email: 'before' };
  const { state } = component(UserInfo, { user });
  state.form.phonenumber = 'submitted';
  const pending = state.submit();
  await flushPromises();
  setQuerySession(2, [], []);
  response.resolve({ data: null, postGroup: '', roleGroup: '' });
  await pending;
  expect(user.phonenumber).toBe('before');
});

it('captures the avatar scope before asynchronous cropping', async () => {
  const { state } = component(UserAvatar);
  state.editCropper();
  state.modalOpened();
  await vue.nextTick();
  const pending = state.uploadImg();
  await flushPromises();
  setQuerySession(2, [], []);
  crop(new Blob(['avatar']));
  await pending;
  expect(uploadAvatar).not.toHaveBeenCalled();
});

it('does not update the current user store from an old avatar response', async () => {
  const response = deferred<{ imgUrl: string }>();
  vi.mocked(uploadAvatar).mockReturnValueOnce(response.promise);
  const { state } = component(UserAvatar);
  state.editCropper();
  state.modalOpened();
  await vue.nextTick();
  const pending = state.uploadImg();
  await flushPromises();
  crop(new Blob(['avatar']));
  await flushPromises();
  setQuerySession(2, [], []);
  store.avatar = 'new-session-avatar';
  response.resolve({ imgUrl: '/old-avatar.png' });
  await pending;
  expect(store.avatar).toBe('new-session-avatar');
});
