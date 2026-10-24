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
const unsafe = /* @__PURE__ */ new Set(["__proto__", "constructor", "prototype"]);
function validPath(path) {
  return Array.isArray(path) && path.every(
    (part) => typeof part === "string" ? !unsafe.has(part) : Number.isInteger(part) && part >= 0
  );
}
function readPath(value, path) {
  let current = value;
  for (const part of path) {
    if (!current || typeof current !== "object" || !Object.hasOwn(current, part))
      return void 0;
    current = current[part];
  }
  return current;
}
function anchorPath(path, submitted, keys2) {
  return path.map((part, index$1) => {
    var _a;
    if (typeof part === "string") return part;
    const arrayPath = path.slice(0, index$1);
    const rows = readPath(submitted, arrayPath);
    const key = (_a = keys2.find((item) => index.equal(item.path, arrayPath))) == null ? void 0 : _a.key;
    if (!Array.isArray(rows)) return { index: part, unsafe: true };
    if (!key) return { index: part, snapshot: index.copy(rows) };
    const value = readPath(rows[part], [key]);
    if (typeof value !== "string" && typeof value !== "number" || rows.filter((row) => readPath(row, [key]) === value).length !== 1)
      return { index: part, unsafe: true };
    return { index: part, key, value };
  });
}
function resolvePath(anchor, current) {
  const path = [];
  for (const part of anchor) {
    if (typeof part === "string") {
      path.push(part);
      continue;
    }
    const rows = readPath(current, path);
    if (!Array.isArray(rows) || part.unsafe) return {};
    if (!part.key) {
      if (!index.equal(rows, part.snapshot)) return {};
      path.push(part.index);
      continue;
    }
    const matches = rows.flatMap(
      (row, index2) => readPath(row, [part.key]) === part.value ? [index2] : []
    );
    if (!matches.length) return { deleted: true };
    if (matches.length !== 1) return {};
    path.push(matches[0]);
  }
  return { path };
}
function locateField(api, path) {
  var _a, _b;
  if (!api || !path.length || typeof path[0] !== "string") return void 0;
  const rule = (_a = api.getRule) == null ? void 0 : _a.call(api, path[0]);
  if (!rule || rule.hidden || rule.display === false) return void 0;
  const field = path[0];
  const remaining = path.slice(1);
  if (!remaining.length) return { api, field, relative: [] };
  const child = (_b = api.getSubForm) == null ? void 0 : _b.call(api, field);
  if (Array.isArray(child) && typeof remaining[0] === "number")
    return locateField(child[remaining[0]], remaining.slice(1));
  if (child && !Array.isArray(child)) return locateField(child, remaining);
  return { api, field, relative: remaining };
}
function wrapProps(rule) {
  const wrap = rule.wrap;
  return wrap && typeof wrap === "object" && !(wrap instanceof Boolean) ? { ...wrap } : {};
}
function createErrors(getApi, getValues, arrayKeys, isComposite) {
  let entries = [];
  let overlays = [];
  const issues = vue.shallowRef([]);
  const formIssues = vue.shallowRef([]);
  const locations = vue.shallowRef([]);
  function inlineLocation(path) {
    const location = path ? locateField(getApi(), path) : void 0;
    const rule = location == null ? void 0 : location.api.getRule(location.field);
    if (!location || !rule) return void 0;
    if (!isComposite(location.api, location.field) && (rule.wrap === false || location.relative.length))
      return void 0;
    return location;
  }
  function restore() {
    for (const item of overlays) {
      const rule = item.api.getRule(item.field);
      if (rule !== item.rule) continue;
      const wrap = wrapProps(rule);
      if (wrap.error !== item.projected) continue;
      if (item.hadError) wrap.error = item.error;
      else delete wrap.error;
      item.api.updateRule(item.field, { wrap });
    }
    overlays = [];
  }
  function refresh() {
    restore();
    const visible = [];
    const summary = [];
    const currentIssues = [];
    const grouped = /* @__PURE__ */ new Map();
    for (const entry of entries) {
      const result = entry.anchor ? resolvePath(entry.anchor, getValues()) : {};
      if (result.deleted) continue;
      const issue = {
        ...entry.issue,
        ...result.path ? { path: result.path } : {}
      };
      currentIssues.push(issue);
      const location = inlineLocation(result.path);
      const rule = location == null ? void 0 : location.api.getRule(location.field);
      if (!location || !rule) {
        summary.push(issue);
        continue;
      }
      visible.push({ issue, location });
      if (isComposite(location.api, location.field)) continue;
      let group = grouped.get(rule);
      if (!group) {
        group = { location, messages: [] };
        grouped.set(rule, group);
      }
      group.messages.push(issue.message);
    }
    for (const [rule, { location, messages: messages2 }] of grouped) {
      const wrap = wrapProps(rule);
      const error = wrap.error;
      const projected = [error, ...messages2].filter(Boolean).join("；");
      overlays.push({
        ...location,
        rule,
        error,
        projected,
        hadError: Object.hasOwn(wrap, "error")
      });
      location.api.updateRule(location.field, {
        wrap: { ...wrap, error: projected }
      });
    }
    issues.value = currentIssues;
    formIssues.value = summary;
    locations.value = visible;
  }
  function set(next, submitted = getValues()) {
    entries = next.map((issue) => {
      var _a;
      if (typeof issue.message !== "string" || issue.path !== void 0 && !validPath(issue.path))
        throw new TypeError("Invalid server field issue");
      const path = ((_a = issue.path) == null ? void 0 : _a.length) ? [...issue.path] : void 0;
      return {
        issue: { ...path ? { path } : {}, message: issue.message },
        anchor: path ? anchorPath(path, submitted, arrayKeys) : void 0,
        value: path ? readPath(submitted, path) : void 0
      };
    });
    refresh();
  }
  function changed() {
    entries = entries.filter((entry) => {
      if (!entry.anchor) return false;
      const result = resolvePath(entry.anchor, getValues());
      if (result.deleted) return false;
      return !result.path || index.equal(entry.value, readPath(getValues(), result.path));
    });
    refresh();
  }
  function messages(api, field) {
    return locations.value.filter(
      (item) => item.location.api === api && item.location.field === field
    ).map(({ issue, location }) => ({
      severity: "error",
      message: issue.message,
      path: location.relative
    }));
  }
  function first() {
    var _a;
    return (_a = locations.value[0]) == null ? void 0 : _a.issue.path;
  }
  const stopVisibility = vue.watch(
    () => issues.value.map((issue) => inlineLocation(issue.path) ? 1 : 0).join(),
    refresh,
    { flush: "post" }
  );
  return {
    issues,
    formIssues,
    set,
    changed,
    refresh,
    messages,
    first,
    clear: () => set([]),
    dispose: () => {
      stopVisibility();
      set([]);
    }
  };
}
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
}, arrayKeys = []) {
  let api;
  let baseline = index.copy(initial);
  let generation = 0;
  let revision = 0;
  let alive = true;
  let accepting = false;
  const recordController = new AbortController();
  let attempt;
  const current = vue.shallowRef(index.copy(initial));
  const seed = vue.shallowRef(index.copy(initial));
  const key = vue.ref(0);
  const pending = vue.ref(false);
  const phase = vue.ref("idle");
  const status = vue.ref("已载入");
  const composites = /* @__PURE__ */ new Set();
  const compositeVersion = vue.ref(0);
  const errors = createErrors(
    () => api,
    () => current.value,
    arrayKeys,
    (owner, field) => [...composites].some((item) => item.api === owner && item.field === field)
  );
  const dirty = vue.computed(() => !index.equal(current.value, baseline));
  const blocked = vue.computed(() => {
    compositeVersion.value;
    return [...composites].some((item) => {
      var _a;
      return (_a = item.state.blocking) == null ? void 0 : _a.length;
    });
  });
  const fieldPending = vue.computed(() => {
    compositeVersion.value;
    return [...composites].some((item) => item.state.pending);
  });
  const formIssues = vue.computed(() => {
    compositeVersion.value;
    return [
      ...errors.formIssues.value,
      ...phase.value === "blocked" ? [...composites].flatMap(
        (item) => (item.state.blocking ?? []).map(({ message }) => ({ message }))
      ) : []
    ];
  });
  function focus(path = errors.first()) {
    var _a, _b, _c, _d, _e, _f, _g, _h;
    if (!path) {
      const first = [...composites].find((item) => {
        var _a2;
        return (_a2 = item.state.blocking) == null ? void 0 : _a2.length;
      });
      (_d = (_a = first == null ? void 0 : first.control()) == null ? void 0 : _a.focus) == null ? void 0 : _d.call(_a, (_c = (_b = first.state.blocking) == null ? void 0 : _b[0]) == null ? void 0 : _c.path);
      return;
    }
    const location = locateField(api, path);
    if (!location) return;
    const composite = [...composites].find(
      (item) => item.api === location.api && item.field === location.field
    );
    if (composite) (_f = (_e = composite.control()) == null ? void 0 : _e.focus) == null ? void 0 : _f.call(_e, location.relative);
    else if (!location.relative.length) (_h = (_g = location.api).focus) == null ? void 0 : _h.call(_g, location.field);
  }
  function observe(value) {
    if (!alive || accepting) return;
    const values = snapshot(value);
    if (index.equal(values, current.value)) return;
    current.value = values;
    revision++;
    errors.changed();
  }
  function attach(value) {
    if (!alive || api === value) return;
    api = value;
    accepting = true;
    try {
      api.coverValue(index.copy(seed.value));
      current.value = index.copy(seed.value);
    } finally {
      accepting = false;
    }
    errors.refresh();
  }
  function ready(value) {
    if (!alive || api !== value) return;
    baseline = snapshot(value.formData());
    current.value = index.copy(baseline);
    errors.refresh();
  }
  function invalidate() {
    generation++;
    attempt == null ? void 0 : attempt.abort();
    attempt = void 0;
    pending.value = false;
  }
  function reset() {
    invalidate();
    errors.clear();
    composites.clear();
    compositeVersion.value++;
    api = void 0;
    current.value = index.copy(baseline);
    seed.value = index.copy(baseline);
    key.value++;
    revision++;
    phase.value = "idle";
    status.value = "已恢复保存基线";
  }
  function registerComposite(owner, field, control) {
    const item = { api: owner, field, control, state: {} };
    composites.add(item);
    compositeVersion.value++;
    errors.refresh();
    return {
      messages: vue.computed(() => errors.messages(owner, field)),
      report(state) {
        if (!alive || !composites.has(item)) return;
        item.state = {
          pending: !!state.pending,
          blocking: (state.blocking ?? []).map((message) => ({
            severity: message.severity,
            message: message.message,
            ...message.path ? { path: [...message.path] } : {}
          }))
        };
        compositeVersion.value++;
      },
      dispose() {
        composites.delete(item);
        compositeVersion.value++;
        if (alive) errors.refresh();
      }
    };
  }
  function stopBlocked() {
    phase.value = "blocked";
    status.value = "请完成字段编辑后再保存";
    return false;
  }
  async function submit() {
    if (!api || pending.value || !alive) return false;
    const ownedApi = api;
    const epoch = generation;
    const edit = revision;
    attempt == null ? void 0 : attempt.abort();
    const controller = new AbortController();
    attempt = controller;
    const active = () => alive && generation === epoch && revision === edit && !controller.signal.aborted;
    pending.value = true;
    phase.value = "validating";
    status.value = "校验并保存中";
    errors.clear();
    let saving = false;
    let focusAfter;
    const blockedResult = () => {
      focusAfter = () => focus();
      return stopBlocked();
    };
    try {
      await vue.nextTick();
      if (!active()) return false;
      const controls = [...composites];
      const sameControls = () => controls.length === composites.size && controls.every((item) => composites.has(item));
      const results = await Promise.all(
        controls.map(async (item) => {
          var _a, _b;
          return {
            item,
            valid: await ((_b = (_a = item.control()) == null ? void 0 : _a.validate) == null ? void 0 : _b.call(_a))
          };
        })
      );
      await vue.nextTick();
      if (!active() || !sameControls()) return false;
      const invalid = results.find((result2) => result2.valid === false);
      if (invalid) {
        if (!blocked.value) errors.set([{ message: "请检查复合字段中的错误" }]);
        stopBlocked();
        focusAfter = () => {
          var _a, _b;
          if (composites.has(invalid.item)) (_b = (_a = invalid.item.control()) == null ? void 0 : _a.focus) == null ? void 0 : _b.call(_a);
        };
        return false;
      }
      if (blocked.value) return blockedResult();
      await ownedApi.validate();
      if (!active() || !sameControls()) return false;
      if (blocked.value) return blockedResult();
      const submitted = snapshot(ownedApi.formData());
      saving = true;
      phase.value = "saving";
      const result = await save(index.copy(submitted), controller.signal);
      if (!active() || !sameControls()) return false;
      if (blocked.value) return blockedResult();
      if (!result.ok) {
        errors.set(result.issues, submitted);
        phase.value = "invalid";
        status.value = "请修正服务端返回的问题";
        focusAfter = () => focus();
        return false;
      }
      let accepted = submitted;
      if (result.values !== void 0) {
        const authoritative = index.copy(result.values);
        accepting = true;
        try {
          ownedApi.coverValue(authoritative);
          accepted = snapshot(ownedApi.formData());
          current.value = index.copy(accepted);
        } finally {
          accepting = false;
        }
      }
      await vue.nextTick();
      if (!alive || generation !== epoch || controller.signal.aborted)
        return false;
      if (blocked.value) return blockedResult();
      const actual = snapshot(ownedApi.formData());
      if (!index.equal(actual, accepted)) {
        observe(actual);
        return false;
      }
      baseline = index.copy(accepted);
      current.value = index.copy(accepted);
      errors.clear();
      phase.value = "saved";
      status.value = "已保存";
      try {
        committed(index.copy(accepted));
      } catch (error) {
        console.error(error);
      }
      return true;
    } catch (error) {
      if (active()) {
        phase.value = saving ? "error" : "invalid";
        status.value = error instanceof Error ? error.message : "请检查表单中的错误";
        if (saving) errors.set([{ message: status.value }]);
      }
      return false;
    } finally {
      if (alive && generation === epoch && attempt === controller) {
        pending.value = false;
        if (phase.value === "validating" || phase.value === "saving") {
          phase.value = blocked.value ? "blocked" : "idle";
          status.value = "表单已更新，请重新提交";
        }
        if (focusAfter) {
          await vue.nextTick();
          if (alive && generation === epoch && !pending.value) focusAfter();
        }
      }
    }
  }
  function dispose() {
    errors.dispose();
    alive = false;
    recordController.abort();
    invalidate();
    composites.clear();
    compositeVersion.value++;
    api = void 0;
  }
  return {
    key: vue.readonly(key),
    seed: vue.shallowReadonly(seed),
    pending: vue.readonly(pending),
    phase: vue.readonly(phase),
    status: vue.readonly(status),
    issues: vue.readonly(errors.issues),
    formIssues,
    dirty,
    fieldPending,
    blocked,
    read: () => index.copy(current.value),
    focus,
    attach,
    ready,
    observe,
    registerComposite,
    signal: () => recordController.signal,
    reset,
    submit,
    dispose
  };
}
function compositeComponent(component, session, disabled) {
  const child = vue.markRaw(vue.toRaw(component));
  return vue.markRaw(
    vue.defineComponent({
      name: "SchemaCompositeField",
      inheritAttrs: false,
      props: {
        formCreateInject: {
          type: Object,
          required: true
        }
      },
      emits: ["edit-state"],
      setup(props, { attrs, emit, expose, slots }) {
        const control = vue.ref();
        const port = session.registerComposite(
          props.formCreateInject.api,
          props.formCreateInject.field,
          () => control.value
        );
        vue.onBeforeUnmount(port.dispose);
        expose({
          focus: (path) => {
            var _a, _b;
            return (_b = (_a = control.value) == null ? void 0 : _a.focus) == null ? void 0 : _b.call(_a, path);
          }
        });
        return () => vue.h(
          child,
          {
            ...attrs,
            ref: control,
            disabled: !!attrs.disabled || disabled(),
            messages: [
              ...attrs.messages ?? [],
              ...port.messages.value
            ],
            "onEdit-state": (state) => {
              port.report(state);
              emit("edit-state", state);
            }
          },
          slots
        );
      }
    })
  );
}
function prepareRule(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return value;
  const source = value;
  const rule = { ...source };
  const computed = source.computed && typeof source.computed !== "object" ? { value: source.computed } : { ...source.computed };
  const authoredPaths = Object.keys(computed);
  const bindResource = (owner, key, path, target) => {
    if (vue.isReactive(owner) || vue.isRef(owner[key]) || vue.isReactive(owner[key])) {
      if (authoredPaths.some(
        (authored) => authored === path || authored.startsWith(`${path}.`) || path.startsWith(`${authored}.`)
      )) {
        target[key] = vue.unref(owner[key]);
        return;
      }
      computed[path] = () => vue.unref(owner[key]);
      delete target[key];
    }
  };
  if (source.props) {
    rule.props = { ...source.props };
    for (const key of Object.keys(source.props)) {
      if (key === "rule" && Array.isArray(source.props.rule))
        rule.props.rule = source.props.rule.map(prepareRule);
      else bindResource(source.props, key, `props.${key}`, rule.props);
    }
  }
  if (vue.isRef(source.options) || vue.isReactive(source.options))
    bindResource(source, "options", "options", rule);
  if (Array.isArray(source.children))
    rule.children = source.children.map(prepareRule);
  if (Array.isArray(source.control))
    rule.control = source.control.map(
      (control) => ({
        ...control,
        ...Array.isArray(control.rule) ? { rule: control.rule.map(prepareRule) } : {}
      })
    );
  for (const key of ["prefix", "suffix"])
    if (source[key] && typeof source[key] === "object")
      rule[key] = prepareRule(source[key]);
  if (Object.keys(computed).length) rule.computed = computed;
  return rule;
}
function copySessionRules(rules) {
  return formCreate.copyRules(rules.map(prepareRule));
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
    ZxInput: vue.markRaw(input.ZxInput),
    ZxInputNumber: vue.markRaw(inputNumber.ZxInputNumber),
    ZxRadioGroup: vue.markRaw(_sfc_main$1),
    ZxSelect: vue.markRaw(select.ZxSelect),
    ZxTagsInput: vue.markRaw(tagsInput.ZxTagsInput)
  };
}
function createZxuiDefinitionPolicy() {
  return {
    ZxInput: {
      props: ["placeholder", "aria-label", "type", "rows", "maxlength"]
    },
    ZxInputNumber: {
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
      props: ["options", "disabled", "aria-label"]
    },
    ZxSelect: {
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
    disabled: { type: Boolean },
    arrayKeys: { default: () => [] },
    columns: { default: 1 }
  },
  emits: ["saved"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const session = createSession(
      props.initial,
      props.save,
      (values) => emit("saved", values),
      props.arrayKeys
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
    })) {
      const composite = typeof binding === "object" && "composite" in binding && binding.composite === true;
      Engine.component(
        name,
        composite ? compositeComponent(
          binding.component,
          session,
          () => props.disabled || session.pending.value
        ) : vue.markRaw(vue.toRaw(binding))
      );
    }
    const recipe = props.createRules({ read: session.read, signal: session.signal });
    function instantiateRules() {
      const result = copySessionRules(recipe);
      const layout = (items) => {
        var _a;
        for (const item of items) {
          if (!item || typeof item !== "object") continue;
          const rule = item;
          if (rule.fullWidth)
            rule.col = { ...rule.col, span: 24, xs: 24, sm: 24, md: 24 };
          delete rule.fullWidth;
          if (Array.isArray(rule.children)) layout(rule.children);
          if (Array.isArray((_a = rule.props) == null ? void 0 : _a.rule)) layout(rule.props.rule);
          for (const control of rule.control ?? [])
            if (Array.isArray(control.rule)) layout(control.rule);
        }
      };
      layout(result);
      return vue.reactive(result);
    }
    const rules = vue.shallowRef(instantiateRules());
    vue.watch(
      session.key,
      () => {
        rules.value = instantiateRules();
      },
      { flush: "sync" }
    );
    const option = vue.computed(() => ({
      submitBtn: false,
      resetBtn: false,
      col: {
        span: 24 / props.columns,
        xs: 24,
        sm: props.columns === 1 ? 24 : 12,
        md: 24 / props.columns
      },
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
      focus: session.focus,
      dirty: session.dirty,
      phase: session.phase,
      blocked: session.blocked,
      fieldPending: session.fieldPending,
      pending: session.pending,
      status: session.status
    });
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createElementBlock("section", vue.mergeProps(_ctx.$attrs, { class: "schema-form" }), [
        (vue.openBlock(), vue.createBlock(vue.resolveDynamicComponent(vue.unref(Engine)), {
          key: vue.unref(session).key.value,
          rule: rules.value,
          option: option.value,
          "onUpdate:api": vue.unref(session).attach,
          onMounted: vue.unref(session).ready,
          "onUpdate:modelValue": vue.unref(session).observe
        }, null, 40, ["rule", "option", "onUpdate:api", "onMounted", "onUpdate:modelValue"])),
        vue.unref(session).formIssues.value.length ? (vue.openBlock(), vue.createElementBlock("ul", _hoisted_1, [
          (vue.openBlock(true), vue.createElementBlock(vue.Fragment, null, vue.renderList(vue.unref(session).formIssues.value, (issue, index2) => {
            return vue.openBlock(), vue.createElementBlock("li", { key: index2 }, vue.toDisplayString(issue.message), 1);
          }), 128))
        ])) : vue.createCommentVNode("", true),
        vue.renderSlot(_ctx.$slots, "diagnostics", {
          status: vue.unref(session).status.value,
          dirty: vue.unref(session).dirty.value,
          pending: vue.unref(session).pending.value,
          phase: vue.unref(session).phase.value,
          blocked: vue.unref(session).blocked.value,
          fieldPending: vue.unref(session).fieldPending.value
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
function parseDefinition(text, policy) {
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
    if (typeof rule.type !== "string" || !Object.hasOwn(policy, rule.type))
      throw new Error("Unknown component");
    if (typeof rule.field !== "string" || !/^[A-Za-z][A-Za-z0-9]*$/.test(rule.field) || Object.hasOwn(Object.prototype, rule.field) || rule.field === "prototype" || fields.has(rule.field))
      throw new Error("Invalid/duplicate/reserved field");
    fields.add(rule.field);
    if (typeof rule.title !== "string") throw new Error("Invalid field title");
    if (rule.props !== void 0) {
      if (!index.record(rule.props)) throw new Error("Invalid props");
      keys(rule.props, policy[rule.type].props);
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
        if (validation.type !== void 0 && (typeof validation.type !== "string" || !["string", "number", "array"].includes(validation.type)))
          throw new Error("Invalid validation type");
        if (validation.trigger !== void 0 && (typeof validation.trigger !== "string" || !["blur", "change"].includes(validation.trigger)))
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
exports.createZxuiDefinitionPolicy = createZxuiDefinitionPolicy;
exports.parseDefinition = parseDefinition;
