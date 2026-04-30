import { createIssue, ToolError } from '../errors.js';
import { sha256Hex } from '../hash.js';

const TOPIC_KEY_HINTS: Array<[RegExp, string]> = [
  [
    /云服务|云主机|MSP|Kubernetes|k8s|容器平台|容器云|对象存储|OSS|数据库高可用|灾备演练|日志监控|可观测|两地三中心|GitOps/,
    'cloud-service-msp',
  ],
  [/无人机|巡检|航线|飞手|热成像/, 'drone-inspection-operations'],
  [/二手.*电脑.*回收|电脑.*回收|回收.*电脑/, 'used-computer-recycling'],
  // 避免单独匹配「交付」等通用词，防止云服务/通用交付主题落入地产蓝图
  [/房地产|地产|楼盘|预售|网签|交房|售楼|置业/, 'real-estate-delivery'],
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
