<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" class="simulation-dialog">
    <div class="simulation-report">
      <!-- 摘要信息 -->
      <div class="simulation-report__summary">
        <h3>仿真摘要</h3>
        <div class="simulation-report__summary-grid">
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">开始时间</span>
            <span class="simulation-report__summary-value">{{
              state.data.summary?.startTime || '-'
            }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">运行时长</span>
            <span class="simulation-report__summary-value">{{
              state.data.summary?.duration || '-'
            }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">报文总数</span>
            <span class="simulation-report__summary-value">{{
              state.data.summary?.messageCount || 0
            }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">告警数量</span>
            <span class="simulation-report__summary-value">{{
              state.data.summary?.alarmCount || 0
            }}</span>
          </div>
        </div>
      </div>

      <!-- 带宽统计 -->
      <div class="simulation-report__section">
        <h3>带宽统计</h3>
        <el-table :data="state.data.summary?.bandwidthStats || []" stripe>
          <el-table-column prop="protocol" label="协议类型" />
          <el-table-column prop="avgBandwidth" label="平均带宽" />
          <el-table-column prop="maxBandwidth" label="峰值带宽" />
          <el-table-column prop="avgLoad" label="平均负载" />
        </el-table>
      </div>

      <!-- 告警汇总 -->
      <div class="simulation-report__section">
        <h3>告警汇总</h3>
        <el-table :data="state.data.summary?.alarmStats || []" stripe>
          <el-table-column prop="type" label="告警类型" />
          <el-table-column prop="count" label="数量" />
          <el-table-column prop="level" label="级别">
            <template #default="{ row }">
              <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 自定义底部按钮 -->
    <template #footer>
      <div class="simulation-report__footer">
        <el-button @click="close">关闭</el-button>
        <el-dropdown @command="handleExport" trigger="click">
          <el-button type="primary">
            导出报告 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
              <el-dropdown-item command="docx">导出 Word</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup>
import { useDialog } from '@zxio/zxui';
import { ArrowDown } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
  AlignmentType,
  HeadingLevel,
  BorderStyle,
} from 'docx';
import { saveAs } from 'file-saver';

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  title: '仿真报告',
  width: '800px',
  showOk: false,
  showCancel: false,
  defaultData: () => ({
    sessionId: '',
    summary: null,
  }),
});

function getLevelType(level) {
  const map = {
    error: 'danger',
    warning: 'warning',
    info: 'info',
  };
  return map[level] || 'info';
}

/**
 * 生成报告数据对象
 */
function getReportData() {
  const summary = state.data.summary || {};
  return {
    sessionId: state.data.sessionId,
    exportTime: new Date().toLocaleString(),
    summary: {
      startTime: summary.startTime || '-',
      duration: summary.duration || '-',
      messageCount: summary.messageCount || 0,
      alarmCount: summary.alarmCount || 0,
    },
    bandwidthStats: summary.bandwidthStats || [],
    alarmStats: summary.alarmStats || [],
  };
}

/**
 * 导出为 CSV 格式
 */
function exportCSV() {
  const data = getReportData();
  const lines = [];

  // 添加 BOM 以支持中文
  // 摘要信息
  lines.push('仿真报告');
  lines.push(`导出时间,${data.exportTime}`);
  lines.push(`会话ID,${data.sessionId}`);
  lines.push('');
  lines.push('【仿真摘要】');
  lines.push(`开始时间,${data.summary.startTime}`);
  lines.push(`运行时长,${data.summary.duration}`);
  lines.push(`报文总数,${data.summary.messageCount}`);
  lines.push(`告警数量,${data.summary.alarmCount}`);
  lines.push('');

  // 带宽统计
  lines.push('【带宽统计】');
  lines.push('协议类型,平均带宽,峰值带宽,平均负载');
  if (data.bandwidthStats.length > 0) {
    data.bandwidthStats.forEach((item) => {
      lines.push(`${item.protocol || ''},${item.avgBandwidth || ''},${item.maxBandwidth || ''},${item.avgLoad || ''}`);
    });
  } else {
    lines.push('暂无数据');
  }
  lines.push('');

  // 告警汇总
  lines.push('【告警汇总】');
  lines.push('告警类型,数量,级别');
  if (data.alarmStats.length > 0) {
    data.alarmStats.forEach((item) => {
      lines.push(`${item.type || ''},${item.count || ''},${item.level || ''}`);
    });
  } else {
    lines.push('暂无数据');
  }

  const csvContent = lines.join('\n');
  downloadFile(csvContent, `仿真报告_${getTimestamp()}.csv`, 'text/csv;charset=utf-8');
  ElMessage.success('CSV 导出成功');
}

/**
 * 导出为 JSON 格式
 */
function exportJSON() {
  const data = getReportData();
  const jsonContent = JSON.stringify(data, null, 2);
  downloadFile(jsonContent, `仿真报告_${getTimestamp()}.json`, 'application/json;charset=utf-8');
  ElMessage.success('JSON 导出成功');
}

/**
 * 创建表格单元格
 */
function createTableCell(text, isHeader = false) {
  return new TableCell({
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text: String(text ?? ''),
            bold: isHeader,
            size: isHeader ? 24 : 22,
          }),
        ],
        alignment: AlignmentType.CENTER,
      }),
    ],
    shading: isHeader ? { fill: 'E6E6E6' } : undefined,
  });
}

/**
 * 创建表格
 */
function createTable(headers, rows) {
  const tableRows = [
    new TableRow({
      children: headers.map((h) => createTableCell(h, true)),
      tableHeader: true,
    }),
    ...rows.map(
      (row) =>
        new TableRow({
          children: row.map((cell) => createTableCell(cell)),
        })
    ),
  ];

  return new Table({
    rows: tableRows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
      left: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
      right: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
      insideVertical: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
    },
  });
}

/**
 * 导出为 DOCX 格式
 */
async function exportDOCX() {
  const data = getReportData();

  // 构建文档内容
  const children = [
    // 标题
    new Paragraph({
      text: '仿真报告',
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `导出时间：${data.exportTime}`, size: 20, color: '666666' }),
      ],
      alignment: AlignmentType.CENTER,
    }),
    new Paragraph({ text: '' }),

    // 仿真摘要
    new Paragraph({
      text: '一、仿真摘要',
      heading: HeadingLevel.HEADING_1,
    }),
    createTable(
      ['项目', '值'],
      [
        ['会话ID', data.sessionId || '-'],
        ['开始时间', data.summary.startTime],
        ['运行时长', data.summary.duration],
        ['报文总数', data.summary.messageCount],
        ['告警数量', data.summary.alarmCount],
      ]
    ),
    new Paragraph({ text: '' }),

    // 带宽统计
    new Paragraph({
      text: '二、带宽统计',
      heading: HeadingLevel.HEADING_1,
    }),
  ];

  // 带宽统计表格
  if (data.bandwidthStats.length > 0) {
    children.push(
      createTable(
        ['协议类型', '平均带宽', '峰值带宽', '平均负载'],
        data.bandwidthStats.map((item) => [
          item.protocol || '-',
          item.avgBandwidth || '-',
          item.maxBandwidth || '-',
          item.avgLoad || '-',
        ])
      )
    );
  } else {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: '暂无数据', italics: true, color: '999999' })],
      })
    );
  }
  children.push(new Paragraph({ text: '' }));

  // 告警汇总
  children.push(
    new Paragraph({
      text: '三、告警汇总',
      heading: HeadingLevel.HEADING_1,
    })
  );

  if (data.alarmStats.length > 0) {
    children.push(
      createTable(
        ['告警类型', '数量', '级别'],
        data.alarmStats.map((item) => [item.type || '-', item.count || 0, item.level || '-'])
      )
    );
  } else {
    children.push(
      new Paragraph({
        children: [new TextRun({ text: '暂无数据', italics: true, color: '999999' })],
      })
    );
  }

  // 创建文档
  const doc = new Document({
    sections: [
      {
        properties: {},
        children,
      },
    ],
  });

  // 生成并下载
  const blob = await Packer.toBlob(doc);
  saveAs(blob, `仿真报告_${getTimestamp()}.docx`);
  ElMessage.success('Word 导出成功');
}

/**
 * 下载文件
 */
function downloadFile(content, filename, mimeType) {
  const blob = new Blob(['\ufeff' + content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 获取时间戳字符串
 */
function getTimestamp() {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
}

/**
 * 处理导出
 */
function handleExport(format) {
  switch (format) {
    case 'csv':
      exportCSV();
      break;
    case 'json':
      exportJSON();
      break;
    case 'docx':
      exportDOCX();
      break;
    default:
      ElMessage.warning('不支持的导出格式');
  }
}

function openDialog(data) {
  open({
    sessionId: data?.sessionId || '',
    summary: data?.summary || null,
  });
}

defineExpose({ open: openDialog, close });
</script>

<style lang="less" scoped>
@import (reference) '../styles/simulation-dialog-theme.less';

.simulation-report {
  color: @sim-dialog-text-primary;

  &__summary {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: @sim-dialog-text-primary;
    }
  }

  &__summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  &__summary-item {
    .sim-dialog-card();
    padding: 16px;
    text-align: center;
  }

  &__summary-label {
    display: block;
    font-size: 12px;
    color: @sim-dialog-text-secondary;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
  }

  &__summary-value {
    display: block;
    font-size: 18px;
    font-weight: 700;
    color: @sim-dialog-text-white;
  }

  &__section {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 600;
      color: @sim-dialog-text-primary;
    }
  }

  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
