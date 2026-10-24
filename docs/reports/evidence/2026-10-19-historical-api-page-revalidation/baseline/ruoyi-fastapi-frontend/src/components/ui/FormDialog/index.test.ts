import { describe, expect, it } from 'vitest';
import { useFormDialog } from './index';

describe('FormDialog hard-cut geometry contract', () => {
  it.each([
    { columns: 1, width: '640px' },
    { columns: 1, height: 480 },
    { columns: 1, dialogStyle: { width: '40vw' } },
    { columns: 1, dialogStyle: { height: '60vh' } },
  ])('rejects unsupported width/height at the JavaScript boundary: %j', (options) => {
    expect(() => Reflect.apply(useFormDialog, undefined, [options])).toThrow(
      '[useFormDialog] width/height are unsupported'
    );
  });

  it('rejects missing columns before constructing a dialog', () => {
    expect(() => Reflect.apply(useFormDialog, undefined, [{}])).toThrow(
      'columns must explicitly be 1, 2 or 3'
    );
  });
});
