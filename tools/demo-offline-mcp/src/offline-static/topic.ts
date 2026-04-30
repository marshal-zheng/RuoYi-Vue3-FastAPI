import { createIssue, ToolError } from '../errors.js';
import { sha256Hex } from '../hash.js';

const TOPIC_KEY_HINTS: Array<[RegExp, string]> = [
  [/无人机|巡检|航线|飞手|热成像/, 'drone-inspection-operations'],
  [/二手.*电脑.*回收|电脑.*回收|回收.*电脑/, 'used-computer-recycling'],
  [/房地产|地产|楼盘|交付|预售/, 'real-estate-delivery'],
  [/制造|工厂|产线|设备/, 'manufacturing-operations'],
  [/教育|学校|教务|培训/, 'education-operations'],
  [/外卖|餐饮|配送/, 'food-delivery-operations'],
];

export function normalizeTopicKey(topic: string, businessDescription = ''): string {
  const source = `${topic}\n${businessDescription}`.trim();

  if (source.length < 4 || /^(演示|demo|测试)$/i.test(source)) {
    throw new ToolError(
      createIssue({
        path: 'topic',
        code: 'topic_ambiguous',
        severity: 'error',
        actual: topic,
        expected: 'A concrete business topic',
        fixHint: 'Provide a specific business description, for example "二手电脑回收项目演示".',
        autoRepairable: false,
      })
    );
  }

  const matched = TOPIC_KEY_HINTS.find(([pattern]) => pattern.test(source));
  if (matched) return matched[1];

  const asciiSlug = source
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);

  return asciiSlug || `cn-topic-${sha256Hex(source).slice(0, 12)}`;
}

export function createStableSeed(input: {
  topicKey: string;
  businessDescription?: string;
  contractFingerprint: string;
  generatorVersion: string;
}): string {
  return sha256Hex(
    [
      input.topicKey,
      input.businessDescription?.trim() ?? '',
      input.contractFingerprint,
      input.generatorVersion,
    ].join('\n')
  );
}
