/* empty css                 */
import { shallowRef, ref, computed, readonly, shallowReadonly, nextTick, defineComponent, createBlock, openBlock, unref, withCtx, createElementBlock, Fragment, renderList, createTextVNode, toDisplayString, markRaw, onBeforeUnmount, mergeProps, createCommentVNode, renderSlot, resolveDynamicComponent } from "vue";
import formCreate from "@form-create/element-ui";
import { ElRadioGroup, ElRadio, ElIcon, ElTooltip, ElPopover, ElButton, ElCol, ElRow, ElFormItem, ElForm } from "element-plus";
import { c as copy, e as equal, s as safeJson, r as record } from "../index-BiqhT_5-.mjs";
import { ZxInput } from "@zxio/zxui/input";
import { ZxInputNumber } from "@zxio/zxui/input-number";
import { ZxSelect } from "@zxio/zxui/select";
import { ZxTagsInput } from "@zxio/zxui/tags-input";
function snapshot(value) {
  const normalize = (item) => {
    if (Array.isArray(item)) return item.map(normalize);
    if (item && typeof item === "object" && Object.getPrototypeOf(item) === Object.prototype)
      return Object.fromEntries(
        Object.entries(item).filter(([, v]) => v !== void 0).map(([k, v]) => [k, normalize(v)])
      );
    return item;
  };
  return copy(normalize(value));
}
function createSession(initial, save, committed = () => {
}) {
  let api;
  let baseline = copy(initial);
  let generation = 0;
  let revision = 0;
  let alive = true;
  let controller = new AbortController();
  const current = shallowRef(copy(initial));
  const seed = shallowRef(copy(initial));
  const key = ref(0);
  const pending = ref(false);
  const status = ref("已载入");
  const issues = shallowRef([]);
  const dirty = computed(() => !equal(current.value, baseline));
  const applyIssues = (next) => {
    const fields = /* @__PURE__ */ new Set([
      ...issues.value.map((issue) => issue.field),
      ...next.map((issue) => issue.field)
    ]);
    issues.value = copy(next);
    for (const field of fields) {
      if (api == null ? void 0 : api.getRule(field))
        api.updateRule(field, {
          wrap: {
            error: next.filter((issue) => issue.field === field).map((issue) => issue.message).join("；")
          }
        });
    }
  };
  function observe(value) {
    const values = snapshot(value);
    if (!alive || equal(values, current.value)) return;
    const previous = current.value;
    current.value = copy(values);
    revision++;
    applyIssues(
      issues.value.filter(
        (issue) => issue.field && (api == null ? void 0 : api.getRule(issue.field)) && equal(previous[issue.field], values[issue.field])
      )
    );
  }
  function attach(value) {
    if (!alive || api === value) return;
    api = value;
    api.coverValue(copy(seed.value));
    current.value = copy(seed.value);
  }
  function invalidate() {
    generation++;
    controller.abort();
    controller = new AbortController();
    pending.value = false;
  }
  function reset() {
    invalidate();
    api = void 0;
    issues.value = [];
    current.value = copy(baseline);
    seed.value = copy(baseline);
    key.value++;
    revision++;
    status.value = "已恢复保存基线";
  }
  async function submit() {
    if (!api || pending.value || !alive) return false;
    const ownedApi = api;
    const epoch = generation;
    const edit = revision;
    const signal = controller.signal;
    const active = () => alive && generation === epoch && revision === edit && !signal.aborted;
    pending.value = true;
    status.value = "校验并保存中";
    applyIssues([]);
    let validating = true;
    try {
      await nextTick();
      await ownedApi.validate();
      if (!active()) return false;
      const submitted = snapshot(ownedApi.formData());
      validating = false;
      const result = await save(submitted, signal);
      if (!active()) return false;
      if (!result.ok) {
        applyIssues(result.issues);
        status.value = "请修正服务端返回的问题";
        return false;
      }
      baseline = copy(submitted);
      current.value = copy(submitted);
      status.value = "已保存";
      committed(copy(submitted));
      return true;
    } catch (error) {
      if (active()) {
        status.value = error instanceof Error ? error.message : "请检查表单中的错误";
        if (!validating) applyIssues([{ field: "", message: status.value }]);
      }
      return false;
    } finally {
      if (alive && generation === epoch) pending.value = false;
    }
  }
  function dispose() {
    alive = false;
    invalidate();
    api = void 0;
  }
  return {
    key: readonly(key),
    seed: shallowReadonly(seed),
    pending: readonly(pending),
    status: readonly(status),
    issues: readonly(issues),
    formIssues: computed(
      () => issues.value.filter((issue) => !issue.field || !(api == null ? void 0 : api.getRule(issue.field)))
    ),
    dirty,
    read: () => copy(current.value),
    // Internal adapter ports. SchemaForm does not expose these to its consumer.
    attach,
    observe,
    signal: () => controller.signal,
    reset,
    submit,
    dispose
  };
}
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "RadioOptions",
  props: {
    modelValue: { type: [String, Number, Boolean] },
    options: { type: [Array, Function] },
    disabled: { type: Boolean }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const resolved = computed(
      () => typeof props.options === "function" ? props.options() : props.options ?? []
    );
    return (_ctx, _cache) => {
      return openBlock(), createBlock(unref(ElRadioGroup), {
        "model-value": __props.modelValue,
        disabled: __props.disabled,
        "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => emit("update:modelValue", $event))
      }, {
        default: withCtx(() => [
          (openBlock(true), createElementBlock(Fragment, null, renderList(resolved.value, (option) => {
            return openBlock(), createBlock(unref(ElRadio), {
              key: `${typeof option.value}:${option.value}`,
              value: option.value,
              disabled: option.disabled
            }, {
              default: withCtx(() => [
                createTextVNode(toDisplayString(option.label), 1)
              ]),
              _: 2
            }, 1032, ["value", "disabled"]);
          }), 128))
        ]),
        _: 1
      }, 8, ["model-value", "disabled"]);
    };
  }
});
function createZxuiBindings() {
  return {
    ZxInput: {
      component: markRaw(ZxInput),
      props: ["placeholder", "aria-label", "type", "rows", "maxlength"]
    },
    ZxInputNumber: {
      component: markRaw(ZxInputNumber),
      props: [
        "min",
        "max",
        "step",
        "precision",
        "controlsPosition",
        "aria-label"
      ]
    },
    ZxRadioGroup: {
      component: markRaw(_sfc_main$1),
      props: ["options", "disabled", "aria-label"]
    },
    ZxSelect: {
      component: markRaw(ZxSelect),
      props: [
        "clearable",
        "filterable",
        "remote",
        "valueOnClear",
        "aria-label",
        "options"
      ]
    },
    ZxTagsInput: {
      component: markRaw(ZxTagsInput),
      props: ["placeholder", "maxCount"]
    }
  };
}
const _hoisted_1 = {
  key: 0,
  class: "schema-form__errors",
  role: "alert"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...{ name: "ZxSchemaForm", inheritAttrs: false },
  __name: "SchemaForm",
  props: {
    initial: {},
    createRules: {},
    save: {},
    bindings: { default: void 0 },
    labelPosition: { default: "top" },
    labelWidth: { default: void 0 },
    disabled: { type: Boolean }
  },
  emits: ["saved"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const session = createSession(
      props.initial,
      props.save,
      (values) => emit("saved", values)
    );
    const Engine = markRaw(formCreate.factory());
    for (const [name, component] of Object.entries({
      ElForm,
      ElFormItem,
      ElRow,
      ElCol,
      ElButton,
      ElPopover,
      ElTooltip,
      ElIcon
    }))
      Engine.component(name, markRaw(component));
    for (const [name, binding] of Object.entries({
      ...createZxuiBindings(),
      ...props.bindings
    }))
      Engine.component(name, binding.component);
    const rules = props.createRules({ read: session.read, signal: session.signal });
    const option = computed(() => ({
      submitBtn: false,
      resetBtn: false,
      form: {
        labelPosition: props.labelPosition,
        labelWidth: props.labelWidth,
        disabled: props.disabled || session.pending.value
      }
    }));
    onBeforeUnmount(session.dispose);
    __expose({
      read: session.read,
      reset: session.reset,
      submit: () => props.disabled ? Promise.resolve(false) : session.submit(),
      dirty: session.dirty,
      pending: session.pending,
      status: session.status
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("section", mergeProps(_ctx.$attrs, { class: "schema-form" }), [
        (openBlock(), createBlock(resolveDynamicComponent(unref(Engine)), {
          key: unref(session).key.value,
          rule: unref(rules),
          option: option.value,
          "onUpdate:api": unref(session).attach,
          "onUpdate:modelValue": unref(session).observe
        }, null, 40, ["rule", "option", "onUpdate:api", "onUpdate:modelValue"])),
        unref(session).formIssues.value.length ? (openBlock(), createElementBlock("ul", _hoisted_1, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(unref(session).formIssues.value, (issue, index) => {
            return openBlock(), createElementBlock("li", { key: index }, toDisplayString(issue.message), 1);
          }), 128))
        ])) : createCommentVNode("", true),
        renderSlot(_ctx.$slots, "diagnostics", {
          status: unref(session).status.value,
          dirty: unref(session).dirty.value,
          pending: unref(session).pending.value
        })
      ], 16);
    };
  }
});
function keys(value, allowed) {
  for (const key of Object.keys(value))
    if (!allowed.includes(key))
      throw new Error(`Unsupported definition key: ${key}`);
}
function parseDefinition(text, bindings) {
  if (text.length > 1e5)
    throw new Error("Definition exceeds supported limit");
  const value = JSON.parse(text);
  safeJson(value);
  if (!record(value)) throw new Error("Expected definition object");
  keys(value, ["id", "revision", "engine", "contract", "rules"]);
  if (typeof value.id !== "string" || !Number.isInteger(value.revision) || Number(value.revision) < 1 || value.engine !== "form-create@3.3.5" || value.contract !== "zxui-schema-form-v1")
    throw new Error("Unsupported definition identity/version");
  if (!Array.isArray(value.rules) || !value.rules.length || value.rules.length > 40)
    throw new Error("Invalid rule count");
  const fields = /* @__PURE__ */ new Set();
  for (const rule of value.rules) {
    if (!record(rule)) throw new Error("Invalid rule");
    keys(rule, ["type", "field", "title", "props", "validate"]);
    if (typeof rule.type !== "string" || !Object.hasOwn(bindings, rule.type))
      throw new Error("Unknown component");
    if (typeof rule.field !== "string" || !/^[A-Za-z][A-Za-z0-9]*$/.test(rule.field) || Object.hasOwn(Object.prototype, rule.field) || rule.field === "prototype" || fields.has(rule.field))
      throw new Error("Invalid/duplicate/reserved field");
    fields.add(rule.field);
    if (typeof rule.title !== "string") throw new Error("Invalid field title");
    if (rule.props !== void 0) {
      if (!record(rule.props)) throw new Error("Invalid props");
      keys(rule.props, bindings[rule.type].props);
    }
    if (rule.validate !== void 0) {
      if (!Array.isArray(rule.validate)) throw new Error("Invalid validation");
      for (const validation of rule.validate) {
        if (!record(validation)) throw new Error("Invalid validation rule");
        keys(validation, [
          "required",
          "type",
          "min",
          "max",
          "message",
          "trigger"
        ]);
        if (validation.required !== void 0 && typeof validation.required !== "boolean")
          throw new Error("Invalid required");
        if (validation.type !== void 0 && !["string", "number", "array"].includes(String(validation.type)))
          throw new Error("Invalid validation type");
        if (validation.trigger !== void 0 && !["blur", "change"].includes(String(validation.trigger)))
          throw new Error("Invalid trigger");
        if (validation.message !== void 0 && typeof validation.message !== "string")
          throw new Error("Invalid validation message");
        for (const bound of ["min", "max"])
          if (validation[bound] !== void 0 && (typeof validation[bound] !== "number" || Number(validation[bound]) < 0))
            throw new Error("Invalid validation bound");
      }
    }
  }
  return value;
}
export {
  _sfc_main as ZxSchemaForm,
  createZxuiBindings,
  parseDefinition
};
