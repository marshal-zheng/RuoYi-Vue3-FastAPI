import { describe, expect, it } from 'vitest';
import { useVxeTableValidation, VxeValidationError } from './useVxeTableValidation';
import { createBandwidthValidator, validateByRule } from './validators';

interface EditorRow {
  protocolName: string;
  port: string;
  byteCount: number;
}
interface EditorContext {
  frequency: number;
  bandwidthLimit: number;
}

describe('typed VXE validation contracts', () => {
  it('preserves a concrete row for messages and custom validators without an index signature', async () => {
    const validation = useVxeTableValidation<EditorRow>({
      rules: {
        port: {
          validator: (value, row) => value === '80' || `${row.protocolName} 的端口必须为 80`,
        },
      },
    });
    const result = await validation.validate([{ protocolName: 'HTTP', port: '81', byteCount: 16 }]);
    expect(result.valid).toBe(false);
    expect(result.issues[0]).toMatchObject({
      field: 'port',
      value: '81',
      message: 'HTTP 的端口必须为 80',
    });
  });

  it('retains a typed context and row in global validators', async () => {
    const validation = useVxeTableValidation<EditorRow, EditorContext>({
      globalValidators: [
        createBandwidthValidator<EditorRow, EditorContext>({
          getFrameLength: (rows) => rows.reduce((length, row) => length + row.byteCount, 0),
          getFrequency: (context) => context?.frequency ?? 1,
          getBandwidthLimit: (context) => context?.bandwidthLimit ?? 0,
        }),
      ],
      context: { frequency: 2, bandwidthLimit: 100 },
    });
    const result = await validation.validate([{ protocolName: 'HTTP', port: '80', byteCount: 16 }]);
    expect(result.issues[0]).toMatchObject({ ruleName: 'bandwidth', value: 256, level: 'error' });
  });

  it('throws an inspectable validation error that retains the actual result', async () => {
    const validation = useVxeTableValidation<EditorRow>({ rules: { port: { required: true } } });
    const result = await validation.validate([{ protocolName: 'HTTP', port: '', byteCount: 16 }]);
    await expect(
      validation.validateOrThrow([{ protocolName: 'HTTP', port: '', byteCount: 16 }])
    ).rejects.toBeInstanceOf(VxeValidationError);
    await expect(
      validation.validateOrThrow([{ protocolName: 'HTTP', port: '', byteCount: 16 }])
    ).rejects.toMatchObject({ isValidationError: true, validationResult: result });
  });

  it('does not call a row-dependent message factory without a row when deriving VXE rules', async () => {
    const validation = useVxeTableValidation<EditorRow>({
      rules: {
        port: {
          required: true,
          message: (value, row) => `${row.protocolName} 缺少端口（${String(value ?? '')}）`,
        },
      },
    });
    const rules = validation.toVxeEditRules();
    const validator = rules.port[0].validator;
    expect(typeof validator).toBe('function');
    const result = await validation.validate([{ protocolName: 'HTTP', port: '', byteCount: 16 }]);
    expect(result.issues[0].message).toBe('HTTP 缺少端口（）');
  });

  it('rejects unsupported date input values at the validation boundary', () => {
    expect(validateByRule({}, { type: 'date' }, {}, 0, 'timestamp')).toBe('必须是有效日期');
    expect(validateByRule('2026-10-13', { type: 'date' }, {}, 0, 'timestamp')).toBeNull();
  });
});
