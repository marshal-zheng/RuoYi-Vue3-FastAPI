/* empty css                 */
import { defineComponent, useId, computed, createElementBlock, openBlock, mergeProps, createElementVNode, renderSlot, createCommentVNode, createTextVNode, toDisplayString, Fragment, renderList, createBlock, unref } from "vue";
import { ZxInput } from "@zxio/zxui/input";
const _hoisted_1 = {
  key: 0,
  "aria-hidden": "true",
  class: "zx-schema-field__required"
};
const _hoisted_2 = ["id"];
const _hoisted_3 = ["id"];
const _hoisted_4 = ["data-severity"];
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
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
    const id = `zx-field-${useId()}`;
    const controlProps = computed(() => {
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
      return openBlock(), createElementBlock("div", mergeProps(_ctx.$attrs, { class: "zx-schema-field" }), [
        createElementVNode("label", {
          for: id,
          class: "zx-schema-field__label"
        }, [
          createTextVNode(toDisplayString(__props.label), 1),
          __props.required ? (openBlock(), createElementBlock("span", _hoisted_1, " *")) : createCommentVNode("", true)
        ]),
        renderSlot(_ctx.$slots, "default", { controlProps: controlProps.value }),
        __props.description ? (openBlock(), createElementBlock("small", {
          key: 0,
          id: `${id}-help`,
          class: "zx-schema-field__help"
        }, toDisplayString(__props.description), 9, _hoisted_2)) : createCommentVNode("", true),
        ((_a = __props.messages) == null ? void 0 : _a.length) ? (openBlock(), createElementBlock("ul", {
          key: 1,
          id: `${id}-messages`,
          class: "zx-schema-field__messages",
          "aria-live": "polite"
        }, [
          (openBlock(true), createElementBlock(Fragment, null, renderList(__props.messages, (item, index) => {
            return openBlock(), createElementBlock("li", {
              key: index,
              "data-severity": item.severity
            }, toDisplayString(item.message), 9, _hoisted_4);
          }), 128))
        ], 8, _hoisted_3)) : createCommentVNode("", true)
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
const _sfc_main = /* @__PURE__ */ defineComponent({
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
      return openBlock(), createBlock(unref(ZxInput), mergeProps(_ctx.$attrs, {
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
export {
  _sfc_main$1 as ZxField,
  _sfc_main as ZxNumberTextInput,
  parseNumberText
};
