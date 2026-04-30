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

const baseTeam = '智慧菜市场运营管理演示团队';
const INDUSTRY = 'smart-wet-market-ops';
const INDUSTRY_NAME = '智慧菜市场运营管理';

type RiskLevel = 'high' | 'medium' | 'low';

interface MarketSpec {
  projectId: number;
  versionId: number;
  projectCode: string;
  stallTypeLabel: string;
  districtLabel: string;
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

const SPECS: MarketSpec[] = [
  {
    projectId: 7161,
    versionId: 8161,
    projectCode: 'SMART-WET-CSFR-071',
    stallTypeLabel: '水产／冰鲜联营档口',
    districtLabel: '湖南省长沙市芙蓉区｜五一商圈「坡子街·火宫殿」市井智慧菜场片区',
    projectName:
      '芙蓉区坡子市井智慧菜场水产联营区地沟排水与地面防滑提档改造项目',
    themesLabel: '生鲜摊位改造工程（排水防滑）施工图会审与商户清场',
    owner: '物业运营经理-沈梦舟',
    department: '市场物业与现场运营一部',
    businessStage: '施工图会审与商户清场',
    progress:
      '排水泵站容量与坡向复核已完成，联营户清场签收公示满 72 小时；夜间错峰封场施工图已报芙蓉区城管局备案。',
    background:
      '火宫殿及周边早市人流量大，水产宰杀冲洗水量集中，联营区地沟坡向偏小，梅雨季节湿滑投诉上升。须在保障早市开市前提下分片区封控改造。',
    mainRisk:
      '梅雨期临时泵站抽排能力不足可能引起相邻肉制品区渗水；节假日游客与备货高峰叠加易导致工期纠纷。',
    handling:
      '沈梦舟与市政养护单位共设导流槽及临时泵站，联营理事长签分时段卸货承诺书；湿滑警示与围挡纳入每日巡检工单。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '清场签收完成率', value: '94%', trend: 'up' },
      { name: '湿滑隐患工单关闭率', value: '71%', trend: 'flat' },
    ],
    topologyEntry: '水产联营区宰杀冲洗入口',
    topologyStage: '施工图会审与临时排水节点',
    topologyRiskMonitor: '地沟渗漏与渗水外溢监控',
    alarmTopic:
      '湘江沿岸湿度回升预警下，临时排水泵站流量偏低已持续 15 分钟，相邻果蔬岛台地面相对湿度抬升。',
    sessionStatus: 'running',
    scenarioStage: '摊位改造',
    includeFault: true,
    faultStatus: 'processing',
  },
  {
    projectId: 7162,
    versionId: 8171,
    projectCode: 'SMART-WET-CSYH-072',
    stallTypeLabel: '白条肉与冰鲜冷链专档',
    districtLabel: '湖南省长沙市雨花区｜高桥副食品城与智慧农批衔接带',
    projectName:
      '雨花区高桥冷链岛台与智慧农批数据中台联通下的机组维保与库温专项治理',
    themesLabel: '冷链设备维护与库温稳定',
    owner: '设备设施主管-高远',
    department: '设施设备与能源管理组',
    businessStage: '维保窗口冻结与备件就位',
    progress:
      '二号螺杆压缩机轴承与高桥仓同步到货，制冷剂加注窗口锁定周三凌晨；库温探头已与市级重要产品追溯试点平台心跳对时。',
    background:
      '高桥片区批发与零售业态交织，白条、冰鲜周转快，三伏天库温易出现尖峰；管理方要求冷链曲线、价签溯源与抽检留样同一口径展示。',
    mainRisk:
      '凌晨维保停机若未及时复启，将影响早六点「批零交接」档期；物联网关偶发超时导致备用机组联锁滞后。',
    handling:
      '高远执行双人操作票与扫码复启确认，维保与食安值守岗拉通短信链；超时未复机触发雨花运营总值班升级流程。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '库温达标时长占比', value: '98.2%', trend: 'up' },
      { name: '维保准时完成率', value: '89%', trend: 'flat' },
    ],
    topologyEntry: '冷链机组与库门传感入口',
    topologyStage: '维保窗口冻结节点',
    topologyRiskMonitor: '库温贴近上限监控',
    alarmTopic:
      '二号冷库 30 分钟滚动均值距上限不足 0.6℃，门磁显示频繁开启，复核是否接驳货车同时开门散热。',
    sessionStatus: 'running',
    scenarioStage: '冷链维护',
    includeFault: true,
    faultStatus: 'processing',
  },
  {
    projectId: 7163,
    versionId: 8181,
    projectCode: 'SMART-WET-CSTX-073',
    stallTypeLabel: '散装熟食与豆制品档',
    districtLabel: '湖南省长沙市天心区｜书院路旧城改造邻里智慧菜场',
    projectName:
      '天心区书院路邻里菜场散装熟食快检复检与岳麓山游客外带食品溯源台账专项',
    themesLabel: '食品安全抽检与快检闭环',
    owner: '食安稽查主管-廖清仪',
    department: '食品安全与抽检协调室',
    businessStage: '快检阳性追溯与摊位对照封存',
    progress:
      '初检可疑批次已由天心区市场监管局见证封存留样；索证影像已推送「湘冷链」与智慧监管侧，待第三方复检报告编号回写。',
    background:
      '书院路菜场服务周边住民与天心阁—书院路步道游客外带熟食需求，市里要求公示屏同源展示快检、处置与复牌条件。',
    mainRisk:
      '复检等候期同类熟食摊客流量转移易出现谣言；手写进货单未及时补录将影响电子台账与监管侧字段对齐。',
    handling:
      '廖清仪组织监管、摊主、市场方三方签封笔录；滚动字幕公示预计反馈时点；接线口径由天心客服坐席单向下发。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '抽检台账字段完整率', value: '99.1%', trend: 'up' },
      { name: '公示信息更新延迟', value: '≤12 分钟', trend: 'down' },
    ],
    topologyEntry: '散装熟食快检与留样入口',
    topologyStage: '封存与溯源核对节点',
    topologyRiskMonitor: '台账一致性复核',
    alarmTopic:
      '市场监管侧提示某批发商索证缺页扫描件，与本市场扫码签收时间偏差 8 分钟，需在「湘食安」侧补备注。',
    sessionStatus: 'paused',
    scenarioStage: '食安抽检',
    includeFault: false,
  },
  {
    projectId: 7164,
    versionId: 8191,
    projectCode: 'SMART-WET-CSYL-074',
    stallTypeLabel: '主通道肉菜综合岛台',
    districtLabel: '湖南省长沙市岳麓区｜溁湾镇望月湖老旧小区配套菜场',
    projectName:
      '望月湖老旧小区配套菜场主通道潮汐护栏与地面高差客流动线综合治理',
    themesLabel: '客流动线与高峰潮汐疏导',
    owner: '企划现场运营-林子墨',
    department: '市场企划与客流量分析组',
    businessStage: '导流标线施划与潮汐护栏试点',
    progress:
      '咸嘉湖路与麓山路通勤潮汐下，两处拐角导流护栏试运行完成热力比对，冲突触点下降约 18%；周末拟扩展至毗邻水产岛台。',
    background:
      '望月湖片区老龄住户与大学城通勤共用早市峰值，斜坡收口的雨棚滴水加剧地面湿滑；改造以可调护栏试错，不向摊主收押金。',
    mainRisk:
      '护栏开合若遮挡消防目视通道将不符合岳麓消防大队责令改正要求；摊主上货电瓶车与接送学童对冲。',
    handling:
      '林子墨联合岳麓区城管驻场专班与街道办踏勘标线，电瓶车限时单行；指示牌增加岳麓山景区客流导向简体字说明。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '拥挤指数峰值', value: '6.4→5.2', trend: 'down' },
      { name: '通道冲突告警数', value: '单日 37→21', trend: 'down' },
    ],
    topologyEntry: '主通道高差收口入口',
    topologyStage: '潮汐护栏试点节点',
    topologyRiskMonitor: '视线遮挡与拐角冲突监控',
    alarmTopic:
      '望月湖拐角热力图连续 22 分钟超阈值，推断护栏转角半径偏大形成局部回旋，企划需现场确认是否回收一节栅栏。',
    sessionStatus: 'running',
    scenarioStage: '动线优化',
    includeFault: false,
  },
  {
    projectId: 7165,
    versionId: 8201,
    projectCode: 'SMART-WET-CSKF-075',
    stallTypeLabel: '联营冻品白条区',
    districtLabel: '湖南省长沙市开福区｜北辰三角洲「渔人码头」临江智慧市集',
    projectName:
      '北辰三角洲临江市集冻品白条联营区明码标价屏与智慧价签回传问题整改',
    themesLabel: '价格公示与智慧价签数据治理',
    owner: '综合管理科科长-瞿晓枫',
    department: '市场综合管理科',
    businessStage: '公示屏模版统一与离线价签清点',
    progress:
      '省级「湘价通」推荐模版已下发至各联营秤台，156 枚价签清点完毕，尚有 14 枚回传周期超 2 小时待厂商驻场复检。',
    background:
      '12345·长沙市民热线多起反映「灯箱价与小票价不符」。开市福区综治专项，聚焦物联离线、收银员手工改价未回写两个问题。',
    mainRisk:
      '节假日龙虾、闸蟹促销规则与静态屏内容不同步引发二次投诉；多版本小票样式干扰监管抽查。',
    handling:
      '瞿晓枫暂缓异常联营户信用加分参评，约谈组长开立「调价双人确认」工单，消费者端开放「扫码差评—价签异常」单列入口。',
    riskLevel: 'medium',
    keyMetrics: [
      { name: '价签在线率', value: '91%', trend: 'up' },
      { name: '热线价格类投诉周环比', value: '-35%', trend: 'down' },
    ],
    topologyEntry: '冻品联营区收银与公示屏入口',
    topologyStage: '公示模版切换节点',
    topologyRiskMonitor: '价签回传延迟监控',
    alarmTopic:
      '联营秤批次 B—CS—12 出现连续 11 笔结算未触发价签回写，怀疑 RS485 防雷盒受潮，值守建议远程复位采集网关。',
    sessionStatus: 'paused',
    scenarioStage: '价格公示治理',
    includeFault: true,
    faultStatus: 'investigating',
  },
  {
    projectId: 7166,
    versionId: 8211,
    projectCode: 'SMART-WET-CSXS-076',
    stallTypeLabel: '社区便民服务与联营咨询台',
    districtLabel: '湖南省长沙县星沙｜泉塘街道泉星智慧邻里菜场',
    projectName:
      '长沙县泉星邻里菜场商户投诉工单线上化与浏阳河片区舆情回访能力提升专项',
    themesLabel: '投诉处理与服务台能力提升',
    owner: '客服与公共关系-阮诗涵',
    department: '客户服务与舆情专班',
    businessStage: '工单 SLA 校准与多渠道入口合并',
    progress:
      '「我的长沙」小程序与场内统一二维码编号已完成映射绑定；法定节假日 SLA 延长至 120 分钟并以短信兜底告知；经营户培训覆盖率约 92%。',
    background:
      '泉塘片区工业区与住宅区混居，工单集中在退换货不畅、白条称重解释、夜市排队三方面，需与市场巡逻与视频索引联动便于复盘。',
    mainRisk:
      '普通话话术与浏阳、湘乡等地方言解释不一致易产生二次舆情；极少数摊位不使用线上工单被督导视为响应不及时。',
    handling:
      '阮诗涵增补湘语系常用话术快捷回复，网格员协助年长摊主代为录单；「重复工单」自动生成升级调解台账并抄送县区综治中心。',
    riskLevel: 'high',
    keyMetrics: [
      { name: '工单按期关闭率', value: '94%', trend: 'up' },
      { name: '二次投诉占比', value: '6%', trend: 'down' },
    ],
    topologyEntry: '社区服务台与意见码入口',
    topologyStage: 'SLA 与回访节点',
    topologyRiskMonitor: '重复投诉激增监控',
    alarmTopic:
      '同一联营编码 30 分钟内产生 5 条「白条斤两疑虑」工单，专班需连线现场标准砝码复检并调取监控视频片段。',
    sessionStatus: 'paused',
    scenarioStage: '商户服务',
    includeFault: true,
    faultStatus: 'processing',
  },
];

const SEED =
  'smart-market-ops-demo-changsha-9e2bbd11c8344cf4a501c403a3c60190';

function sessionIdFor(pid: number) {
  return `smart-market-ops-session-${pid}-1`;
}

function buildProjects(now: Date): DemoProject[] {
  return SPECS.map((s) => ({
    projectId: s.projectId,
    projectName: s.projectName,
    projectCode: s.projectCode,
    projectDesc: s.background,
    description: `${s.mainRisk} 当前阶段：${s.businessStage}。${s.handling}`,
    status: '0' as const,
    createTime: new Date(now.getTime() - 9 * 24 * 60 * 60 * 1000).toISOString(),
    updateTime: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
    remark: `${s.handling} 最近一次运营例会上由 ${s.owner} 汇报并形成纪要。`,
    owner: s.owner,
    department: s.department,
    createBy: `${s.department}-统筹`,
    updateBy: s.owner.split('-').pop() ?? s.owner,
    industry: INDUSTRY,
    industryName: INDUSTRY_NAME,
    region: s.districtLabel,
    stallCategory: s.stallTypeLabel,
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
    versionName: `${s.projectName}（${s.businessStage}）演示拓扑版`,
    description: `${baseTeam}围绕${s.stallTypeLabel}，在「${s.themesLabel}」主题下沉淀可回放的处理记录、告警与巡检信号，用于离线演示链路验收。`,
    locked: true,
    isLocked: '1',
    status: '0',
    createTime: new Date(now.getTime() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    updateTime: now.toISOString(),
    createBy: baseTeam,
    updateBy: s.owner.replace(/.*?-/, ''),
    remark: s.progress,
  }));
}

function buildTopologies(now: Date): DemoTopology[] {
  return SPECS.map((s) => ({
    id: `smart-market-ops-topology-${s.projectId}`,
    projectId: s.projectId,
    versionId: s.versionId,
    updateTime: now.toISOString(),
    graph: {
      nodes: [
        {
          id: `smart-mkt-${s.projectId}-n1`,
          label: s.topologyEntry,
          type: 'domain-object',
          status: 'active',
        },
        {
          id: `smart-mkt-${s.projectId}-n2`,
          label: s.topologyStage,
          type: 'process-stage',
          status: 'warning',
        },
        {
          id: `smart-mkt-${s.projectId}-n3`,
          label: `${s.owner}处置`,
          type: 'persona-action',
          status: 'active',
        },
        {
          id: `smart-mkt-${s.projectId}-n4`,
          label: s.topologyRiskMonitor,
          type: 'risk-control',
          status: s.riskLevel === 'high' ? 'warning' : 'active',
        },
      ],
      edges: [
        {
          id: `smart-mkt-${s.projectId}-e1`,
          source: s.topologyEntry,
          target: s.topologyStage,
          label: s.progress.slice(0, 28),
        },
        {
          id: `smart-mkt-${s.projectId}-e2`,
          source: s.topologyStage,
          target: `${s.owner}处置`,
          label: '现场协调与签收',
        },
        {
          id: `smart-mkt-${s.projectId}-e3`,
          source: `${s.owner}处置`,
          target: s.topologyRiskMonitor,
          label: `${s.keyMetrics[0]?.name ?? '核心指标'} 跟踪`,
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
    createTime: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
    updateTime: now.toISOString(),
    scenarioStage: s.scenarioStage,
    riskLevel: s.riskLevel,
    stallCategory: s.stallTypeLabel,
    districtSnapshot: s.districtLabel,
  }));
}

function buildAlarms(now: Date): DemoSimulationAlarm[] {
  return SPECS.map((s) => ({
    alarmId: `${sessionIdFor(s.projectId)}-alarm-1`,
    sessionId: sessionIdFor(s.projectId),
    timestamp: new Date(now.getTime() - 2700000).toISOString(),
    severity: s.riskLevel,
    status: 'open',
    title: `${s.projectName.slice(0, 18)}…`,
    relatedStallType: s.stallTypeLabel,
    message: `【${s.scenarioStage}】${s.alarmTopic} 经办责任人：${s.owner}（${s.department}）。`,
  }));
}

function buildFaults(now: Date): DemoSimulationFault[] {
  return SPECS.filter((s) => s.includeFault).map((s) => ({
    faultId: `${sessionIdFor(s.projectId)}-fault-1`,
    sessionId: sessionIdFor(s.projectId),
    timestamp: new Date(now.getTime() - 2500000).toISOString(),
    faultType: s.scenarioStage,
    relatedTheme: s.themesLabel,
    description: `${s.mainRisk} 当前处置动作：${s.handling}`,
    status: s.faultStatus ?? 'processing',
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
        message: `【推进】${s.owner}完成对「${s.topologyStage}」的例行核对，摊位/设备状态已与巡检单同步。`,
      },
      {
        eventId: `${sid}-event-2`,
        sessionId: sid,
        triggerTime: new Date(now.getTime() - 5200000).toISOString(),
        eventType: s.scenarioStage,
        stageLabel: s.businessStage,
        message: `【风险复核】对照 ${s.mainRisk.slice(0, 36)}… 更新风险分级为「${s.riskLevel === 'high' ? '重点关注' : '常规跟踪'}」。`,
      },
      {
        eventId: `${sid}-event-3`,
        sessionId: sid,
        triggerTime: new Date(now.getTime() - 5000000).toISOString(),
        eventType: s.scenarioStage,
        stageLabel: s.businessStage,
        message: `【指标】《${s.keyMetrics[0].name}》当前为 ${s.keyMetrics[0].value}，处理记录归档至离线演示链路。`,
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
        timestamp: new Date(now.getTime() - 5550000).toISOString(),
        role: 'system',
        content: `系统自动：${s.districtLabel}「${s.stallTypeLabel}」会话已开启，主题为 ${s.themesLabel}，负责人 ${s.owner}。`,
        severity,
      },
      {
        id: `${sid}-msg-2`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5520000).toISOString(),
        role: 'operator',
        content: `${s.owner}：现场最新进展——${s.progress}`,
        severity,
      },
      {
        id: `${sid}-msg-3`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5490000).toISOString(),
        role: 'system',
        content: `核心指标快照：${s.keyMetrics.map((m) => `${m.name}${m.value}`).join('；')}。`,
        severity,
      },
      {
        id: `${sid}-msg-4`,
        sessionId: sid,
        timestamp: new Date(now.getTime() - 5460000).toISOString(),
        role: 'operator',
        content: `${s.handling}`,
        severity,
      }
    );
  }
  return out;
}

function buildBandwidth(now: Date): DemoSimulationBandwidth[] {
  let inbound = 32;
  return SPECS.map((s, i) => ({
    id: `${sessionIdFor(s.projectId)}-bw-1`,
    sessionId: sessionIdFor(s.projectId),
    portId: `smart-mkt-port-${s.projectId}`,
    timestamp: new Date(now.getTime() - (6 - i) * 270000).toISOString(),
    inboundMbps: (inbound += 5 + i),
    outboundMbps: 18 + i * 3,
    utilization: 0.52 + ((i % 4) / 22),
    note: `${s.stallTypeLabel}设备与公示屏链路`,
  }));
}

function buildFrames(): DemoSimulationFrame[] {
  return SPECS.map((s) => ({
    frameId: `${sessionIdFor(s.projectId)}-frame-summary`,
    sessionId: sessionIdFor(s.projectId),
    order: 1,
    type: 'summary',
    delayMs: 200,
    payload: {
      projectName: s.projectName,
      stage: s.businessStage,
      riskLevel: s.riskLevel,
      stallType: s.stallTypeLabel,
      district: s.districtLabel,
    },
  }));
}

export function composeSmartMarketOperationsDemoScenario(referenceTimeIso?: string): DemoScenarioPackage {
  const now = referenceTimeIso ? new Date(referenceTimeIso) : new Date();
  const base = realEstateP0AcceptanceDemoScenario;
  const auth = structuredClone(base.auth);
  const system = structuredClone(base.system);

  return {
    schemaVersion: DEMO_SCENARIO_SCHEMA_VERSION,
    scenario: {
      id: 'smart-market-operations-demo',
      name: '智慧菜市场运营管理（长沙）',
      version: '1.0.1',
      fingerprint: 'smart-market-operations-demo-cs-k3m9',
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

export const smartMarketOperationsDemoScenario =
  composeSmartMarketOperationsDemoScenario();
