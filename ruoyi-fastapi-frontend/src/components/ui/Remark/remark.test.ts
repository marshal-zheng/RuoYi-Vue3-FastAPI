import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import RemarkDisplay from './RemarkDisplay.vue';
import { remarkSummary } from './contract';
import { mockRemark } from '@/mocks/data/remark';
import { buildGenTablePayload } from '@/views/tool/gen/gen-config-policy';

describe('remark display and write boundaries', () => {
  it('keeps grapheme clusters intact at the 160 character summary boundary', () => {
    const cluster = '👩‍💻';
    expect(remarkSummary(cluster.repeat(160))).toBe(cluster.repeat(160));
    expect(remarkSummary(cluster.repeat(161))).toBe(cluster.repeat(160) + '…');
    expect(remarkSummary('é'.repeat(161))).toBe('é'.repeat(160) + '…');
  });
  it('distinguishes missing and invalid remarks and derives an unsaved draft summary', () => {
    expect(mount(RemarkDisplay, { props: { value: null } }).text()).toBe('无备注');
    expect(mount(RemarkDisplay, { props: { value: '旧字符串' } }).text()).toBe('备注读取失败');
    const document = mockRemark('当前草稿👩‍💻', 'draft');
    const wrapper = mount(RemarkDisplay, {
      props: { value: document, summary: true },
    });
    expect(wrapper.text()).toContain('当前草稿👩‍💻');
    expect(wrapper.find('[contenteditable]').exists()).toBe(false);
  });
  it('does not send the readonly generation-table text projection back to writes', () => {
    const source = {
      tableId: 1,
      remark: null,
      remarkText: '服务端摘要',
      tableName: 'article',
    };
    const payload = buildGenTablePayload(source, []);
    expect(payload).not.toHaveProperty('remarkText');
    expect(source.remarkText).toBe('服务端摘要');
    expect(payload).toMatchObject({
      tableId: 1,
      remark: null,
      tableName: 'article',
    });
  });
});
