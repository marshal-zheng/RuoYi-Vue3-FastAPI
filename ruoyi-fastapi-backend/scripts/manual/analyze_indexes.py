#!/usr/bin/env python3
"""
索引分析脚本 - P1-007

分析数据库索引使用情况，识别未使用和重复索引。
支持 MySQL 和 PostgreSQL。

Usage:
    python scripts/manual/analyze_indexes.py
    python scripts/manual/analyze_indexes.py --output report.json
    python scripts/manual/analyze_indexes.py --format markdown
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.database import async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.indexes import IndexAnalyzer


async def run_analysis() -> dict:
    """运行索引分析"""
    async with AsyncSession(async_engine) as db:
        report = await IndexAnalyzer.generate_report(db)
        return report


def format_console_output(report: dict) -> str:
    """格式化控制台输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("索引分析报告")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    
    # 摘要
    summary = report['summary']
    lines.append("\n📊 索引统计摘要")
    lines.append("-" * 40)
    lines.append(f"  总索引数: {summary['total_indexes']}")
    lines.append(f"  活跃索引: {summary['active_indexes']}")
    lines.append(f"  低使用率索引: {summary['low_usage_indexes']}")
    lines.append(f"  未使用索引: {summary['unused_indexes']}")
    lines.append(f"  总索引大小: {summary['total_index_size']}")
    lines.append(f"  未使用索引大小: {summary['unused_index_size']}")
    
    # 未使用索引
    unused = report['unused_indexes']
    if unused:
        lines.append(f"\n⚠️  未使用的索引 ({len(unused)} 个)")
        lines.append("-" * 40)
        for idx in unused[:10]:
            lines.append(f"  - {idx['table_name']}.{idx['index_name']}")
            lines.append(f"    大小: {idx['index_size']}, 扫描次数: {idx['index_scans']}")
        if len(unused) > 10:
            lines.append(f"  ... 还有 {len(unused) - 10} 个未显示")
    
    # 低使用率索引
    low_usage = report['low_usage_indexes']
    if low_usage:
        lines.append(f"\n📉 低使用率索引 ({len(low_usage)} 个)")
        lines.append("-" * 40)
        for idx in low_usage[:10]:
            lines.append(f"  - {idx['table_name']}.{idx['index_name']}")
            lines.append(f"    大小: {idx['index_size']}, 扫描次数: {idx['index_scans']}")
        if len(low_usage) > 10:
            lines.append(f"  ... 还有 {len(low_usage) - 10} 个未显示")
    
    # 重复索引
    duplicates = report['duplicate_indexes']
    if duplicates:
        lines.append(f"\n🔄 重复索引 ({len(duplicates)} 组)")
        lines.append("-" * 40)
        for dup in duplicates[:10]:
            lines.append(f"  - 表: {dup['table_name']}")
            lines.append(f"    索引1: {dup['index1']}")
            lines.append(f"    索引2: {dup['index2']}")
            lines.append(f"    重复列: {dup['columns']}")
        if len(duplicates) > 10:
            lines.append(f"  ... 还有 {len(duplicates) - 10} 组未显示")
    
    # 缺失索引建议
    missing = report['missing_indexes']
    if missing:
        lines.append(f"\n📝 建议添加索引的表 ({len(missing)} 个)")
        lines.append("-" * 40)
        for m in missing[:10]:
            lines.append(f"  - {m['table_name']}")
            lines.append(f"    顺序扫描: {m['sequential_scans']}, 行数: {m['row_count']}")
            lines.append(f"    原因: {m['reason']}")
        if len(missing) > 10:
            lines.append(f"  ... 还有 {len(missing) - 10} 个未显示")
    
    # 优化建议
    recommendations = report['recommendations']
    lines.append("\n💡 优化建议")
    lines.append("-" * 40)
    for rec in recommendations:
        priority_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢', 'INFO': 'ℹ️'}.get(rec['priority'], '•')
        lines.append(f"  {priority_emoji} [{rec['priority']}] {rec['message']}")
        if 'indexes' in rec:
            for idx in rec['indexes'][:3]:
                lines.append(f"     - {idx}")
        if 'tables' in rec:
            for tbl in rec['tables'][:3]:
                lines.append(f"     - {tbl}")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_markdown_output(report: dict) -> str:
    """格式化 Markdown 输出"""
    lines = []
    lines.append("# 索引分析报告")
    lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 摘要
    summary = report['summary']
    lines.append("\n## 📊 索引统计摘要")
    lines.append("\n| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 总索引数 | {summary['total_indexes']} |")
    lines.append(f"| 活跃索引 | {summary['active_indexes']} |")
    lines.append(f"| 低使用率索引 | {summary['low_usage_indexes']} |")
    lines.append(f"| 未使用索引 | {summary['unused_indexes']} |")
    lines.append(f"| 总索引大小 | {summary['total_index_size']} |")
    lines.append(f"| 未使用索引大小 | {summary['unused_index_size']} |")
    
    # 未使用索引
    unused = report['unused_indexes']
    if unused:
        lines.append(f"\n## ⚠️ 未使用的索引 ({len(unused)} 个)")
        lines.append("\n| 表名 | 索引名 | 大小 | 扫描次数 |")
        lines.append("|------|--------|------|----------|")
        for idx in unused[:20]:
            lines.append(f"| {idx['table_name']} | {idx['index_name']} | {idx['index_size']} | {idx['index_scans']} |")
    
    # 重复索引
    duplicates = report['duplicate_indexes']
    if duplicates:
        lines.append(f"\n## 🔄 重复索引 ({len(duplicates)} 组)")
        lines.append("\n| 表名 | 索引1 | 索引2 | 重复列 | 建议 |")
        lines.append("|------|-------|-------|--------|------|")
        for dup in duplicates[:20]:
            lines.append(f"| {dup['table_name']} | {dup['index1']} | {dup['index2']} | {dup['columns']} | {dup['recommendation']} |")
    
    # 缺失索引建议
    missing = report['missing_indexes']
    if missing:
        lines.append(f"\n## 📝 建议添加索引的表 ({len(missing)} 个)")
        lines.append("\n| 表名 | 顺序扫描 | 行数 | 原因 |")
        lines.append("|------|----------|------|------|")
        for m in missing[:20]:
            lines.append(f"| {m['table_name']} | {m['sequential_scans']} | {m['row_count']} | {m['reason']} |")
    
    # 优化建议
    recommendations = report['recommendations']
    lines.append("\n## 💡 优化建议")
    for rec in recommendations:
        priority_badge = {'HIGH': '🔴 HIGH', 'MEDIUM': '🟡 MEDIUM', 'LOW': '🟢 LOW', 'INFO': 'ℹ️ INFO'}.get(rec['priority'], rec['priority'])
        lines.append(f"\n### {priority_badge}")
        lines.append(f"\n{rec['message']}")
        if 'indexes' in rec and rec['indexes']:
            lines.append("\n**相关索引**:")
            for idx in rec['indexes']:
                lines.append(f"- `{idx}`")
        if 'tables' in rec and rec['tables']:
            lines.append("\n**相关表**:")
            for tbl in rec['tables']:
                lines.append(f"- `{tbl}`")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='数据库索引分析工具')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径 (JSON)')
    parser.add_argument('--format', '-f', choices=['console', 'json', 'markdown'], 
                        default='console', help='输出格式')
    args = parser.parse_args()
    
    print("正在分析索引使用情况...")
    
    report = asyncio.run(run_analysis())
    
    # 添加元数据
    report['_meta'] = {
        'generated_at': datetime.now().isoformat(),
        'tool': 'analyze_indexes.py',
        'version': '1.0.0'
    }
    
    # 输出结果
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已保存到: {output_path}")
    
    if args.format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.format == 'markdown':
        print(format_markdown_output(report))
    else:
        print(format_console_output(report))
    
    # 返回状态码
    if report['summary']['unused_indexes'] > 0 or report['duplicate_indexes']:
        return 1  # 有优化建议
    return 0


if __name__ == '__main__':
    sys.exit(main())
