"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
;/* empty css                 */
const vue = require("vue");
const formCreate = require("@form-create/element-ui");
const elementPlus = require("element-plus");
const index = require("../index-BupWnDag.js");
const input = require("@zxio/zxui/input");
const inputNumber = require("@zxio/zxui/input-number");
const select = require("@zxio/zxui/select");
const tagsInput = require("@zxio/zxui/tags-input");
function snapshot(value) {
  const normalize = (item) => {
    if (Array.isArray(item)) return item.map(normalize);
    if (item && typeof item === "object" && Object.getPrototypeOf(item) === Object.prototype)
      return Object.fromEntries(
        Object.entries(item).filter(([, v]) => v !== void 0).map(([k, v]) => [k, normalize(v)])
      );
    return item;
  };
  return index.copy(normalize(value));
}
function createSession(initial, save, committed = () => {
}) {
  let api;
  let baseline = index.copy(initial);
  let generation = 0;
  let revision = 0;
  let alive = true;
  let controller = new AbortController();
  const current = vue.shallowRef(index.copy(initial));
  const seed = vue.shallowRef(index.copy(initial));
  const key = vue.ref(0);
  const pending = vue.ref(false);
  const status = vue.ref("已载入");
  const issues = vue.shallowRef([]);
  const dirty = vue.computed(() => !index.equal(current.value, baseline));
  const applyIssues = (next) => {
    const fields = /* @__PURE__ */ new Set([
      ...issues.value.map((issue) => issue.field),
      ...next.map((issue) => issue.field)
    ]);
    issues.value = index.copy(next);
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
    if (!alive || index.equal(values, current.value)) return;
    const previous = current.value;
    current.value = index.copy(values);
    revision++;
    applyIssues(
      issues.value.filter(
        (issue) => issue.field && (api == null ? void 0 : api.getRule(issue.field)) && index.equal(previous[issue.field], values[issue.field])
      )
    );
  }
  function attach(value) {
    if (!alive || api === value) return;
    api = value;
    api.coverValue(index.copy(seed.value));
    current.value = index.copy(seed.value);
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
    current.value = index.copy(baseline);
    seed.value = index.copy(baseline);
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
      await vue.nextTick();
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
      baseline = index.copy(submitted);
      current.value = index.copy(submitted);
      status.value = "已保存";
      committed(index.copy(submitted));
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
    key: vue.readonly(key),
    seed: vue.shallowReadonly(seed),
    pending: vue.readonly(pending),
    status: vue.readonly(status),
    issues: vue.readonly(issues),
    formIssues: vue.computed(
      () => issues.value.filter((issue) => !issue.field || !(api == null ? void 0 : api.getRule(issue.field)))
    ),
    dirty,
    read: () => index.copy(current.value),
    // Internal adapter ports. SchemaForm does not expose these to its consumer.
    attach,
    observe,
    signal: () => controller.signal,
    reset,
    submit,
    dispose
  };
}
const _sfc_main$1 = /* @__PURE__ */ vue.defineComponent({
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
    const resolved = vue.computed(
      () => typeof props.options === "function" ? props.options() : props.options ?? []
    );
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createBlock(vue.unref(elementPlus.ElRadioGroup), {
        "model-value": __props.modelValue,
        disabled: __props.disabled,
        "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => emit("update:modelValue", $event))
      }, {
        default: vue.withCtx(() => [
          (vue.openBlock(true), vue.createElementBlock(vue.Fragment, null, vue.renderList(resolved.value, (option) => {
            return vue.openBlock(), vue.createBlock(vue.unref(elementPlus.ElRadio), {
              key: `${typeof option.value}:${option.value}`,
              value: option.value,
              disabled: option.disabled
            }, {
              default: vue.withCtx(() => [
                vue.createTextVNode(vue.toDisplayString(option.label), 1)
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
      component: vue.markRaw(input.ZxInput),
      props: ["placeholder", "aria-label", "type", "rows", "maxlength"]
    },
    ZxInputNumber: {
      component: vue.markRaw(inputNumber.ZxInputNumber),
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
      component: vue.markRaw(_sfc_main$1),
      props: ["options", "disabled", "aria-label"]
    },
    ZxSelect: {
      component: vue.markRaw(select.ZxSelect),
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
      component: vue.markRaw(tagsInput.ZxTagsInput),
      props: ["placeholder", "maxCount"]
    }
  };
}
const _hoisted_1 = {
  key: 0,
  class: "schema-form__errors",
  role: "alert"
};
const _sfc_main = /* @__PURE__ */ vue.defineComponent({
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
    const Engine = vue.markRaw(formCreate.factory());
    for (const [name, component] of Object.entries({
      ElForm: elementPlus.ElForm,
      ElFormItem: elementPlus.ElFormItem,
      ElRow: elementPlus.ElRow,
      ElCol: elementPlus.ElCol,
      ElButton: elementPlus.ElButton,
      ElPopover: elementPlus.ElPopover,
      ElTooltip: elementPlus.ElTooltip,
      ElIcon: elementPlus.ElIcon
    }))
      Engine.component(name, vue.markRaw(component));
    for (const [name, binding] of Object.entries({
      ...createZxuiBindings(),
      ...props.bindings
    }))
      Engine.component(name, binding.component);
    const rules = props.createRules({ read: session.read, signal: session.signal });
    const option = vue.computed(() => ({
      submitBtn: false,
      resetBtn: false,
      form: {
        labelPosition: props.labelPosition,
        labelWidth: props.labelWidth,
        disabled: props.disabled || session.pending.value
      }
    }));
    vue.onBeforeUnmount(session.dispose);
    __expose({
      read: session.read,
      reset: session.reset,
      submit: () => props.disabled ? Promise.resolve(false) : session.submit(),
      dirty: session.dirty,
      pending: session.pending,
      status: session.status
    });
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createElementBlock("section", vue.mergeProps(_ctx.$attrs, { class: "schema-form" }), [
        (vue.openBlock(), vue.createBlock(vue.resolveDynamicComponent(vue.unref(Engine)), {
          key: vue.unref(session).key.value,
          rule: vue.unref(rules),
          option: option.value,
          "onUpdate:api": vue.unref(session).attach,
          "onUpdate:modelValue": vue.unref(session).observe
        }, null, 40, ["rule", "option", "onUpdate:api", "onUpdate:modelValue"])),
        vue.unref(session).formIssues.value.length ? (vue.openBlock(), vue.createElementBlock("ul", _hoisted_1, [
          (vue.openBlock(true), vue.createElementBlock(vue.Fragment, null, vue.renderList(vue.unref(session).formIssues.value, (issue, index2) => {
            return vue.openBlock(), vue.createElementBlock("li", { key: index2 }, vue.toDisplayString(issue.message), 1);
          }), 128))
        ])) : vue.createCommentVNode("", true),
        vue.renderSlot(_ctx.$slots, "diagnostics", {
          status: vue.unref(session).status.value,
          dirty: vue.unref(session).dirty.value,
          pending: vue.unref(session).pending.value
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
  index.safeJson(value);
  if (!index.record(value)) throw new Error("Expected definition object");
  keys(value, ["id", "revision", "engine", "contract", "rules"]);
  if (typeof value.id !== "string" || !Number.isInteger(value.revision) || Number(value.revision) < 1 || value.engine !== "form-create@3.3.5" || value.contract !== "zxui-schema-form-v1")
    throw new Error("Unsupported definition identity/version");
  if (!Array.isArray(value.rules) || !value.rules.length || value.rules.length > 40)
    throw new Error("Invalid rule count");
  const fields = /* @__PURE__ */ new Set();
  for (const rule of value.rules) {
    if (!index.record(rule)) throw new Error("Invalid rule");
    keys(rule, ["type", "field", "title", "props", "validate"]);
    if (typeof rule.type !== "string" || !Object.hasOwn(bindings, rule.type))
      throw new Error("Unknown component");
    if (typeof rule.field !== "string" || !/^[A-Za-z][A-Za-z0-9]*$/.test(rule.field) || Object.hasOwn(Object.prototype, rule.field) || rule.field === "prototype" || fields.has(rule.field))
      throw new Error("Invalid/duplicate/reserved field");
    fields.add(rule.field);
    if (typeof rule.title !== "string") throw new Error("Invalid field title");
    if (rule.props !== void 0) {
      if (!index.record(rule.props)) throw new Error("Invalid props");
      keys(rule.props, bindings[rule.type].props);
    }
    if (rule.validate !== void 0) {
      if (!Array.isArray(rule.validate)) throw new Error("Invalid validation");
      for (const validation of rule.validate) {
        if (!index.record(validation)) throw new Error("Invalid validation rule");
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
exports.ZxSchemaForm = _sfc_main;
exports.createZxuiBindings = createZxuiBindings;
exports.parseDefinition = parseDefinition;
