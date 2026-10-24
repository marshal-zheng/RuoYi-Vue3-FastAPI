import { describe, expect, it } from 'vitest';
import { makeUpHtml } from './html';
import { formConf } from './config';

describe('generated rating contract', () => {
  it('exports the configured maximum to the real ElRate prop', () => {
    const html = makeUpHtml(
      {
        ...formConf,
        fields: [
          {
            tag: 'el-rate',
            layout: 'colFormItem',
            vModel: 'score',
            label: 'Score',
            span: 24,
            max: 7,
          },
        ],
      },
      'form'
    );
    expect(html).toContain(":max='7'");
  });
});
