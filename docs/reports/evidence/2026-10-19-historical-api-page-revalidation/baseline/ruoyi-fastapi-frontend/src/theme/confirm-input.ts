import type { BoundConfirmInputFactory, BoundConfirmInputOptions } from '@zxio/zxui';

export class ZxConfirmInputError extends Error {
  readonly code: string;

  constructor(code: string) {
    super(code);
    this.name = 'ZxConfirmInputError';
    this.code = code;
  }
}

let boundConfirmInputFactory: BoundConfirmInputFactory | null = null;
let boundConfirmInputFactoryProvider: (() => BoundConfirmInputFactory) | null = null;

export function setBoundConfirmInputFactory(factory: BoundConfirmInputFactory | null): void {
  boundConfirmInputFactory = factory;
  boundConfirmInputFactoryProvider = factory ? () => factory : null;
}

export function setBoundConfirmInputFactoryProvider(
  provider: (() => BoundConfirmInputFactory) | null
): void {
  boundConfirmInputFactory = null;
  boundConfirmInputFactoryProvider = provider;
}

function resolveBoundConfirmInputFactory(): BoundConfirmInputFactory {
  if (boundConfirmInputFactory) {
    return boundConfirmInputFactory;
  }
  if (!boundConfirmInputFactoryProvider) {
    throw new Error('ZXUI theme host is not bound');
  }
  boundConfirmInputFactory = boundConfirmInputFactoryProvider();
  return boundConfirmInputFactory;
}

export async function confirmInputDanger(options?: BoundConfirmInputOptions): Promise<unknown> {
  const factory = resolveBoundConfirmInputFactory();
  const handle = await factory.danger(options);
  if (!handle.ok) {
    throw new ZxConfirmInputError(
      handle.diagnostics[0]?.code ?? 'CONSUMER_BOUND_CONFIRM_INPUT_RENDER_FAILED'
    );
  }

  const result = await handle.value.result;
  if (!result.ok) {
    throw new ZxConfirmInputError(
      result.diagnostics[0]?.code ?? 'CONSUMER_BOUND_CONFIRM_INPUT_CLOSED'
    );
  }

  return result.value;
}
