import { realEstateP0AcceptanceDemoScenario } from './real-estate-p0-acceptance-demo';
import type {
  DemoProject,
  DemoProjectVersion,
  DemoScenarioPackage,
  DemoSimulationBandwidth,
  DemoSimulationEvent,
  DemoSimulationFault,
  DemoSimulationFrame,
  DemoSimulationMessage,
  DemoSimulationAlarm,
  DemoSimulationSession,
  DemoTopology,
} from '../schema';
import { DEMO_SCENARIO_SCHEMA_VERSION } from '../schema';

const baseTeam = '军工软件项目交付与质量管理演示团队';
const INDUSTRY = 'defense-sw-delivery-qm';
const INDUSTRY_NAME = '军工软件项目交付与质量管理';

type RiskLevel = 'high' | 'medium' | 'low';

interface SwSpec {
  projectId: number;
  versionId: number;
  projectCode: string;
  rndDirectionLabel: string;
  orgLineLabel: string;
  projectName: string;
  themesLabel: string;
  owner: string;
  department: string;
  businessStage: string;
  progress: string;
  background: string;
  mainRisk: string;
  handling: string;
  riskLevel: RiskLevel;
  keyMetrics: { name: string; value: string; trend: string }[];
  topologyEntry: string;
  topologyStage: string;
  topologyRiskMonitor: string;
  alarmTopic: string;
  sessionStatus: string;
  scenarioStage: string;
  includeFault: boolean;
  faultStatus?: string;
}

const SPECS: SwSpec[] = [
  {
    projectId: 7361,
    versionId: 8361,
    projectCode: 'DEF-SW-C2ISR-081',
    rndDirectionLabel: '指挥控制应用软件（CSCI）',
    orgLineLabel: '总体设计所｜指挥控制软件工程专业部牵总／军方质量监督代表列席',
    projectName:
      '编队级指挥决策支持软件跨平台移植与入网鉴定试验收口及交付准备',
    themesLabel:
      '指挥控制软件：任务线程实时性复核、交战规则配置受控与联试归零',
    owner: '主任设计师-褚江澜',
    department: '指挥控制软件工程专业部',
    businessStage: 'CSCI联试入网与归零验证',
    progress:
      '第三方测评缺陷清单已收口至残余 4 条且均带归零报告；仿真对抗科目三轮通过，静待「配置管理基线—发布包」封存审批。',
    background:
      '指挥链软件须在异构国产化计算环境下保持战术级响应指标，入网前须完成密钥注入、交战规则与安全策略一致性和场景回归全覆盖。',
    mainRisk:
      '实时调度偶发优先级反转导致链路抖动未被完全覆盖；封存前若未及时冻结第三方库条目，将影响鉴定试验结论可追溯性。',
    handling:
      '褚江澜组织线程模型再走查与长稳压试验，配置管理员执行库清单「双岗比对」，质量师补充鉴定符合性举证目录。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '需求可追溯闭合率', value: '97.8%', trend: 'up' },
      { name: '联试重大问题归零周期', value: '6.2 天', trend: 'down' },
    ],
    topologyEntry: '指挥链路任务调度与交战规则注入入口',
    topologyStage: 'CSCI联试入网与归零节点',
    topologyRiskMonitor: '实时性与配置基线受控复核',
    alarmTopic:
      '夜航压测中指挥线程偶发优先级抢占异常告警增加，需在封存前补齐「最坏情况序列」回放证据包。',
    sessionStatus: 'running',
    scenarioStage: '联试联调',
    includeFault: true,
    faultStatus: 'processing',
  },
  {
    projectId: 7362,
    versionId: 8371,
    projectCode: 'DEF-SW-SIMTB-082',
    rndDirectionLabel: '战术级半实物仿真训练软件',
    orgLineLabel: '仿真试验中心｜训练运用处联合见证',
    projectName:
      '合成营战术推演半实物仿真训练平台软件定型试验与数据采集一致性专项',
    themesLabel:
      '仿真训练系统：工况脚本受控、设备驱动联试与教员台缺陷闭环',
    owner: '仿真分系统总师-苏景明',
    department: '半实物仿真与数字孪生室',
    businessStage: '定型试验数据采集双通道校核',
    progress:
      '驱动桩与实物目标源同步误差已校准至阈值内；教员台回放「课目 14」发现 2 帧不同步脚本已回溯至配置管理库特定变更单。',
    background:
      '训练平台须在强电磁干扰科目下保持一致的数据采集链路，仿真软件与工况脚本均需纳入军工软件质量管理体系双岗配置审查。',
    mainRisk:
      '数据采集双通道偶有丢包将导致试验结论争议；教员台离线脚本与用户现场手工改动存在版本分叉风险。',
    handling:
      '苏景明固化「脚本—驱动—数据采集」三位一体签出策略，质检组增加 CRC 快照比对，重大缺陷归零前禁止覆盖发布目录。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '工况脚本一致性校核通过率', value: '99.4%', trend: 'flat' },
      { name: '硬件在环回放一致率', value: '98.1%', trend: 'up' },
    ],
    topologyEntry: '半实物耦合与数据采集入口',
    topologyStage: '定型试验双通道校核节点',
    topologyRiskMonitor: '工况脚本分叉与回放漂移监控',
    alarmTopic:
      '硬件在环比对显示第二通道帧序号跳变，教员台告警建议暂停后续课目直至驱动桩版本回滚确认。',
    sessionStatus: 'running',
    scenarioStage: '仿真联试',
    includeFault: true,
    faultStatus: 'investigating',
  },
  {
    projectId: 7363,
    versionId: 8381,
    projectCode: 'DEF-SW-MPLOS-083',
    rndDirectionLabel: '任务规划与地面站应用软件',
    orgLineLabel: '任务规划条线｜飞试规划室与质量体系联合审查',
    projectName:
      '跨区域多目标任务筹划与地面站装订软件需求基线与接口控制文件收口专项',
    themesLabel:
      '任务规划软件：需求双轨追溯、界面冻结与装订数据完整性验证',
    owner: '软件负责人-霍思齐',
    department: '任务规划与地面站软件室',
    businessStage: '需求评审后基线冻结与接口控制落实',
    progress:
      'ICD-V3.4 与用户代表会签闭环；装订数据校验脚本已迁入受控构建管线，下一轮飞前桌面推演定于周五。',
    background:
      '任务规划链路涉及装订数据多源汇入，任一字段歧义都会造成「飞不起来」的工程事故，必须在研制阶段压实需求与接口条目。',
    mainRisk:
      '装订字段与 ICD 注释存在两处语义冲突；跨部门复核节奏若滞后，将影响联试准入审查节点。',
    handling:
      '霍思齐组织需求矛盾矩阵「红蓝对抗」评审一天内闭合，质量保证工程师更新双向追溯矩阵并锁定 UI 原型冻结标签。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '需求条目双岗确认率', value: '100%', trend: 'flat' },
      { name: 'ICD闭环周期', value: '2.8 周', trend: 'down' },
    ],
    topologyEntry: '任务筹划与装订数据入口',
    topologyStage: '基线冻结与接口控制核对节点',
    topologyRiskMonitor: '需求语义冲突与追溯断链监控',
    alarmTopic:
      '自动化校验报告提示两类装订字段在用户侧沙箱仍存在历史脏数据，需在联试准入前清零并附验证记录。',
    sessionStatus: 'paused',
    scenarioStage: '需求与配置',
    includeFault: false,
  },
  {
    projectId: 7364,
    versionId: 8391,
    projectCode: 'DEF-SW-PHMG-084',
    rndDirectionLabel: '装备健康管理（PHM）地面分析软件',
    orgLineLabel: '服务保障工程部｜承制单位质量体系年度监督抽查配合',
    projectName:
      '主战平台装备健康管理地面分析与寿命预测算法软件定型审查前复核',
    themesLabel:
      '装备健康管理平台：模型版本受控、健康指数口径一致性与告警门限审定',
    owner: '专业副总师-蔺承泽',
    department: 'PHM与地面保障软件室',
    businessStage: '定型审查前独立验证与残余风险报批',
    progress:
      '寿命预测模型的训练数据边界已重写说明材料；告警门限与装备履历系统的映射表经由「双台账」校对完成。',
    background:
      'PHM结论直接影响保障决策，须在定型关口前厘清模型可信度边界，避免告警虚警淹没关键故障特征。',
    mainRisk:
      '训练数据集存在场景覆盖缺口可能导致模型外推告警失真；告警门限未与履历系统对齐或引发误报舆情。',
    handling:
      '蔺承泽报批残余风险并接受独立验证抽样，质量保证室补充模型适用域声明与用户提示语，告警策略走变更控制委员会。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '告警虚警压降率（对比基线）', value: '−42%', trend: 'up' },
      { name: '模型版本可追溯条目', value: '186 条', trend: 'up' },
    ],
    topologyEntry: '健康分析与寿命预测流水线入口',
    topologyStage: '定型审查前置独立验证节点',
    topologyRiskMonitor: '告警门限与适用域漂移监控',
    alarmTopic:
      '对比试验显示某型传感器特征在低温段的残差偏大，需在定型材料中单列残余风险与用户提示。',
    sessionStatus: 'paused',
    scenarioStage: '质量评审',
    includeFault: true,
    faultStatus: 'processing',
  },
  {
    projectId: 7365,
    versionId: 8401,
    projectCode: 'DEF-SW-LINKMG-085',
    rndDirectionLabel: '战术数据链监视告警软件',
    orgLineLabel: '数据链系统工程部｜基地联试分队驻场协同',
    projectName:
      '战术数据链链路监视告警与拓扑呈现软件配置项冻结与入网参数校核专项',
    themesLabel:
      '数据链监控软件：入网参数对齐、拓扑缓存一致性与告警风暴抑制策略',
    owner: '技术负责人-易舒扬',
    department: '数据链与波形软件研究室',
    businessStage: '配置项冻结与入网参数对齐',
    progress:
      '冻结标签「FC-0512」已挂接至源码与二进制双签名；入网参数与用户侧离线库完成首轮差异 Diff，仅存 7 条待用户代表确认。',
    background:
      '链路监视告警直接支撑作战态势判断，入网前须确保参数与用户侧完全一致，拓扑缓存错误会导致虚警链路指向错误节点。',
    mainRisk:
      '冻结后若开发人员私拉分支修补将破坏鉴定结论；入网参数与用户侧离线库时差导致重复告警。',
    handling:
      '易舒扬执行代码仓只读快照与二进制指纹固化，质量保证工程师建立参数 Diff 周报机制，告警抑制策略须经配置控制委员会条目化。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '配置项一致性抽查通过率', value: '96%', trend: 'up' },
      { name: '告警风暴峰值（条/秒）', value: '≤12', trend: 'down' },
    ],
    topologyEntry: '链路与拓扑数据源入口',
    topologyStage: '配置冻结与入网参数校核节点',
    topologyRiskMonitor: '拓扑缓存错位与告警洪泛监控',
    alarmTopic:
      '训练网回放出现同一告警 ID 在 800ms 内重复触发三百余次，判定为抑制脚本未挂载，须在冻结前复检。',
    sessionStatus: 'running',
    scenarioStage: '配置受控',
    includeFault: true,
    faultStatus: 'closed',
  },
  {
    projectId: 7366,
    versionId: 8411,
    projectCode: 'DEF-SW-TEDRPT-086',
    rndDirectionLabel: '试飞试验自动判读与报告生成软件',
    orgLineLabel: '试飞测试技术部｜型号办公室与质量体系联合签收',
    projectName:
      '靶场多源遥测试飞数据自动判读与鉴定试验报告草稿生成软件交付冲刺',
    themesLabel:
      '试验数据判读系统：判读规则可追溯、图表模板签批与归档介质完整性',
    owner: '项目质量师-闵若昀',
    department: '试验测试与数据处理中心',
    businessStage: '交付验收试飞数据闭环与归档',
    progress:
      '判读脚本与鉴定试验科目的映射表已定稿并双签；自动生成报告模版通过保密审查，仅存介质封签与离线校验两项待收口。',
    background:
      '判读链路覆盖多型号遥测包格式，试飞节奏紧，任何「判读漂移」都会造成试验结论重写，必须与缺陷归零和配置统一管理。',
    mainRisk:
      '模版字段与最新试验纪实存在版本滞后可能导致报告返工；归档介质哈希校验链路若断裂影响交付追溯。',
    handling:
      '闵若昀串联型号办与数据处理岗完成「试飞日清」条目，质量保证室执行模版—判读脚本—原始数据三位一体指纹比对。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '判读一次通过率（科目级）', value: '93%', trend: 'up' },
      { name: '报告返工工时（人日）', value: '−28%', trend: 'down' },
    ],
    topologyEntry: '多源试飞遥测入库与规则引擎入口',
    topologyStage: '交付验收试飞数据归档节点',
    topologyRiskMonitor: '判读规则漂移与模版版本监控',
    alarmTopic:
      '沙箱回放显示两份遥测载荷解析规则版本号不一致，可能引发同架次两份报告的矛盾结论，需在交付冻结前统一到规则包 R-090。',
    sessionStatus: 'archived_review',
    scenarioStage: '交付验收',
    includeFault: false,
  },
];

const SEED =
  'defense-sw-delivery-qm-b4d8e7016e3c4cf6a912d5e801c90def';

function sessionIdFor(pid: number) {
  return `defense-sw-qm-session-${pid}-1`;
}

function buildProjects(now: Date): DemoProject[] {
  return SPECS.map((s) => ({
    projectId: s.projectId,
    projectName: s.projectName,
    projectCode: s.projectCode,
    projectDesc: s.background,
    description: `${s.mainRisk} 当前阶段：${s.businessStage}。${s.handling}`,
    status: '0' as const,
    createTime: new Date(now.getTime() - 12 * 24 * 60 * 60 * 1000).toISOString(),
    updateTime: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(),
    remark: `${s.handling} 最近一次质量管理体系双周例会由 ${s.owner} 汇报并形成质量行动项闭环。`,
    owner: s.owner,
    department: s.department,
    createBy: `${s.department}-科研项目统筹`,
    updateBy: s.owner.split('-').pop() ?? s.owner,
    industry: INDUSTRY,
    industryName: INDUSTRY_NAME,
    region: s.orgLineLabel,
    stallCategory: s.rndDirectionLabel,
    businessStage: s.businessStage,
    operationTheme: s.themesLabel,
    progressOverview: s.progress,
    dominantRisk: s.mainRisk,
    keyMetrics: s.keyMetrics,
    riskLevel: s.riskLevel,
  }));
}

function buildVersions(now: Date): DemoProjectVersion[] {
  return SPECS.map((s) => ({
    versionId: s.versionId,
    projectId: s.projectId,
    versionNumber: `${s.projectCode}-V1.0`,
    versionName: `${s.projectName}（${s.businessStage}）离线演示拓扑基线`,
    description: `${baseTeam}依托${s.rndDirectionLabel}研制主线，贯通「立项—研制—试验—归零—评审—交付」质量记录，离线打包告警、缺陷与试飞（联试）状态机用于交付展示。`,
    locked: true,
    isLocked: '1',
    status: '0',
    createTime: new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updateTime: now.toISOString(),
    createBy: baseTeam,
    updateBy: s.owner.replace(/^.*?-/u, ''),
    remark: s.progress,
  }));
}

function buildTopologies(now: Date): DemoTopology[] {
  return SPECS.map((s) => ({
    id: `defense-sw-qm-topology-${s.projectId}`,
    projectId: s.projectId,
    versionId: s.versionId,
    updateTime: now.toISOString(),
    graph: {
      nodes: [
        {
          id: `def-sw-${s.projectId}-n1`,
          label: s.topologyEntry,
          type: 'domain-object',
          status: 'active',
        },
        {
          id: `def-sw-${s.projectId}-n2`,
          label: s.topologyStage,
          type: 'process-stage',
          status: 'warning',
        },
        {
          id: `def-sw-${s.projectId}-n3`,
          label: `${s.owner}闭环`,
          type: 'persona-action',
          status: 'active',
        },
        {
          id: `def-sw-${s.projectId}-n4`,
          label: s.topologyRiskMonitor,
          type: 'risk-control',
          status: s.riskLevel === 'high' ? 'warning' : 'active',
        },
      ],
      edges: [
        {
          id: `def-sw-${s.projectId}-e1`,
          source: s.topologyEntry,
          target: s.topologyStage,
          label: `研制进展摘录：${s.progress.slice(0, 26)}`,
        },
        {
          id: `def-sw-${s.projectId}-e2`,
          source: s.topologyStage,
          target: `${s.owner}闭环`,
          label: '缺陷归零与技术状态核实',
        },
        {
          id: `def-sw-${s.projectId}-e3`,
          source: `${s.owner}闭环`,
          target: s.topologyRiskMonitor,
          label: `${s.keyMetrics[0]?.name ?? '核心质量指标'} 跟踪`,
        },
      ],
    },
  }));
}

function buildSessions(now: Date): DemoSimulationSession[] {
  return SPECS.map((s) => ({
    sessionId: sessionIdFor(s.projectId),
    projectId: s.projectId,
    versionId: s.versionId,
    status: s.sessionStatus,
    createTime: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
    updateTime: now.toISOString(),
    scenarioStage: s.scenarioStage,
    riskLevel: s.riskLevel,
    rndDirection: s.rndDirectionLabel,
    orgSnapshot: s.orgLineLabel,
  }));
}

function buildAlarms(now: Date): DemoSimulationAlarm[] {
  return SPECS.map((s) => ({
    alarmId: `${sessionIdFor(s.projectId)}-alarm-1`,
    sessionId: sessionIdFor(s.projectId),
    timestamp: new Date(now.getTime() - 2680000).toISOString(),
    severity: s.riskLevel,
    status: s.sessionStatus === 'archived_review' ? 'closed' : 'open',
    title: `${s.projectName.slice(0, 22)}`,
    subsystem: s.rndDirectionLabel,
    message: `【${s.scenarioStage}丨${s.projectCode}】${s.alarmTopic} 技术状态负责人：${s.owner}（${s.department}）。`,
  }));
}

function buildFaults(now: Date): DemoSimulationFault[] {
  return SPECS.filter((s) => s.includeFault).map((s) => ({
    faultId: `${sessionIdFor(s.projectId)}-fault-1`,
    sessionId: sessionIdFor(s.projectId),
    timestamp: new Date(now.getTime() - 2460000).toISOString(),
    faultType: s.scenarioStage,
    subsystem: s.rndDirectionLabel,
    description: `质量关注点：${s.mainRisk} 当前归零或处置路径：${s.handling}`,
    status: s.faultStatus ?? 'processing',
    trackingCode: `${s.projectCode}-FR-${String(s.projectId).slice(-2)}`,
  }));
}

function buildEvents(now: Date): DemoSimulationEvent[] {
  const out: DemoSimulationEvent[] = [];
  for (const s of SPECS) {
    const sid = sessionIdFor(s.projectId);
    out.push(
      {
        eventId: `${sid}-event-1`,
        sessionId: sid,
        triggerTime: new Date(now.getTime() - 5400000).toISOString(),
        eventType: s.scenarioStage,
        stageLabel: s.businessStage,
        message: `【研制推进】${s.owner}组织完成「${s.topologyStage}」条目核对：软件构建标识、交付数据库与第三方测评记录已对位。`,
      },
      {
        eventId: `${sid}-event-2`,
        sessionId: sid,
        triggerTime: new Date(now.getTime() - 5190000).toISOString(),
        eventType: s.scenarioStage,
        stageLabel: s.businessStage,
        message: `【风险评估】对照 ${s.mainRisk.slice(0, 42)}… 风险等级调整为「${s.riskLevel === 'high' ? '所级重点督办' : '项目级例行跟踪'}」。`,
      },
      {
        eventId: `${sid}-event-3`,
        sessionId: sid,
        triggerTime: new Date(now.getTime() - 4980000).toISOString(),
        eventType: s.scenarioStage,
        stageLabel: s.businessStage,
        message: `【质量度量】《${s.keyMetrics[0].name}》报出 ${s.keyMetrics[0].value}，记入型号质量月报离线演示链路。`,
      }
    );
  }
  return out;
}

function buildMessages(now: Date): DemoSimulationMessage[] {
  const out: DemoSimulationMessage[] = [];
  const sevs: Array<'high' | 'medium' | 'low'> = SPECS.map((s) =>
    s.riskLevel === 'high' ? 'high' : 'medium'
  );
  for (let i = 0; i < SPECS.length; i++) {
    const s = SPECS[i];
    const sid = sessionIdFor(s.projectId);
    const severity = sevs[i];
    out.push(
      {
        id: `${sid}-msg-1`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5560000).toISOString(),
        role: 'system',
        content: `质量态势感知：会话「${sid}」已绑定 ${s.projectCode}，研制的 ${s.rndDirectionLabel} 处于 ${s.businessStage}，责任 ${s.owner}。`,
        severity,
      },
      {
        id: `${sid}-msg-2`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5535000).toISOString(),
        role: 'operator',
        content: `${s.owner}：最新进展摘要——${s.progress}`,
        severity,
      },
      {
        id: `${sid}-msg-3`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5510000).toISOString(),
        role: 'system',
        content: `质量指标快照（${INDUSTRY_NAME}）：${s.keyMetrics.map((m) => `${m.name} ${m.value}`).join('；')}。`,
        severity,
      },
      {
        id: `${sid}-msg-4`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5485000).toISOString(),
        role: 'operator',
        content: `归零与纠正措施：${s.handling}`,
        severity,
      }
    );
  }
  return out;
}

function buildBandwidth(now: Date): DemoSimulationBandwidth[] {
  let inbound = 48;
  return SPECS.map((s, i) => ({
    id: `${sessionIdFor(s.projectId)}-bw-1`,
    sessionId: sessionIdFor(s.projectId),
    portId: `def-sw-telem-port-${s.projectId}`,
    timestamp: new Date(now.getTime() - (6 - i) * 280000).toISOString(),
    inboundMbps: (inbound += 4 + i * 2),
    outboundMbps: 22 + i * 4,
    utilization: Math.min(
      0.94,
      0.55 + (((i + 3) % 5) / 18) + (s.riskLevel === 'high' ? 0.06 : 0)
    ),
    note: `${s.rndDirectionLabel}联试／遥测数据汇聚链路`,
  }));
}

function buildFrames(): DemoSimulationFrame[] {
  return SPECS.map((s) => ({
    frameId: `${sessionIdFor(s.projectId)}-frame-summary`,
    sessionId: sessionIdFor(s.projectId),
    order: 1,
    type: 'summary',
    delayMs: 220,
    payload: {
      projectName: s.projectName,
      projectCode: s.projectCode,
      stage: s.businessStage,
      riskLevel: s.riskLevel,
      subsystem: s.rndDirectionLabel,
      orgLine: s.orgLineLabel,
    },
  }));
}

export function composeDefenseSoftwareDeliveryQmDemoScenario(
  referenceTimeIso?: string
): DemoScenarioPackage {
  const now = referenceTimeIso ? new Date(referenceTimeIso) : new Date();
  const base = realEstateP0AcceptanceDemoScenario;
  const auth = structuredClone(base.auth);
  const system = structuredClone(base.system);

  return {
    schemaVersion: DEMO_SCENARIO_SCHEMA_VERSION,
    scenario: {
      id: 'defense-software-delivery-qm-demo',
      name: '军工软件项目交付与质量管理',
      version: '1.0.0',
      fingerprint: 'defense-sw-delivery-qm-demo-u8q4',
      seed: SEED,
    },
    auth,
    system,
    project: {
      projects: buildProjects(now) as DemoProject[],
      versions: buildVersions(now) as DemoProjectVersion[],
      topologies: buildTopologies(now),
    },
    simulation: {
      sessions: buildSessions(now) as DemoSimulationSession[],
      messages: buildMessages(now),
      bandwidth: buildBandwidth(now),
      alarms: buildAlarms(now),
      faults: buildFaults(now),
      events: buildEvents(now),
      streamFrames: buildFrames(),
    },
  };
}

export const defenseSoftwareDeliveryQmDemoScenario =
  composeDefenseSoftwareDeliveryQmDemoScenario();
