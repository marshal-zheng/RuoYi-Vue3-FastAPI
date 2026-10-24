"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
;/* empty css                 */
const vue = require("vue");
const input = require("@zxio/zxui/input");
const _hoisted_1 = {
  key: 0,
  "aria-hidden": "true",
  class: "zx-schema-field__required"
};
const _hoisted_2 = ["id"];
const _hoisted_3 = ["id"];
const _hoisted_4 = ["data-severity"];
const _sfc_main$1 = /* @__PURE__ */ vue.defineComponent({
  ...{ name: "ZxField", inheritAttrs: false },
  __name: "Field",
  props: {
    label: {},
    description: {},
    required: { type: Boolean },
    messages: {}
  },
  setup(__props) {
    const props = __props;
    const id = `zx-field-${vue.useId()}`;
    const controlProps = vue.computed(() => {
      var _a, _b;
      return {
        id,
        "aria-required": props.required || void 0,
        "aria-invalid": ((_a = props.messages) == null ? void 0 : _a.some((item) => item.severity === "error")) || void 0,
        "aria-describedby": [
          props.description ? `${id}-help` : "",
          ((_b = props.messages) == null ? void 0 : _b.length) ? `${id}-messages` : ""
        ].filter(Boolean).join(" ") || void 0
      };
    });
    return (_ctx, _cache) => {
      var _a;
      return vue.openBlock(), vue.createElementBlock("div", vue.mergeProps(_ctx.$attrs, { class: "zx-schema-field" }), [
        vue.createElementVNode("label", {
          for: id,
          class: "zx-schema-field__label"
        }, [
          vue.createTextVNode(vue.toDisplayString(__props.label), 1),
          __props.required ? (vue.openBlock(), vue.createElementBlock("span", _hoisted_1, " *")) : vue.createCommentVNode("", true)
        ]),
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
          (vue.openBlock(true), vue.createElementBlock(vue.Fragment, null, vue.renderList(__props.messages, (item, index) => {
            return vue.openBlock(), vue.createElementBlock("li", {
              key: index,
              "data-severity": item.severity
            }, vue.toDisplayString(item.message), 9, _hoisted_4);
          }), 128))
        ], 8, _hoisted_3)) : vue.createCommentVNode("", true)
      ], 16);
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
const _sfc_main = /* @__PURE__ */ vue.defineComponent({
  ...{ name: "ZxNumberTextInput", inheritAttrs: false },
  __name: "NumberTextInput",
  props: {
    text: {},
    disabled: { type: Boolean },
    readonly: { type: Boolean }
  },
  emits: ["edit"],
  setup(__props, { emit: __emit }) {
    const emit = __emit;
    function edit(text) {
      emit("edit", { text, badInput: parseNumberText(text).status === "invalid" });
    }
    return (_ctx, _cache) => {
      return vue.openBlock(), vue.createBlock(vue.unref(input.ZxInput), vue.mergeProps(_ctx.$attrs, {
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
exports.ZxField = _sfc_main$1;
exports.ZxNumberTextInput = _sfc_main;
exports.parseNumberText = parseNumberText;
