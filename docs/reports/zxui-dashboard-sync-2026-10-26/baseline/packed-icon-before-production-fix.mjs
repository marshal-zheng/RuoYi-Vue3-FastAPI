import { defineComponent, computed, ref, getCurrentInstance, toRaw, createBlock, createElementBlock, openBlock, unref, createSlots, withCtx, createCommentVNode, normalizeStyle, normalizeClass, createElementVNode, Fragment, resolveDynamicComponent, createVNode, renderSlot } from 'vue';
import { ElIcon } from 'element-plus';
import { useNamespace } from '@zxio/hooks';
import { useZxUiCapabilities, UnconfiguredTooltip, resolveCapabilityIcon } from '../../capabilities/context.mjs';
import { iconProps } from './props.mjs';

var _sfc_main = /* @__PURE__ */ defineComponent({
  ...{ name: "ZxIcon" },
  __name: "icon-core",
  props: iconProps,
  emits: ["click"],
  setup(__props, { emit: __emit }) {
    var _a;
    const capabilities = useZxUiCapabilities();
    const ZxTooltipOrPopover = (_a = capabilities.tooltip) != null ? _a : UnconfiguredTooltip;
    const props = __props;
    const resolvedIcon = computed(() => props.icon || props.name || "");
    const emit = __emit;
    const ns = useNamespace("icon");
    const isHover = ref(false);
    const instance = getCurrentInstance();
    const IconifyComponent = computed(() => {
      var _a2;
      return (_a2 = instance == null ? void 0 : instance.appContext.components) == null ? void 0 : _a2.Icon;
    });
    const isIconifyAvailable = computed(() => {
      var _a2;
      return !!((_a2 = instance == null ? void 0 : instance.appContext.components) == null ? void 0 : _a2.Icon);
    });
    const iconfontRe = /^(iconfont|icon|el-icon)-.*/;
    const iconifyRe = /^[a-z0-9-]+:[a-z0-9-]+$/i;
    const normalizedIcon = computed(
      () => typeof resolvedIcon.value === "string" ? resolvedIcon.value : ""
    );
    const isLocalSvg = computed(
      () => {
        var _a2, _b;
        return (_b = (_a2 = normalizedIcon.value) == null ? void 0 : _a2.startsWith("svg-icon:")) != null ? _b : false;
      }
    );
    const isIconify = computed(() => iconifyRe.test(normalizedIcon.value));
    const tooltipConfig = computed(() => {
      if (!props.tooltip) {
        return {
          enabled: false
        };
      }
      if (typeof props.tooltip === "string") {
        return {
          content: props.tooltip,
          trigger: "hover",
          placement: "top",
          offset: 6,
          enabled: true
        };
      }
      return {
        trigger: "hover",
        placement: "top",
        offset: 6,
        enabled: true,
        ...props.tooltip
      };
    });
    const icon = normalizedIcon;
    const type = computed(() => {
      if (isLocalSvg.value)
        return "svg";
      if (isIconify.value && isIconifyAvailable.value)
        return "iconify";
      if (iconfontRe.test(normalizedIcon.value))
        return "iconfont";
      if (iconComponent.value)
        return "element";
      return "iconfont";
    });
    const symbolId = computed(() => {
      return isLocalSvg.value ? `#icon-${normalizedIcon.value.split("svg-icon:")[1]}` : "";
    });
    const iconComponent = computed(() => {
      var _a2;
      const value = resolvedIcon.value;
      return typeof value === "string" ? (_a2 = resolveCapabilityIcon(capabilities, value)) != null ? _a2 : null : value ? toRaw(value) : null;
    });
    const iconClasses = computed(() => {
      const classes = [ns.b()];
      if (props.disabled) {
        classes.push("is-disabled");
      }
      if (props.className) {
        classes.push(props.className);
      }
      return classes.join(" ");
    });
    const iconfontClasses = computed(() => {
      const classes = ["iconfont", ns.b()];
      if (normalizedIcon.value) {
        const iconClass = normalizedIcon.value.startsWith("icon-") ? normalizedIcon.value : `icon-${normalizedIcon.value}`;
        classes.push(iconClass);
      }
      if (props.disabled) {
        classes.push("is-disabled");
      }
      if (props.className) {
        classes.push(props.className);
      }
      return classes.join(" ");
    });
    const iconfontStyles = computed(() => {
      const result = {};
      if (props.size) {
        result.fontSize = typeof props.size === "number" ? `${props.size}px` : props.size;
      }
      const color = isHover.value && props.hoverColor ? props.hoverColor : props.color;
      if (color) {
        result.color = color;
      }
      return result;
    });
    const currentColor = computed(() => {
      if (props.hoverColor && isHover.value) {
        return props.hoverColor;
      }
      return props.color || void 0;
    });
    const iconStyles = computed(() => {
      const styles = {};
      const color = currentColor.value;
      if (color) {
        styles[ns.cssVarBlockName("color")] = color;
        styles.color = color;
        styles["--color"] = color;
      }
      if (props.hoverColor) {
        styles[ns.cssVarBlockName("hover-color")] = props.hoverColor;
      }
      return styles;
    });
    const handleMouseEnter = () => {
      if (props.hoverColor && !props.disabled) {
        isHover.value = true;
      }
    };
    const handleMouseLeave = () => {
      if (!props.disabled) {
        isHover.value = false;
      }
    };
    const handleClick = (event) => {
      if (!props.disabled) {
        emit("click", event);
      }
    };
    return (_ctx, _cache) => {
      return tooltipConfig.value.content || tooltipConfig.value.title ? (openBlock(), createBlock(unref(ZxTooltipOrPopover), {
        key: 0,
        content: tooltipConfig.value.content,
        title: tooltipConfig.value.title,
        trigger: tooltipConfig.value.trigger,
        placement: tooltipConfig.value.placement,
        offset: tooltipConfig.value.offset,
        persistent: tooltipConfig.value.persistent,
        width: tooltipConfig.value.width,
        disabled: _ctx.disabled || !tooltipConfig.value.enabled
      }, createSlots({
        default: withCtx(() => [
          isLocalSvg.value ? (openBlock(), createBlock(unref(ElIcon), {
            key: 0,
            class: normalizeClass(iconClasses.value),
            size: _ctx.size,
            color: currentColor.value,
            style: normalizeStyle(iconStyles.value),
            onMouseenter: handleMouseEnter,
            onMouseleave: handleMouseLeave,
            onClick: handleClick
          }, {
            default: withCtx(() => [
              (openBlock(), createElementBlock("svg", {
                "aria-hidden": "true",
                fill: "currentColor"
              }, [
                createElementVNode("use", { "xlink:href": symbolId.value }, null, 8, ["xlink:href"])
              ]))
            ]),
            _: 1
            /* STABLE */
          }, 8, ["class", "size", "color", "style"])) : type.value === "iconify" ? (openBlock(), createElementBlock(
            Fragment,
            { key: 1 },
            [
              createCommentVNode(" Iconify \u56FE\u6807 "),
              (openBlock(), createBlock(resolveDynamicComponent(IconifyComponent.value), {
                icon: unref(icon),
                class: normalizeClass(iconClasses.value),
                width: _ctx.size,
                height: _ctx.size,
                style: normalizeStyle(iconStyles.value),
                onMouseenter: handleMouseEnter,
                onMouseleave: handleMouseLeave,
                onClick: handleClick
              }, null, 40, ["icon", "class", "width", "height", "style"]))
            ],
            2112
            /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
          )) : type.value === "element" ? (openBlock(), createElementBlock(
            Fragment,
            { key: 2 },
            [
              createCommentVNode(" Element Plus \u56FE\u6807 "),
              createVNode(unref(ElIcon), {
                class: normalizeClass(iconClasses.value),
                size: _ctx.size,
                color: currentColor.value,
                style: normalizeStyle(iconStyles.value),
                onMouseenter: handleMouseEnter,
                onMouseleave: handleMouseLeave,
                onClick: handleClick
              }, {
                default: withCtx(() => [
                  (openBlock(), createBlock(resolveDynamicComponent(iconComponent.value)))
                ]),
                _: 1
                /* STABLE */
              }, 8, ["class", "size", "color", "style"])
            ],
            2112
            /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
          )) : type.value === "iconfont" ? (openBlock(), createElementBlock(
            Fragment,
            { key: 3 },
            [
              createCommentVNode(" iconfont \u56FE\u6807 "),
              createElementVNode(
                "i",
                {
                  class: normalizeClass(iconfontClasses.value),
                  style: normalizeStyle(iconfontStyles.value),
                  onMouseenter: handleMouseEnter,
                  onMouseleave: handleMouseLeave,
                  onClick: handleClick
                },
                null,
                38
                /* CLASS, STYLE, NEED_HYDRATION */
              )
            ],
            2112
            /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
          )) : createCommentVNode("v-if", true)
        ]),
        _: 2
        /* DYNAMIC */
      }, [
        tooltipConfig.value.title && _ctx.$slots.popoverContent ? {
          name: "content",
          fn: withCtx(() => [
            renderSlot(_ctx.$slots, "popoverContent")
          ]),
          key: "0"
        } : void 0
      ]), 1032, ["content", "title", "trigger", "placement", "offset", "persistent", "width", "disabled"])) : isLocalSvg.value ? (openBlock(), createElementBlock(
        Fragment,
        { key: 1 },
        [
          createCommentVNode(" \u65E0 tooltip/popover \u65F6\u7684\u666E\u901A\u56FE\u6807 "),
          createCommentVNode(" SVG \u56FE\u6807 (\u901A\u8FC7 svg-icon: \u524D\u7F00\u8BC6\u522B) "),
          createVNode(unref(ElIcon), {
            class: normalizeClass(iconClasses.value),
            size: _ctx.size,
            color: currentColor.value,
            style: normalizeStyle(iconStyles.value),
            onMouseenter: handleMouseEnter,
            onMouseleave: handleMouseLeave,
            onClick: handleClick
          }, {
            default: withCtx(() => [
              (openBlock(), createElementBlock("svg", {
                "aria-hidden": "true",
                fill: "currentColor"
              }, [
                createElementVNode("use", { "xlink:href": symbolId.value }, null, 8, ["xlink:href"])
              ]))
            ]),
            _: 1
            /* STABLE */
          }, 8, ["class", "size", "color", "style"])
        ],
        2112
        /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
      )) : type.value === "iconify" ? (openBlock(), createElementBlock(
        Fragment,
        { key: 2 },
        [
          createCommentVNode(" Iconify \u56FE\u6807 "),
          (openBlock(), createBlock(resolveDynamicComponent(IconifyComponent.value), {
            icon: unref(icon),
            class: normalizeClass(iconClasses.value),
            width: _ctx.size,
            height: _ctx.size,
            style: normalizeStyle(iconStyles.value),
            onMouseenter: handleMouseEnter,
            onMouseleave: handleMouseLeave,
            onClick: handleClick
          }, null, 40, ["icon", "class", "width", "height", "style"]))
        ],
        2112
        /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
      )) : type.value === "element" ? (openBlock(), createElementBlock(
        Fragment,
        { key: 3 },
        [
          createCommentVNode(" Element Plus \u56FE\u6807 "),
          createVNode(unref(ElIcon), {
            class: normalizeClass(iconClasses.value),
            size: _ctx.size,
            color: currentColor.value,
            style: normalizeStyle(iconStyles.value),
            onMouseenter: handleMouseEnter,
            onMouseleave: handleMouseLeave,
            onClick: handleClick
          }, {
            default: withCtx(() => [
              (openBlock(), createBlock(resolveDynamicComponent(iconComponent.value)))
            ]),
            _: 1
            /* STABLE */
          }, 8, ["class", "size", "color", "style"])
        ],
        2112
        /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
      )) : (openBlock(), createElementBlock(
        Fragment,
        { key: 4 },
        [
          createCommentVNode(" iconfont \u56FE\u6807 "),
          createElementVNode(
            "i",
            {
              class: normalizeClass(iconfontClasses.value),
              style: normalizeStyle(iconfontStyles.value),
              onMouseenter: handleMouseEnter,
              onMouseleave: handleMouseLeave,
              onClick: handleClick
            },
            null,
            38
            /* CLASS, STYLE, NEED_HYDRATION */
          )
        ],
        2112
        /* STABLE_FRAGMENT, DEV_ROOT_FRAGMENT */
      ));
    };
  }
});

export { _sfc_main as default };
