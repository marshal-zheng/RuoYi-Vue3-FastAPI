import { describe, expect, it } from 'vitest';
import { makeUpHtml } from './html';
import { formConf } from './config';
import { makeUpJs } from './js';

describe('generated rating contract', () => {
  it('emits explicit component bindings and only the configured icon imports', () => {
    const config = {
      ...formConf,
      fields: [
        {
          tag: 'zx-input',
          layout: 'colFormItem',
          vModel: 'name',
          label: 'Name',
          span: 24,
          'prefix-icon': 'Watermelon',
          'suffix-icon': 'Search',
        },
      ],
    };
    const html = makeUpHtml(config, 'form');
    const script = makeUpJs(config, 'form');
    expect(html).toContain(':prefix-icon="Watermelon"');
    expect(html).toContain(':suffix-icon="Search"');
    expect(script).toContain("import { Search, Watermelon } from '@element-plus/icons-vue'");
    expect(script).not.toContain('import *');
  });
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
