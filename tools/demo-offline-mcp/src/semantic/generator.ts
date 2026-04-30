import { sha256Hex } from '../hash.js';
import type {
  BusinessBlueprint,
  SemanticDepartment,
  SemanticDomainObject,
  SemanticMetricDefinition,
  SemanticPersona,
  SemanticProcessStage,
  SemanticRiskSeverity,
  SemanticRiskType,
  SemanticStoryBeat,
} from './types.js';

export interface GenerateBusinessBlueprintInput {
  topic: string;
  businessDescription?: string;
  topicKey: string;
  seed: string;
  contractFingerprint: string;
  generatorVersion: string;
  projectCount: number;
}

interface DomainProfile {
  keywords: string[];
  domainObjects: string[];
  departments: Array<{ label: string; responsibility: string }>;
  personas: Array<{ role: string; actions: string[] }>;
  processStages: Array<{ label: string; action: string }>;
  riskTypes: Array<{ label: string; severity: SemanticRiskSeverity; signals: string[] }>;
  metricDefinitions: Array<{ name: string; unit: string; samples: string[]; trend?: 'up' | 'down' | 'flat' }>;
}

const PERSON_NAMES = ['顾清远', '林知夏', '陈启航', '周明岚', '叶南乔', '许知衡', '何以安', '沈洛宁'];

const DRONE_PROFILE: DomainProfile = {
  keywords: ['无人机巡检', '航线', '飞手', '热成像', '隐患工单', '空域审批'],
  domainObjects: ['巡检航线', '无人机机队', '杆塔区段', '热成像缺陷', '飞行电池', '作业空域', '隐患工单'],
  departments: [
    { label: '巡检调度中心', responsibility: '统筹航线窗口、飞手排班和任务优先级' },
    { label: '设备运维部', responsibility: '复核杆塔缺陷、派发隐患工单和闭环复测' },
    { label: '安全合规组', responsibility: '确认空域审批、电池安全和现场风控' },
  ],
  personas: [
    { role: '巡检调度员', actions: ['调整航线窗口', '协调飞手接力', '同步天气风险'] },
    { role: '设备缺陷工程师', actions: ['复核热成像缺陷', '判定隐患等级', '发起复测'] },
    { role: '安全合规专员', actions: ['核对空域许可', '检查电池健康', '留存飞行记录'] },
    { role: '现场飞手', actions: ['执行航线采集', '回传异常影像', '确认返航状态'] },
  ],
  processStages: [
    { label: '航线排程', action: '锁定巡检窗口并生成飞行批次' },
    { label: '空域审批', action: '核对飞行许可和现场禁飞条件' },
    { label: '现场起飞', action: '按批次执行杆塔区段采集' },
    { label: '缺陷复核', action: '比对热成像与历史隐患记录' },
    { label: '工单闭环', action: '派发运维工单并完成复测确认' },
    { label: '复盘归档', action: '汇总航线效率和风险处置记录' },
  ],
  riskTypes: [
    { label: '空域窗口冲突', severity: 'high', signals: ['许可延迟', '临时禁飞', '航线重排'] },
    { label: '电池健康异常', severity: 'medium', signals: ['电压波动', '返航余量不足', '替换电池排队'] },
    { label: '影像识别误判', severity: 'medium', signals: ['热斑疑似', '可见光遮挡', '复核样本不足'] },
    { label: '恶劣天气插队', severity: 'high', signals: ['阵风超限', '降雨逼近', '任务窗口缩短'] },
    { label: '工单闭环延迟', severity: 'low', signals: ['复测排队', '责任班组待确认', '材料补录'] },
  ],
  metricDefinitions: [
    { name: '航线完成率', unit: '%', samples: ['82%', '89%', '94%', '97%'], trend: 'up' },
    { name: '缺陷识别准确率', unit: '%', samples: ['88%', '91%', '93%', '95%'], trend: 'up' },
    { name: '平均返航余量', unit: '%', samples: ['18%', '24%', '31%', '36%'], trend: 'up' },
    { name: '隐患闭环时长', unit: '小时', samples: ['18小时', '26小时', '34小时', '42小时'], trend: 'down' },
    { name: '空域审批等待', unit: '分钟', samples: ['22分钟', '34分钟', '48分钟', '63分钟'], trend: 'down' },
  ],
};

const COMPUTER_RECYCLING_PROFILE: DomainProfile = {
  keywords: ['二手电脑回收', '检测', '报价', '数据清除', '环保流转', '质检报告'],
  domainObjects: ['回收批次', '检测工位', '数据清除证明', '估价规则', '环保流转单', '客户交接单', '质检报告'],
  departments: [
    { label: '回收运营部', responsibility: '协调上门回收、批次入库和报价确认' },
    { label: '质检估价中心', responsibility: '执行硬件检测、成色判定和估价复核' },
    { label: '合规流转组', responsibility: '留存数据清除证明并跟踪环保去向' },
  ],
  personas: [
    { role: '回收运营经理', actions: ['确认回收批次', '协调客户交接', '调整入库节奏'] },
    { role: '质检估价师', actions: ['检测硬件成色', '复核估价规则', '标注维修价值'] },
    { role: '数据清除专员', actions: ['执行擦除流程', '上传清除证明', '抽检高风险设备'] },
    { role: '环保流转专员', actions: ['登记环保去向', '核验拆解凭证', '同步合规台账'] },
  ],
  processStages: [
    { label: '回收预约', action: '确认客户设备清单与上门窗口' },
    { label: '批次入库', action: '按来源与型号完成批次分拣' },
    { label: '硬件检测', action: '检查屏幕、电池、硬盘和主板状态' },
    { label: '报价确认', action: '根据估价规则生成复核报价' },
    { label: '数据清除', action: '执行擦除并生成可审计证明' },
    { label: '环保流转', action: '将不可售设备转入合规流转链路' },
  ],
  riskTypes: [
    { label: '检测批次积压', severity: 'medium', signals: ['待检设备堆积', '报价延迟', '客户催办'] },
    { label: '高价值成色争议', severity: 'high', signals: ['屏幕暗病', '维修记录缺失', '估价复核'] },
    { label: '数据清除证明缺口', severity: 'high', signals: ['擦除日志缺失', '客户审计追问', '证明补传'] },
    { label: '环保流转凭证滞后', severity: 'medium', signals: ['拆解凭证未回传', '去向台账待补', '合规抽检'] },
    { label: '客户交接信息不全', severity: 'low', signals: ['序列号缺失', '配件未核对', '联系人变更'] },
  ],
  metricDefinitions: [
    { name: '单台检测时长', unit: '分钟', samples: ['18分钟', '24分钟', '31分钟', '39分钟'], trend: 'down' },
    { name: '报价确认率', unit: '%', samples: ['76%', '84%', '91%', '95%'], trend: 'up' },
    { name: '数据擦除通过率', unit: '%', samples: ['92%', '96%', '98%', '99%'], trend: 'up' },
    { name: '环保凭证回传率', unit: '%', samples: ['81%', '87%', '93%', '97%'], trend: 'up' },
    { name: '可再售设备占比', unit: '%', samples: ['42%', '51%', '57%', '63%'], trend: 'up' },
  ],
};

const GENERIC_PROFILE: DomainProfile = {
  keywords: ['任务管理', '流程协同', '风险处置', '指标看板', '交付闭环'],
  domainObjects: ['业务任务', '客户请求', '资源池', '审批单', '执行批次', '风险记录', '交付报告'],
  departments: [
    { label: '业务运营部', responsibility: '统筹任务排期、资源协调和交付节奏' },
    { label: '质量风控组', responsibility: '识别过程风险、复核异常并输出改进动作' },
    { label: '客户成功组', responsibility: '同步客户反馈、确认验收标准和闭环结果' },
  ],
  personas: [
    { role: '业务负责人', actions: ['拆解任务目标', '协调跨组资源', '确认交付结果'] },
    { role: '运营调度员', actions: ['调整任务排程', '同步处理进度', '追踪异常状态'] },
    { role: '质量复核员', actions: ['复核风险记录', '校验指标口径', '推动闭环整改'] },
  ],
  processStages: [
    { label: '需求识别', action: '澄清业务目标和交付边界' },
    { label: '方案设计', action: '拆解流程节点和资源计划' },
    { label: '执行跟踪', action: '按批次推进任务并同步进展' },
    { label: '风险复核', action: '复核异常并指定责任动作' },
    { label: '交付验收', action: '汇总指标并完成验收确认' },
  ],
  riskTypes: [
    { label: '关键流程延迟', severity: 'medium', signals: ['排期压缩', '责任人待确认', '交付窗口逼近'] },
    { label: '跨组信息缺口', severity: 'medium', signals: ['反馈未同步', '口径不一致', '依赖等待'] },
    { label: '验收材料缺失', severity: 'high', signals: ['附件待补', '证据链不完整', '复核退回'] },
    { label: '指标口径漂移', severity: 'low', signals: ['统计口径变化', '看板刷新延迟', '样本不足'] },
  ],
  metricDefinitions: [
    { name: '任务完成率', unit: '%', samples: ['78%', '86%', '91%', '96%'], trend: 'up' },
    { name: '异常闭环率', unit: '%', samples: ['72%', '83%', '89%', '94%'], trend: 'up' },
    { name: '平均处理时长', unit: '小时', samples: ['6小时', '9小时', '14小时', '21小时'], trend: 'down' },
    { name: '验收一次通过率', unit: '%', samples: ['68%', '79%', '87%', '93%'], trend: 'up' },
  ],
};

function hashNumber(value: string): number {
  return Number.parseInt(sha256Hex(value).slice(0, 8), 16);
}

function rotate<T>(values: T[], seed: string): T[] {
  if (!values.length) return [];
  const offset = hashNumber(seed) % values.length;
  return [...values.slice(offset), ...values.slice(0, offset)];
}

function unique(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
}

function makeId(kind: string, label: string, index: number): string {
  return `${kind}-${index + 1}-${sha256Hex(`${kind}:${label}`).slice(0, 8)}`;
}

function selectProfile(topic: string, topicKey: string, businessDescription = ''): DomainProfile {
  const source = `${topic}\n${topicKey}\n${businessDescription}`;
  if (/无人机|巡检|航线|飞手|热成像/.test(source)) return DRONE_PROFILE;
  if (/二手.*电脑|电脑.*回收|回收.*电脑|数据清除|环保流转/.test(source)) return COMPUTER_RECYCLING_PROFILE;
  return GENERIC_PROFILE;
}

function extractDescriptionTokens(topic: string, businessDescription = ''): string[] {
  const source = businessDescription || topic;
  const rawTokens = source
    .split(/[，。；、,.;&\s]+/)
    .map((token) => token.trim())
    .filter((token) => token.length >= 2 && token.length <= 12)
    .filter((token) => !/^(突出|围绕|以及|进行|管理|演示|任务|项目|流程|客户)$/.test(token));

  return unique(rawTokens).slice(0, 6);
}

function describeDomainObject(label: string, topic: string): string {
  return `${label}是${topic}演示中的核心业务对象，用于串联列表、拓扑和仿真记录。`;
}

function createDomainObjects(profile: DomainProfile, input: GenerateBusinessBlueprintInput): SemanticDomainObject[] {
  const descriptionTokens = extractDescriptionTokens(input.topic, input.businessDescription);
  const labels = unique([
    ...descriptionTokens.filter((token) => !profile.domainObjects.includes(token)).slice(0, 2),
    ...rotate(profile.domainObjects, `${input.seed}:domainObjects`),
  ]).slice(0, Math.max(5, profile.domainObjects.length));

  return labels.map((label, index) => ({
    id: makeId('domain-object', label, index),
    label,
    description: describeDomainObject(label, input.topic),
    attributes: rotate([...profile.keywords, ...descriptionTokens], `${input.seed}:domainObject:${label}`).slice(0, 3),
  }));
}

function createDepartments(profile: DomainProfile, input: GenerateBusinessBlueprintInput): SemanticDepartment[] {
  return rotate(profile.departments, `${input.seed}:departments`)
    .slice(0, Math.max(2, Math.min(profile.departments.length, 4)))
    .map((department, index) => ({
      id: makeId('department', department.label, index),
      label: department.label,
      responsibility: department.responsibility,
    }));
}

function createPersonas(
  profile: DomainProfile,
  departments: SemanticDepartment[],
  input: GenerateBusinessBlueprintInput
): SemanticPersona[] {
  const personas = rotate(profile.personas, `${input.seed}:personas`).slice(0, Math.max(3, profile.personas.length));
  const names = rotate(PERSON_NAMES, `${input.seed}:personNames`);

  return personas.map((persona, index) => ({
    id: makeId('persona', persona.role, index),
    name: names[index % names.length],
    role: persona.role,
    departmentId: departments[index % departments.length].id,
    actions: persona.actions,
  }));
}

function createProcessStages(profile: DomainProfile, input: GenerateBusinessBlueprintInput): SemanticProcessStage[] {
  return rotate(profile.processStages, `${input.seed}:stages`)
    .slice(0, Math.max(5, profile.processStages.length))
    .map((stage, index) => ({
      id: makeId('process-stage', stage.label, index),
      label: stage.label,
      sequence: index + 1,
      description: `${stage.label}阶段会${stage.action}。`,
      action: stage.action,
    }))
    .sort((left, right) => left.sequence - right.sequence);
}

function createRiskTypes(profile: DomainProfile, input: GenerateBusinessBlueprintInput): SemanticRiskType[] {
  return rotate(profile.riskTypes, `${input.seed}:riskTypes`)
    .slice(0, Math.max(4, profile.riskTypes.length))
    .map((risk, index) => ({
      id: makeId('risk-type', risk.label, index),
      label: risk.label,
      severity: risk.severity,
      description: `${risk.label}会影响${input.topic}的关键节点，需要在仿真中解释风险进展和处置结果。`,
      riskSignals: risk.signals,
    }));
}

function createMetricDefinitions(
  profile: DomainProfile,
  input: GenerateBusinessBlueprintInput
): SemanticMetricDefinition[] {
  return rotate(profile.metricDefinitions, `${input.seed}:metrics`)
    .slice(0, Math.max(4, profile.metricDefinitions.length))
    .map((metric, index) => ({
      id: makeId('metric-definition', metric.name, index),
      name: metric.name,
      description: `${metric.name}用于衡量${input.topic}在主演示链路中的业务成效。`,
      unit: metric.unit,
      valueSamples: rotate(metric.samples, `${input.seed}:metric:${metric.name}`),
      trend: metric.trend,
    }));
}

function createStoryBeats(input: {
  blueprintInput: GenerateBusinessBlueprintInput;
  domainObjects: SemanticDomainObject[];
  departments: SemanticDepartment[];
  personas: SemanticPersona[];
  processStages: SemanticProcessStage[];
  riskTypes: SemanticRiskType[];
  metricDefinitions: SemanticMetricDefinition[];
}): SemanticStoryBeat[] {
  const count = Math.max(1, Math.floor(input.blueprintInput.projectCount));
  const storyBeats: SemanticStoryBeat[] = [];

  for (let index = 0; index < count; index += 1) {
    const domainObject = input.domainObjects[index % input.domainObjects.length];
    const stage = input.processStages[index % input.processStages.length];
    const persona = input.personas[index % input.personas.length];
    const department = input.departments[index % input.departments.length];
    const riskType = input.riskTypes[index % input.riskTypes.length];
    const metricA = input.metricDefinitions[index % input.metricDefinitions.length];
    const metricB = input.metricDefinitions[(index + 1) % input.metricDefinitions.length];

    storyBeats.push({
      id: makeId('story-beat', `${domainObject.label}-${stage.label}-${index}`, index),
      title: `${domainObject.label}${stage.label}处置`,
      summary: `${persona.role}${persona.name}在${department.label}牵头${stage.action}，重点跟踪${domainObject.label}的${riskType.label}并用${metricA.name}验证处置效果。`,
      domainObjectId: domainObject.id,
      departmentId: department.id,
      personaId: persona.id,
      processStageId: stage.id,
      riskTypeId: riskType.id,
      metricDefinitionIds: unique([metricA.id, metricB.id]),
      outcome: `${domainObject.label}在${stage.label}阶段形成可解释的${metricA.name}变化和风险闭环记录。`,
    });
  }

  return storyBeats;
}

export function generateDeterministicBusinessBlueprint(input: GenerateBusinessBlueprintInput): BusinessBlueprint {
  const profile = selectProfile(input.topic, input.topicKey, input.businessDescription);
  const descriptionTokens = extractDescriptionTokens(input.topic, input.businessDescription);
  const domainObjects = createDomainObjects(profile, input);
  const departments = createDepartments(profile, input);
  const personas = createPersonas(profile, departments, input);
  const processStages = createProcessStages(profile, input);
  const riskTypes = createRiskTypes(profile, input);
  const metricDefinitions = createMetricDefinitions(profile, input);
  const storyBeats = createStoryBeats({
    blueprintInput: input,
    domainObjects,
    departments,
    personas,
    processStages,
    riskTypes,
    metricDefinitions,
  });

  return {
    schemaVersion: 1,
    topic: input.topic,
    businessDescription: input.businessDescription,
    topicKey: input.topicKey,
    seed: input.seed,
    contractFingerprint: input.contractFingerprint,
    generatorVersion: input.generatorVersion,
    industry: {
      name: input.topic,
      keywords: unique([...profile.keywords, ...descriptionTokens, input.topic, input.topicKey]).slice(0, 10),
    },
    domainObjects,
    departments,
    personas,
    processStages,
    riskTypes,
    metricDefinitions,
    storyBeats,
  };
}
