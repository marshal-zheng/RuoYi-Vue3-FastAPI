"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
;/* empty css                 */
const vue = require("vue");
const input = require("@zxio/zxui/input");
const index = require("../index-BupWnDag.js");
const _hoisted_1 = {
  key: 0,
  "aria-hidden": "true",
  class: "zx-schema-field__required"
};
const _hoisted_2 = ["id"];
const _hoisted_3 = ["id"];
const _hoisted_4 = ["data-severity"];
const _sfc_main$2 = /* @__PURE__ */ vue.defineComponent({
  ...{ name: "ZxField", inheritAttrs: false },
  __name: "Field",
  props: {
    label: {},
    description: {},
    required: { type: Boolean },
    group: { type: Boolean },
    messages: {}
  },
  setup(__props) {
    const props = __props;
    const id = `zx-field-${vue.useId()}`;
    const controlProps = vue.computed(() => {
      var _a, _b;
      return {
        id,
        "aria-required": !props.group && props.required || void 0,
        "aria-labelledby": props.group ? `${id}-label` : void 0,
        "aria-invalid": ((_a = props.messages) == null ? void 0 : _a.some((item) => item.severity === "error")) || void 0,
        "aria-describedby": [
          props.description ? `${id}-help` : "",
          ((_b = props.messages) == null ? void 0 : _b.length) ? `${id}-messages` : ""
        ].filter(Boolean).join(" ") || void 0
      };
    });
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createBlock(vue.resolveDynamicComponent(__props.group ? "fieldset" : "div"), vue.mergeProps(_ctx.$attrs, { class: "zx-schema-field" }), {
        default: vue.withCtx(() => {
          var _a;
          return [
            (vue.openBlock(), vue.createBlock(vue.resolveDynamicComponent(__props.group ? "legend" : "label"), {
              id: `${id}-label`,
              for: __props.group ? void 0 : id,
              class: "zx-schema-field__label"
            }, {
              default: vue.withCtx(() => [
                vue.createTextVNode(vue.toDisplayString(__props.label), 1),
                __props.required ? (vue.openBlock(), vue.createElementBlock("span", _hoisted_1, " *")) : vue.createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["id", "for"])),
            vue.renderSlot(_ctx.$slots, "default", { controlProps: controlProps.value }),
            __props.description ? (vue.openBlock(), vue.createElementBlock("small", {
              key: 0,
              id: `${id}-help`,
              class: "zx-schema-field__help"
            }, vue.toDisplayString(__props.description), 9, _hoisted_2)) : vue.createCommentVNode("", true),
            ((_a = __props.messages) == null ? void 0 : _a.length) ? (vue.openBlock(), vue.createElementBlock("ul", {
              key: 1,
              id: `${id}-messages`,
              class: "zx-schema-field__messages",
              "aria-live": "polite"
            }, [
              (vue.openBlock(true), vue.createElementBlock(vue.Fragment, null, vue.renderList(__props.messages, (item, index2) => {
                return vue.openBlock(), vue.createElementBlock("li", {
                  key: index2,
                  "data-severity": item.severity
                }, vue.toDisplayString(item.message), 9, _hoisted_4);
              }), 128))
            ], 8, _hoisted_3)) : vue.createCommentVNode("", true)
          ];
        }),
        _: 3
      }, 16);
    };
  }
});
function parseNumberText(text) {
  const value = text.trim();
  if (!value) return { status: "empty" };
  if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(value))
    return { status: "invalid" };
  const number = Number(value);
  return Number.isFinite(number) ? { status: "valid", value: number } : { status: "invalid" };
}
const _sfc_main$1 = /* @__PURE__ */ vue.defineComponent({
  ...{ name: "ZxNumberTextInput", inheritAttrs: false },
  __name: "NumberTextInput",
  props: {
    text: {},
    disabled: { type: Boolean },
    readonly: { type: Boolean }
  },
  emits: ["edit"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const emit = __emit;
    const input$1 = vue.shallowRef();
    function setInput(value) {
      input$1.value = value;
    }
    function edit(text) {
      emit("edit", { text, badInput: parseNumberText(text).status === "invalid" });
    }
    __expose({ focus: () => {
      var _a;
      return (_a = input$1.value) == null ? void 0 : _a.focus();
    } });
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createBlock(vue.unref(input.ZxInput), vue.mergeProps({ ref: setInput }, _ctx.$attrs, {
        type: "text",
        inputmode: "decimal",
        "model-value": __props.text,
        disabled: __props.disabled,
        readonly: __props.readonly,
        "onUpdate:modelValue": edit
      }), null, 16, ["model-value", "disabled", "readonly"]);
    };
  }
});
function parseJsonText(text) {
  if (!text.trim()) return { status: "empty" };
  try {
    const value = JSON.parse(text);
    index.safeJson(value, "$", false);
    return { status: "valid", value };
  } catch {
    return { status: "invalid" };
  }
}
const _sfc_main = /* @__PURE__ */ vue.defineComponent({
  ...{ name: "ZxJsonTextInput", inheritAttrs: false },
  __name: "JsonTextInput",
  props: {
    text: {},
    disabled: { type: Boolean },
    readonly: { type: Boolean }
  },
  emits: ["edit"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const emit = __emit;
    const input$1 = vue.shallowRef();
    function setInput(value) {
      input$1.value = value;
    }
    function edit(text) {
      emit("edit", { text, badInput: parseJsonText(text).status === "invalid" });
    }
    __expose({ focus: () => {
      var _a;
      return (_a = input$1.value) == null ? void 0 : _a.focus();
    } });
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createBlock(vue.unref(input.ZxInput), vue.mergeProps({ ref: setInput }, _ctx.$attrs, {
        type: "textarea",
        "model-value": __props.text,
        disabled: __props.disabled,
        readonly: __props.readonly,
        "onUpdate:modelValue": edit
      }), null, 16, ["model-value", "disabled", "readonly"]);
    };
  }
});
exports.ZxField = _sfc_main$2;
exports.ZxJsonTextInput = _sfc_main;
exports.ZxNumberTextInput = _sfc_main$1;
exports.parseJsonText = parseJsonText;
exports.parseNumberText = parseNumberText;
