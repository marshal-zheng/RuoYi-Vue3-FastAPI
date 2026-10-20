import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import PostDlg from "@/views/system/post/components/PostDlg.vue";
import type { Save } from "@zxio/schema-form/formily";
import type { PostValues } from "@/views/system/post/components/post-form";

const api = vi.hoisted(() => ({
  read: vi.fn(),
  add: vi.fn(),
  update: vi.fn(),
  recover: vi.fn(),
}));
vi.mock("@/api/system/post", () => ({
  getPost: api.read,
  addPost: api.add,
  updatePost: api.update,
  listPost: vi.fn(),
}));
vi.mock("@/utils/http", () => ({ presentRequestError: api.recover }));
vi.mock("@/utils/dict", async () => {
  const { ref } = await import("vue");
  return { useDict: () => ({ sys_normal_disable: ref([]) }) };
});
vi.mock("@zxio/schema-form/formily", () => ({
  ZxSchemaForm: {
    name: "ZxSchemaForm",
    props: ["initial", "createSchema", "save"],
    template: "<div />",
  },
}));

const values: PostValues = {
  postName: "QA",
  postCode: "qa",
  postSort: 0,
  status: "0",
  remark: "",
};
let wrapper: ReturnType<typeof mount>;
async function opening(id?: number): Promise<Save<PostValues>> {
  wrapper = mount(PostDlg, {
    global: {
      stubs: {
        ElAlert: true,
        ElButton: true,
        ZxDialog: {
          props: ["modelValue"],
          template: "<section><slot /></section>",
        },
        DictStatus: true,
      },
    },
  });
  await (
    wrapper.vm as unknown as { open: (id?: number) => Promise<void> }
  ).open(id);
  await flushPromises();
  return wrapper.findComponent({ name: "ZxSchemaForm" }).props("save");
}
const failure = (
  status: number,
  errors?: { field: string; message: string }[],
) =>
  Object.assign(new Error("save failed"), {
    problem: {
      type: "about:blank",
      title: "save failed",
      detail: "save failed",
      instance: "/system/post",
      status,
      errors,
    },
    meta: { status },
  });
beforeEach(() => {
  vi.resetAllMocks();
  api.read.mockResolvedValue({ ...values, postId: 31 });
  api.add.mockResolvedValue({ ...values, postId: 31 });
  api.update.mockResolvedValue({ ...values, postId: 31 });
});
afterEach(() => wrapper?.unmount());

describe("post save feedback ownership", () => {
  it("lets the form own a conflict while requesting only silent HTTP errors", async () => {
    const save = await opening();
    const error = failure(409);
    api.add.mockRejectedValueOnce(error);
    await expect(save(values, new AbortController().signal)).resolves.toEqual({
      ok: false,
      outcome: "rejected",
      issues: [{ message: "save failed" }],
    });
    expect(api.add).toHaveBeenCalledTimes(1);
    expect(api.add).toHaveBeenCalledWith(values, { silentError: true });
    expect(api.recover).not.toHaveBeenCalled();
  });
  it("keeps field issues in the form on update", async () => {
    const save = await opening(31);
    api.update.mockRejectedValueOnce(
      failure(422, [{ field: "post_code", message: "invalid code" }]),
    );
    await expect(save(values, new AbortController().signal)).resolves.toEqual({
      ok: false,
      outcome: "rejected",
      issues: [{ path: ["postCode"], message: "invalid code" }],
    });
    expect(api.update).toHaveBeenCalledTimes(1);
    expect(api.update).toHaveBeenCalledWith(
      { ...values, postId: 31 },
      { silentError: true },
    );
    expect(api.recover).not.toHaveBeenCalled();
  });
  it("restores the existing authentication recovery without adding a form error", async () => {
    const save = await opening();
    const error = failure(401);
    api.add.mockRejectedValueOnce(error);
    await expect(save(values, new AbortController().signal)).resolves.toEqual({
      ok: false,
      issues: [],
    });
    expect(api.recover).toHaveBeenCalledTimes(1);
    expect(api.recover).toHaveBeenCalledWith(error, {
      silentError: false,
      feedback: { mode: "auto" },
    });
  });
  it("does not recover authentication from an aborted save", async () => {
    const save = await opening();
    let reject!: (error: Error) => void;
    api.add.mockReturnValueOnce(
      new Promise((_, fail) => {
        reject = fail;
      }),
    );
    const controller = new AbortController();
    const task = save(values, controller.signal);
    controller.abort();
    reject(failure(401));
    await expect(task).resolves.toEqual({
      ok: false,
      outcome: "unknown",
      issues: [],
    });
    expect(api.recover).not.toHaveBeenCalled();
  });
  it("keeps a successful save result and the existing success channel", async () => {
    const save = await opening();
    await expect(save(values, new AbortController().signal)).resolves.toEqual({
      ok: true,
      values,
    });
    expect(api.add).toHaveBeenCalledTimes(1);
    expect(api.add).toHaveBeenCalledWith(values, { silentError: true });
  });
});
