import type { IndustryDataDraft } from '../types.js';
import type {
  BusinessBlueprint,
  SemanticAnchorBinding,
  SemanticAnchorRef,
  SemanticDepartment,
  SemanticDomainObject,
  SemanticMetricDefinition,
  SemanticPersona,
  SemanticProcessStage,
  SemanticRiskType,
  SemanticStoryBeat,
} from './types.js';

export interface CompileBlueprintToIndustryDraftInput {
  blueprint: BusinessBlueprint;
  scenarioId: string;
  scenarioName: string;
  projectCount: number;
}

export interface BlueprintDraftCompileResult {
  draft: IndustryDataDraft;
  bindings: SemanticAnchorBinding[];
}

const REGIONS = ['华东区域', '华南区域', '西南区域', '华北区域', '华中区域', '京津冀区域'];

function findById<T extends { id: string }>(values: T[], id: string, fallbackIndex: number): T {
  return values.find((value) => value.id === id) ?? values[fallbackIndex % values.length];
}

function metricValue(metric: SemanticMetricDefinition, projectIndex: number, metricIndex: number): string {
  return metric.valueSamples[(projectIndex + metricIndex) % metric.valueSamples.length] ?? `${80 + projectIndex}%`;
}

function metricTrend(metric: SemanticMetricDefinition, risk: SemanticRiskType): string {
  if (risk.severity === 'high' && metric.trend === 'up') return 'flat';
  return metric.trend ?? (risk.severity === 'high' ? 'down' : 'up');
}

function anchor(label: string, id: string, type: SemanticAnchorRef['type']): SemanticAnchorRef {
  return { type, id, label };
}

function projectAnchors(input: {
  storyBeat: SemanticStoryBeat;
  domainObject: SemanticDomainObject;
  department: SemanticDepartment;
  persona: SemanticPersona;
  stage: SemanticProcessStage;
  risk: SemanticRiskType;
  metrics: SemanticMetricDefinition[];
}): SemanticAnchorRef[] {
  return [
    anchor(input.storyBeat.title, input.storyBeat.id, 'storyBeat'),
    anchor(input.domainObject.label, input.domainObject.id, 'domainObject'),
    anchor(`${input.persona.role}-${input.persona.name}`, input.persona.id, 'persona'),
    anchor(input.stage.label, input.stage.id, 'processStage'),
    anchor(input.risk.label, input.risk.id, 'riskType'),
    ...input.metrics.map((metric) => anchor(metric.name, metric.id, 'metricDefinition')),
  ];
}

function pushSupportingBinding(input: {
  bindings: SemanticAnchorBinding[];
  recordPath: string;
  recordKey: string;
  module: 'project' | 'simulation';
  anchors: SemanticAnchorRef[];
}): void {
  input.bindings.push({
    recordKind: 'supporting',
    recordPath: input.recordPath,
    recordKey: input.recordKey,
    module: input.module,
    anchors: input.anchors,
  });
}

function createSimulationMessages(input: {
  storyBeat: SemanticStoryBeat;
  domainObject: SemanticDomainObject;
  persona: SemanticPersona;
  stage: SemanticProcessStage;
  risk: SemanticRiskType;
  metrics: SemanticMetricDefinition[];
  projectIndex: number;
}): string[] {
  const [primaryMetric, secondaryMetric] = input.metrics;
  return [
    `${input.persona.role}${input.persona.name}正在${input.stage.action}，${input.domainObject.label}已进入${input.stage.label}跟踪窗口。`,
    `${input.risk.label}出现${input.risk.riskSignals[0]}信号，${input.persona.role}需要复核${input.domainObject.label}的处置优先级。`,
    `${primaryMetric.name}当前为${metricValue(primaryMetric, input.projectIndex, 0)}，${secondaryMetric.name}同步记录为${metricValue(
      secondaryMetric,
      input.projectIndex,
      1
    )}。`,
    `${input.storyBeat.outcome}`,
  ];
}

function createSimulationEvents(input: {
  domainObject: SemanticDomainObject;
  persona: SemanticPersona;
  stage: SemanticProcessStage;
  risk: SemanticRiskType;
  metric: SemanticMetricDefinition;
  projectIndex: number;
}): string[] {
  return [
    `${input.stage.label}推进：${input.persona.role}${input.persona.name}${input.stage.action}，${input.domainObject.label}状态已同步。`,
    `${input.risk.label}处置：${input.persona.role}根据${input.risk.riskSignals[0]}更新风险等级和责任动作。`,
    `${input.metric.name}更新：${input.domainObject.label}记录${metricValue(input.metric, input.projectIndex, 0)}，进入下一轮复核。`,
  ];
}

export function compileBlueprintToIndustryDraft(
  input: CompileBlueprintToIndustryDraftInput
): BlueprintDraftCompileResult {
  const blueprint = input.blueprint;
  const projectCount = Math.min(Math.max(1, Math.floor(input.projectCount)), blueprint.storyBeats.length);
  const bindings: SemanticAnchorBinding[] = [];
  let messageOffset = 0;
  let alarmOffset = 0;
  let faultOffset = 0;
  let eventOffset = 0;

  const projects: IndustryDataDraft['projects'] = blueprint.storyBeats.slice(0, projectCount).map((storyBeat, index) => {
    const domainObject = findById(blueprint.domainObjects, storyBeat.domainObjectId, index);
    const department = findById(blueprint.departments, storyBeat.departmentId, index);
    const persona = findById(blueprint.personas, storyBeat.personaId, index);
    const stage = findById(blueprint.processStages, storyBeat.processStageId, index);
    const risk = findById(blueprint.riskTypes, storyBeat.riskTypeId, index);
    const metrics = storyBeat.metricDefinitionIds
      .map((metricId, metricIndex) => findById(blueprint.metricDefinitions, metricId, index + metricIndex))
      .slice(0, 3);
    const anchors = projectAnchors({ storyBeat, domainObject, department, persona, stage, risk, metrics });
    const key = `${blueprint.topicKey}-${index + 1}`;
    const messages = createSimulationMessages({ storyBeat, domainObject, persona, stage, risk, metrics, projectIndex: index });
    const events = createSimulationEvents({
      domainObject,
      persona,
      stage,
      risk,
      metric: metrics[0],
      projectIndex: index,
    });
    const alarmCount = 1;
    const faultCount = risk.severity === 'high' ? 1 : 0;
    const supportPaths = [
      `project.versions[${index}]`,
      `project.topologies[${index}]`,
      `simulation.sessions[${index}]`,
      ...messages.map((_, messageIndex) => `simulation.messages[${messageOffset + messageIndex}]`),
      `simulation.alarms[${alarmOffset}]`,
      ...Array.from({ length: faultCount }, (_, faultIndex) => `simulation.faults[${faultOffset + faultIndex}]`),
      ...events.map((_, eventIndex) => `simulation.events[${eventOffset + eventIndex}]`),
    ];

    bindings.push({
      recordKind: 'primary',
      recordPath: `project.projects[${index}]`,
      recordKey: key,
      module: 'project',
      anchors,
      supports: supportPaths,
    });
    pushSupportingBinding({
      bindings,
      recordPath: `project.versions[${index}]`,
      recordKey: `${key}-version-1`,
      module: 'project',
      anchors,
    });
    pushSupportingBinding({
      bindings,
      recordPath: `project.topologies[${index}]`,
      recordKey: `${key}-topology-1`,
      module: 'project',
      anchors,
    });
    pushSupportingBinding({
      bindings,
      recordPath: `simulation.sessions[${index}]`,
      recordKey: `${key}-session-1`,
      module: 'simulation',
      anchors,
    });
    messages.forEach((_, messageIndex) =>
      pushSupportingBinding({
        bindings,
        recordPath: `simulation.messages[${messageOffset + messageIndex}]`,
        recordKey: `${key}-message-${messageIndex + 1}`,
        module: 'simulation',
        anchors,
      })
    );
    pushSupportingBinding({
      bindings,
      recordPath: `simulation.alarms[${alarmOffset}]`,
      recordKey: `${key}-alarm-1`,
      module: 'simulation',
      anchors,
    });
    if (risk.severity === 'high') {
      pushSupportingBinding({
        bindings,
        recordPath: `simulation.faults[${faultOffset}]`,
        recordKey: `${key}-fault-1`,
        module: 'simulation',
        anchors,
      });
    }
    events.forEach((_, eventIndex) =>
      pushSupportingBinding({
        bindings,
        recordPath: `simulation.events[${eventOffset + eventIndex}]`,
        recordKey: `${key}-event-${eventIndex + 1}`,
        module: 'simulation',
        anchors,
      })
    );

    messageOffset += messages.length;
    alarmOffset += alarmCount;
    faultOffset += faultCount;
    eventOffset += events.length;

    return {
      key,
      name: storyBeat.title.endsWith('处置') ? `${storyBeat.title}专项` : storyBeat.title,
      region: REGIONS[index % REGIONS.length],
      stage: stage.label,
      departmentName: department.label,
      ownerRole: persona.role,
      ownerName: persona.name,
      riskLevel: risk.severity,
      risk: `${risk.label}：${risk.description}当前信号为${risk.riskSignals[0]}，影响${domainObject.label}在${stage.label}阶段的处置节奏。`,
      remark: storyBeat.summary,
      keyMetrics: metrics.map((metric, metricIndex) => ({
        name: metric.name,
        value: metricValue(metric, index, metricIndex),
        trend: metricTrend(metric, risk),
      })),
      versions: [
        {
          name: `${domainObject.label}${stage.label}语义演示版`,
          locked: true,
          summary: `${department.label}围绕${domainObject.label}在${stage.label}阶段形成${storyBeat.outcome}`,
        },
      ],
      topology: {
        nodes: [
          { name: `${domainObject.label}入口`, type: 'domain-object', status: 'active' },
          { name: `${stage.label}节点`, type: 'process-stage', status: risk.severity === 'high' ? 'warning' : 'active' },
          { name: `${persona.role}处理`, type: 'persona-action', status: 'active' },
          { name: `${risk.label}监控`, type: 'risk-control', status: risk.severity === 'low' ? 'active' : 'warning' },
        ],
        links: [
          { source: `${domainObject.label}入口`, target: `${stage.label}节点`, label: stage.action },
          { source: `${stage.label}节点`, target: `${persona.role}处理`, label: persona.actions[index % persona.actions.length] },
          { source: `${persona.role}处理`, target: `${risk.label}监控`, label: metrics[0].name },
        ],
      },
      simulation: {
        status: risk.severity === 'high' ? 'running' : risk.severity === 'medium' ? 'paused' : 'completed',
        messages,
        alarms: [
          {
            severity: risk.severity,
            message: `${risk.label}告警：${risk.riskSignals.join('、')}，${persona.role}需围绕${domainObject.label}完成处置说明。`,
          },
        ],
        events,
      },
    };
  });

  return {
    draft: {
      industry: {
        id: blueprint.topicKey,
        name: blueprint.industry.name,
        keywords: [...blueprint.industry.keywords, ...blueprint.domainObjects.map((item) => item.label)],
      },
      scenario: {
        id: input.scenarioId,
        name: input.scenarioName,
        version: '1.0.0',
        seed: blueprint.seed,
        description: blueprint.businessDescription || blueprint.topic,
      },
      projects,
    },
    bindings,
  };
}
