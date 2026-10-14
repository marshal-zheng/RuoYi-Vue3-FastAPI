/* eslint-disable vue/one-component-per-file -- This harness creates independent owner/portal fixture components. */
import { defineComponent, h, reactive, ref, withDirectives } from 'vue'
import { useThemeCssAdapter } from '@zxio/theme-consumer/vue'
import { ZxThemeProvider } from '@zxio/zxui/theme-provider'
import { Widget as AcmeWidget } from '@acme/widget/vue'
import { Widget as ExamplePanel } from '@example/panel/vue'

// Deliberately invalid public consumer used only by the executable conformance runner.
const FailureProbe = defineComponent({
  props: { failure: String },
  setup(props) {
    const root = ref<HTMLElement | null>(null)
    const binding = useThemeCssAdapter(root, {
      id: 'acme-widget-css',
      actualVersion: props.failure === 'version' ? '9.0.0' : '1.0.0',
    })
    return () =>
      withDirectives(
        h('div', {
          ref: root,
          'data-failure-probe': binding.state.value,
          'data-probe-diagnostics': JSON.stringify(binding.diagnostics.value),
          style:
            props.failure === 'inline' ? { '--acme-widget-bg': 'red' } : {},
        }),
        [[binding.directive]]
      )
  },
})

export function createConsumerDemo(initial: Record<string, unknown> = {}) {
  const state = reactive({
    themeId: 'default',
    mode: 'light',
    density: 'default',
    contrast: 'normal',
    motion: 'full',
    radius: 'default',
    requestOverride: undefined as Record<string, unknown> | undefined,
    failureProbe: '',
    customPortal: false,
    disabled: false,
    nestedDisabled: false,
    show: true,
    instances: 1,
    seeds: undefined as unknown,
    overrides: undefined as unknown,
    ...initial,
  })
  const Root = defineComponent({
    setup() {
      return () =>
        h('div', { class: 'consumer-demo' }, [
          h('header', [
            h('h1', '周边库主题消费协议'),
            h('p', '业务只登记扩展。两个库通过最近 Provider 自动消费主题。'),
            ...Object.entries({
              themeId: ['default', 'defense-green'],
              mode: ['light', 'dark'],
              density: ['default', 'compact', 'comfortable'],
              contrast: ['normal', 'high', 'forced-colors'],
              motion: ['full', 'reduced', 'none'],
              radius: ['default', 'sharp', 'rounded'],
            }).map(([key, choices]) =>
              h('label', [
                `${key} `,
                h(
                  'select',
                  {
                    value: state[key as keyof typeof state],
                    onChange: (event: Event) => {
                      ;(state as Record<string, unknown>)[key] = (
                        event.target as HTMLSelectElement
                      ).value
                    },
                  },
                  choices.map((value) => h('option', { value }, value))
                ),
              ])
            ),
          ]),
          h('nav', [
            h('label', [
              h('input', {
                type: 'checkbox',
                checked: state.disabled,
                onChange: (event: Event) => {
                  state.disabled = (event.target as HTMLInputElement).checked
                },
              }),
              '停用 Widget 模块',
            ]),
            h('label', [
              h('input', {
                type: 'checkbox',
                checked: state.nestedDisabled,
                onChange: (event: Event) => {
                  state.nestedDisabled = (
                    event.target as HTMLInputElement
                  ).checked
                },
              }),
              '嵌套 Widget inactive',
            ]),
            h('label', [
              h('input', {
                type: 'checkbox',
                checked: Boolean(state.seeds),
                onChange: (event: Event) => {
                  state.seeds = (event.target as HTMLInputElement).checked
                    ? { brand: [0.42, 0.15, 0.56] }
                    : undefined
                },
              }),
              '品牌 Seeds',
            ]),
            h('label', [
              h('input', {
                type: 'checkbox',
                checked: Boolean(state.overrides),
                onChange: (event: Event) => {
                  state.overrides = (event.target as HTMLInputElement).checked
                    ? {
                        'acme-widget/gap': {
                          kind: 'literal',
                          value: { kind: 'value', value: 19, unit: 'px' },
                        },
                      }
                    : undefined
                },
              }),
              '库间距覆盖',
            ]),
          ]),
          h(
            ZxThemeProvider,
            {
              class: 'provider-root',
              ...(state.customPortal
                ? {
                    portalTarget: () =>
                      document.querySelector<HTMLElement>(
                        '[data-zx-consumer-destination="aux"]'
                      )!,
                  }
                : {}),
              themeId: state.themeId,
              mode: state.mode,
              density: state.density,
              contrast: state.contrast,
              motion: state.motion,
              radius: state.radius,
              ...state.requestOverride,
              composition: {
                ...(state.disabled ? { modules: ['example-panel'] } : {}),
                ...(state.seeds ? { seeds: state.seeds } : {}),
                ...(state.overrides ? { overrides: state.overrides } : {}),
              },
            } as never,
            () =>
              state.show
                ? [
                    state.failureProbe
                      ? h(FailureProbe, {
                          key: state.failureProbe,
                          failure: state.failureProbe,
                        })
                      : null,
                    ...Array.from({ length: state.instances }, (_, i) => [
                      h(AcmeWidget, { key: `a-${i}`, label: `outer-a-${i}` }),
                      h(ExamplePanel, { key: `b-${i}`, label: `outer-b-${i}` }),
                    ]),
                    h(
                      ZxThemeProvider,
                      {
                        class: 'provider-root',
                        scopeKey: 'nested',
                        mode: 'dark',
                        density: 'compact',
                        composition: state.nestedDisabled
                          ? { modules: ['example-panel'] }
                          : undefined,
                      },
                      () => [
                        h(AcmeWidget, { label: 'nested-a' }),
                        h(ExamplePanel, { label: 'nested-b' }),
                      ]
                    ),
                  ]
                : []
          ),
        ])
    },
  })
  return { Root, state }
}
