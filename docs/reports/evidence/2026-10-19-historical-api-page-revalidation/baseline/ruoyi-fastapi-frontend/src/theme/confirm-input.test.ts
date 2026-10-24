import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { BoundConfirmInputFactory } from '@zxio/zxui';

import { confirmInputDanger, setBoundConfirmInputFactory } from './confirm-input';

function mockFactory(danger: BoundConfirmInputFactory['danger']): BoundConfirmInputFactory {
  return {
    create: vi.fn(),
    danger,
    warning: vi.fn(),
    info: vi.fn(),
  };
}

describe('confirmInputDanger', () => {
  beforeEach(() => {
    setBoundConfirmInputFactory(null);
  });

  it('throws when the theme host has not been bound', async () => {
    await expect(confirmInputDanger({ targetName: 'demo' })).rejects.toThrow(
      'ZXUI theme host is not bound'
    );
  });

  it('resolves with the confirmed payload', async () => {
    const danger = vi.fn<BoundConfirmInputFactory['danger']>(async () => ({
      ok: true,
      value: {
        result: Promise.resolve({
          ok: true,
          value: { keyword: 'demo' },
          diagnostics: [],
        }),
        closed: Promise.resolve(),
        close: () => ({ ok: true, value: undefined, diagnostics: [] }),
      },
      diagnostics: [],
    }));
    setBoundConfirmInputFactory(mockFactory(danger));

    await expect(confirmInputDanger({ targetName: 'demo' })).resolves.toEqual({
      keyword: 'demo',
    });
    expect(danger).toHaveBeenCalledWith({ targetName: 'demo' });
  });

  it('rejects when the user cancels', async () => {
    setBoundConfirmInputFactory(
      mockFactory(async () => ({
        ok: true,
        value: {
          result: Promise.resolve({
            ok: false,
            diagnostics: [
              {
                code: 'CONSUMER_BOUND_CONFIRM_INPUT_CANCELLED',
                phase: 'imperative-ui',
                details: {},
              },
            ],
          }),
          closed: Promise.resolve(),
          close: () => ({
            ok: true,
            value: undefined,
            diagnostics: [],
          }),
        },
        diagnostics: [],
      }))
    );

    await expect(confirmInputDanger({ targetName: 'demo' })).rejects.toMatchObject({
      code: 'CONSUMER_BOUND_CONFIRM_INPUT_CANCELLED',
    });
  });
});
