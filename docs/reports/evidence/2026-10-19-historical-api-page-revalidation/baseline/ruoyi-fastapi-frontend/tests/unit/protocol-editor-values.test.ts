import { describe, expect, it } from 'vitest';
import { normalizeConfigEditorValue } from '@/components/business/Protocol/templates/editorTypes';
import {
  normalizeFieldRow,
  normalizeFieldRows,
} from '@/components/business/Protocol/templates/fieldUtils';

describe('protocol editor boundaries', () => {
  it('normalizes scalar and dictionary editor values into the text config contract', () => {
    expect(normalizeConfigEditorValue(12)).toEqual({ value: '12', label: '' });
    expect(normalizeConfigEditorValue({ value: 'udp', label: 'UDP' })).toEqual({
      value: 'udp',
      label: 'UDP',
    });
    expect(normalizeConfigEditorValue(null)).toEqual({ value: '', label: '' });
    expect(normalizeConfigEditorValue({ unexpected: true })).toEqual({ value: '', label: '' });
  });

  it('reads the value from a real native input event', () => {
    const input = document.createElement('input');
    input.value = '1553';
    let result;
    input.addEventListener('input', (event) => {
      result = normalizeConfigEditorValue(event);
    });
    input.dispatchEvent(new Event('input'));
    expect(result).toEqual({ value: '1553', label: '' });
  });

  it('keeps field normalization within the declared row contract', () => {
    expect(normalizeFieldRow({ seqNo: 3, infoName: '速度', scale: 2 })).toMatchObject({
      seqNo: '3',
      infoName: '速度',
      scale: '2',
    });
    expect(normalizeFieldRow({ 序号: 4, 信息名称: '角度' })).toMatchObject({
      seqNo: '4',
      infoName: '角度',
    });
    expect(normalizeFieldRows([null, 'bad'])).toHaveLength(2);
    expect(normalizeFieldRow({ infoName: { unexpected: true } }).infoName).toBe('');
  });
});
