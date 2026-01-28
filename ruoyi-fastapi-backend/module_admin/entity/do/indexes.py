"""
数据库索引策略 - Google 工程标准

索引设计原则：
1. 为所有外键创建索引
2. 为常用查询条件创建复合索引
3. 为排序字段创建索引
4. 避免过度索引（影响写入性能）
5. 定期分析索引使用情况

索引命名规范：
- 单列索引: idx_{table}_{column}
- 复合索引: idx_{table}_{col1}_{col2}
- 唯一索引: uk_{table}_{column}
- 外键索引: fk_{table}_{ref_table}
"""
from sqlalchemy import Index, UniqueConstraint
from module_admin.entity.do.user_do import SysUser, SysUserRole, SysUserPost
from module_admin.entity.do.role_do import SysRole, SysRoleMenu, SysRoleDept
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.do.log_do import SysOperLog, SysLogininfor


class IndexStrategy:
    """索引策略定义"""
    
    @staticmethod
    def create_user_indexes():
        """用户表索引"""
        return [
            # 登录查询优化
            Index('idx_user_username_status', SysUser.user_name, SysUser.status, SysUser.del_flag),
            # 部门查询优化
            Index('idx_user_dept', SysUser.dept_id),
            # 手机号查询（使用哈希列）
            Index('idx_user_phone_hash', SysUser.phonenumber_hash),
            # 邮箱查询（使用哈希列）
            Index('idx_user_email_hash', SysUser.email_hash),
            # 身份证查询（使用哈希列）
            Index('idx_user_id_card_hash', SysUser.id_card_hash),
            # 状态筛选
            Index('idx_user_status_delflag', SysUser.status, SysUser.del_flag),
            # 创建时间排序
            Index('idx_user_create_time', SysUser.create_time.desc()),
        ]
    
    @staticmethod
    def create_role_indexes():
        """角色表索引"""
        return [
            # 角色键查询
            Index('idx_role_key', SysRole.role_key),
            # 状态筛选
            Index('idx_role_status_delflag', SysRole.status, SysRole.del_flag),
            # 排序优化
            Index('idx_role_sort', SysRole.role_sort),
        ]
    
    @staticmethod
    def create_dept_indexes():
        """部门表索引"""
        return [
            # 父部门查询
            Index('idx_dept_parent', SysDept.parent_id),
            # 祖先路径查询（用于查找子部门）
            Index('idx_dept_ancestors', SysDept.ancestors),
            # 状态筛选
            Index('idx_dept_status_delflag', SysDept.status, SysDept.del_flag),
            # 排序优化
            Index('idx_dept_order', SysDept.order_num),
        ]
    
    @staticmethod
    def create_menu_indexes():
        """菜单表索引"""
        return [
            # 父菜单查询
            Index('idx_menu_parent', SysMenu.parent_id),
            # 菜单类型筛选
            Index('idx_menu_type_status', SysMenu.menu_type, SysMenu.status),
            # 权限标识查询
            Index('idx_menu_perms', SysMenu.perms),
            # 排序优化
            Index('idx_menu_order', SysMenu.order_num),
        ]
    
    @staticmethod
    def create_log_indexes():
        """日志表索引"""
        return [
            # 操作日志 - 时间范围查询
            Index('idx_operlog_time', SysOperLog.oper_time.desc()),
            # 操作日志 - 操作人查询
            Index('idx_operlog_name', SysOperLog.oper_name),
            # 操作日志 - 业务类型
            Index('idx_operlog_type_status', SysOperLog.business_type, SysOperLog.status),
            
            # 登录日志 - 时间范围查询
            Index('idx_loginlog_time', SysLogininfor.login_time.desc()),
            # 登录日志 - 用户名查询
            Index('idx_loginlog_username', SysLogininfor.user_name),
            # 登录日志 - 状态筛选
            Index('idx_loginlog_status', SysLogininfor.status),
        ]
    
    @staticmethod
    def create_relation_indexes():
        """关联表索引"""
        return [
            # 用户角色关联 - 双向查询优化
            Index('idx_user_role_user', SysUserRole.user_id),
            Index('idx_user_role_role', SysUserRole.role_id),
            
            # 用户岗位关联
            Index('idx_user_post_user', SysUserPost.user_id),
            Index('idx_user_post_post', SysUserPost.post_id),
            
            # 角色菜单关联
            Index('idx_role_menu_role', SysRoleMenu.role_id),
            Index('idx_role_menu_menu', SysRoleMenu.menu_id),
            
            # 角色部门关联
            Index('idx_role_dept_role', SysRoleDept.role_id),
            Index('idx_role_dept_dept', SysRoleDept.dept_id),
        ]


class IndexAnalyzer:
    """
    索引分析器
    
    用于分析索引使用情况和优化建议
    支持 MySQL 和 PostgreSQL
    """
    
    @staticmethod
    def _get_db_type() -> str:
        """获取数据库类型"""
        from config.env import DataBaseConfig
        return DataBaseConfig.db_type
    
    @staticmethod
    async def analyze_index_usage(db):
        """
        分析索引使用情况
        
        Returns:
            dict: 包含索引使用统计的字典列表
            - table_name: 表名
            - index_name: 索引名
            - index_scans: 索引扫描次数 (PostgreSQL) / 使用次数 (MySQL)
            - rows_read: 通过索引读取的行数
            - status: 'unused' | 'low_usage' | 'normal'
        """
        db_type = IndexAnalyzer._get_db_type()
        
        if db_type == 'postgresql':
            query = """
            SELECT 
                schemaname AS schema_name,
                relname AS table_name,
                indexrelname AS index_name,
                idx_scan AS index_scans,
                idx_tup_read AS rows_read,
                idx_tup_fetch AS rows_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                CASE 
                    WHEN idx_scan = 0 THEN 'unused'
                    WHEN idx_scan < 50 THEN 'low_usage'
                    ELSE 'normal'
                END AS status
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
            """
        else:
            # MySQL - 使用 sys.schema_index_statistics（需要 performance_schema）
            query = """
            SELECT 
                s.TABLE_SCHEMA AS schema_name,
                s.TABLE_NAME AS table_name,
                s.INDEX_NAME AS index_name,
                COALESCE(sis.rows_selected, 0) AS index_scans,
                COALESCE(sis.rows_selected, 0) AS rows_read,
                0 AS rows_fetched,
                CONCAT(ROUND(stat.index_length / 1024 / 1024, 2), ' MB') AS index_size,
                CASE 
                    WHEN sis.index_name IS NULL THEN 'unused'
                    WHEN sis.rows_selected < 50 THEN 'low_usage'
                    ELSE 'normal'
                END AS status
            FROM information_schema.STATISTICS s
            LEFT JOIN sys.schema_index_statistics sis
                ON sis.table_schema = s.TABLE_SCHEMA
                AND sis.table_name = s.TABLE_NAME
                AND sis.index_name = s.INDEX_NAME
            LEFT JOIN information_schema.TABLES stat
                ON stat.TABLE_SCHEMA = s.TABLE_SCHEMA
                AND stat.TABLE_NAME = s.TABLE_NAME
            WHERE s.TABLE_SCHEMA = DATABASE()
                AND s.INDEX_NAME != 'PRIMARY'
            GROUP BY s.TABLE_SCHEMA, s.TABLE_NAME, s.INDEX_NAME, 
                     sis.rows_selected, stat.index_length
            ORDER BY COALESCE(sis.rows_selected, 0) ASC
            """
        
        from sqlalchemy import text
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                'schema_name': row[0],
                'table_name': row[1],
                'index_name': row[2],
                'index_scans': row[3],
                'rows_read': row[4],
                'rows_fetched': row[5],
                'index_size': row[6],
                'status': row[7]
            }
            for row in rows
        ]
    
    @staticmethod
    async def analyze_duplicate_indexes(db):
        """
        查找重复索引（索引列完全相同或前缀重复）
        
        Returns:
            dict: 包含重复索引信息的字典列表
            - table_name: 表名
            - index1: 第一个索引名
            - index2: 第二个索引名
            - columns: 重复的列
            - recommendation: 建议操作
        """
        db_type = IndexAnalyzer._get_db_type()
        
        if db_type == 'postgresql':
            query = """
            WITH index_cols AS (
                SELECT
                    t.relname AS table_name,
                    i.relname AS index_name,
                    array_agg(a.attname ORDER BY k.n) AS columns,
                    pg_get_indexdef(i.oid) AS index_def
                FROM pg_index x
                JOIN pg_class t ON t.oid = x.indrelid
                JOIN pg_class i ON i.oid = x.indexrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                CROSS JOIN LATERAL unnest(x.indkey) WITH ORDINALITY AS k(attnum, n)
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
                WHERE n.nspname = 'public'
                GROUP BY t.relname, i.relname, i.oid
            )
            SELECT 
                a.table_name,
                a.index_name AS index1,
                b.index_name AS index2,
                array_to_string(a.columns, ', ') AS columns,
                'Consider dropping ' || b.index_name AS recommendation
            FROM index_cols a
            JOIN index_cols b ON a.table_name = b.table_name 
                AND a.index_name < b.index_name
                AND (a.columns = b.columns 
                     OR a.columns[1:array_length(b.columns, 1)] = b.columns)
            ORDER BY a.table_name, a.index_name
            """
        else:
            # MySQL
            query = """
            SELECT 
                a.TABLE_NAME AS table_name,
                a.INDEX_NAME AS index1,
                b.INDEX_NAME AS index2,
                GROUP_CONCAT(DISTINCT a.COLUMN_NAME ORDER BY a.SEQ_IN_INDEX) AS columns,
                CONCAT('Consider dropping ', b.INDEX_NAME) AS recommendation
            FROM information_schema.STATISTICS a
            JOIN information_schema.STATISTICS b
                ON a.TABLE_SCHEMA = b.TABLE_SCHEMA
                AND a.TABLE_NAME = b.TABLE_NAME
                AND a.SEQ_IN_INDEX = b.SEQ_IN_INDEX
                AND a.COLUMN_NAME = b.COLUMN_NAME
                AND a.INDEX_NAME < b.INDEX_NAME
            WHERE a.TABLE_SCHEMA = DATABASE()
                AND a.INDEX_NAME != 'PRIMARY'
                AND b.INDEX_NAME != 'PRIMARY'
            GROUP BY a.TABLE_NAME, a.INDEX_NAME, b.INDEX_NAME
            HAVING COUNT(*) = (
                SELECT COUNT(*) FROM information_schema.STATISTICS s 
                WHERE s.TABLE_SCHEMA = a.TABLE_SCHEMA 
                AND s.TABLE_NAME = a.TABLE_NAME 
                AND s.INDEX_NAME = a.INDEX_NAME
            )
            ORDER BY a.TABLE_NAME, a.INDEX_NAME
            """
        
        from sqlalchemy import text
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                'table_name': row[0],
                'index1': row[1],
                'index2': row[2],
                'columns': row[3],
                'recommendation': row[4]
            }
            for row in rows
        ]
    
    @staticmethod
    async def find_missing_indexes(db):
        """
        查找缺失的索引（基于查询统计）
        
        Returns:
            dict: 建议添加的索引列表
            - table_name: 表名
            - columns: 建议索引的列
            - reason: 建议原因
            - impact: 预计影响（扫描次数/代价）
        """
        db_type = IndexAnalyzer._get_db_type()
        
        if db_type == 'postgresql':
            # PostgreSQL: 基于 pg_stat_user_tables 分析顺序扫描
            query = """
            SELECT 
                schemaname AS schema_name,
                relname AS table_name,
                seq_scan AS sequential_scans,
                seq_tup_read AS seq_rows_read,
                idx_scan AS index_scans,
                CASE 
                    WHEN idx_scan > 0 
                    THEN ROUND((seq_scan::numeric / idx_scan)::numeric, 2)
                    ELSE seq_scan
                END AS seq_to_idx_ratio,
                n_live_tup AS row_count,
                'High sequential scan ratio - consider adding index' AS reason
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
                AND seq_scan > 100
                AND (idx_scan = 0 OR seq_scan > idx_scan * 10)
                AND n_live_tup > 1000
            ORDER BY seq_scan DESC
            LIMIT 20
            """
        else:
            # MySQL: 基于 sys.statements_with_full_table_scans
            query = """
            SELECT 
                SUBSTRING_INDEX(digest_text, '.', -1) AS table_name,
                '' AS schema_name,
                count_star AS sequential_scans,
                rows_examined AS seq_rows_read,
                0 AS index_scans,
                count_star AS seq_to_idx_ratio,
                rows_examined AS row_count,
                'Full table scan detected - consider adding index' AS reason
            FROM sys.statements_with_full_table_scans
            WHERE db = DATABASE()
            ORDER BY count_star DESC
            LIMIT 20
            """
        
        from sqlalchemy import text
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                'schema_name': row[0] if db_type == 'postgresql' else '',
                'table_name': row[1] if db_type == 'postgresql' else row[0],
                'sequential_scans': row[2],
                'seq_rows_read': row[3],
                'index_scans': row[4],
                'seq_to_idx_ratio': row[5],
                'row_count': row[6],
                'reason': row[7]
            }
            for row in rows
        ]
    
    @staticmethod
    async def get_index_stats_summary(db):
        """
        获取索引统计摘要
        
        Returns:
            dict: 索引统计摘要
        """
        db_type = IndexAnalyzer._get_db_type()
        
        if db_type == 'postgresql':
            query = """
            SELECT 
                COUNT(*) AS total_indexes,
                SUM(CASE WHEN idx_scan = 0 THEN 1 ELSE 0 END) AS unused_indexes,
                SUM(CASE WHEN idx_scan > 0 AND idx_scan < 50 THEN 1 ELSE 0 END) AS low_usage_indexes,
                SUM(CASE WHEN idx_scan >= 50 THEN 1 ELSE 0 END) AS active_indexes,
                pg_size_pretty(SUM(pg_relation_size(indexrelid))) AS total_index_size,
                pg_size_pretty(SUM(CASE WHEN idx_scan = 0 THEN pg_relation_size(indexrelid) ELSE 0 END)) AS unused_index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            """
        else:
            query = """
            SELECT 
                COUNT(DISTINCT CONCAT(s.TABLE_NAME, '.', s.INDEX_NAME)) AS total_indexes,
                COUNT(DISTINCT CASE WHEN sis.index_name IS NULL THEN CONCAT(s.TABLE_NAME, '.', s.INDEX_NAME) END) AS unused_indexes,
                COUNT(DISTINCT CASE WHEN sis.rows_selected > 0 AND sis.rows_selected < 50 THEN CONCAT(s.TABLE_NAME, '.', s.INDEX_NAME) END) AS low_usage_indexes,
                COUNT(DISTINCT CASE WHEN sis.rows_selected >= 50 THEN CONCAT(s.TABLE_NAME, '.', s.INDEX_NAME) END) AS active_indexes,
                CONCAT(ROUND(SUM(DISTINCT stat.index_length) / 1024 / 1024, 2), ' MB') AS total_index_size,
                '0 MB' AS unused_index_size
            FROM information_schema.STATISTICS s
            LEFT JOIN sys.schema_index_statistics sis
                ON sis.table_schema = s.TABLE_SCHEMA
                AND sis.table_name = s.TABLE_NAME
                AND sis.index_name = s.INDEX_NAME
            LEFT JOIN information_schema.TABLES stat
                ON stat.TABLE_SCHEMA = s.TABLE_SCHEMA
                AND stat.TABLE_NAME = s.TABLE_NAME
            WHERE s.TABLE_SCHEMA = DATABASE()
                AND s.INDEX_NAME != 'PRIMARY'
            """
        
        from sqlalchemy import text
        result = await db.execute(text(query))
        row = result.fetchone()
        
        return {
            'total_indexes': row[0] or 0,
            'unused_indexes': row[1] or 0,
            'low_usage_indexes': row[2] or 0,
            'active_indexes': row[3] or 0,
            'total_index_size': row[4] or '0',
            'unused_index_size': row[5] or '0'
        }
    
    @staticmethod
    async def generate_report(db) -> dict:
        """
        生成完整的索引分析报告
        
        Returns:
            dict: 完整的分析报告
        """
        summary = await IndexAnalyzer.get_index_stats_summary(db)
        usage = await IndexAnalyzer.analyze_index_usage(db)
        duplicates = await IndexAnalyzer.analyze_duplicate_indexes(db)
        missing = await IndexAnalyzer.find_missing_indexes(db)
        
        unused_indexes = [idx for idx in usage if idx['status'] == 'unused']
        low_usage_indexes = [idx for idx in usage if idx['status'] == 'low_usage']
        
        return {
            'summary': summary,
            'unused_indexes': unused_indexes,
            'low_usage_indexes': low_usage_indexes,
            'duplicate_indexes': duplicates,
            'missing_indexes': missing,
            'recommendations': IndexAnalyzer._generate_recommendations(
                unused_indexes, duplicates, missing
            )
        }
    
    @staticmethod
    def _generate_recommendations(unused: list, duplicates: list, missing: list) -> list:
        """生成优化建议"""
        recommendations = []
        
        if unused:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'DROP_UNUSED',
                'message': f'发现 {len(unused)} 个未使用的索引，建议删除以节省存储空间和提升写入性能',
                'indexes': [f"{idx['table_name']}.{idx['index_name']}" for idx in unused[:5]]
            })
        
        if duplicates:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'DROP_DUPLICATE',
                'message': f'发现 {len(duplicates)} 组重复索引，建议保留一个并删除其他',
                'indexes': [f"{dup['table_name']}: {dup['index1']} vs {dup['index2']}" for dup in duplicates[:5]]
            })
        
        if missing:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'ADD_INDEX',
                'message': f'发现 {len(missing)} 个表存在高频顺序扫描，建议添加索引',
                'tables': [f"{m['table_name']} (scans: {m['sequential_scans']})" for m in missing[:5]]
            })
        
        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'type': 'OK',
                'message': '索引状态良好，无需优化'
            })
        
        return recommendations


# 索引创建脚本生成
def generate_index_migration():
    """
    生成索引创建的 Alembic 迁移脚本
    
    Usage:
        python -c "from module_admin.entity.do.indexes import generate_index_migration; generate_index_migration()"
    """
    strategy = IndexStrategy()
    
    indexes = []
    indexes.extend(strategy.create_user_indexes())
    indexes.extend(strategy.create_role_indexes())
    indexes.extend(strategy.create_dept_indexes())
    indexes.extend(strategy.create_menu_indexes())
    indexes.extend(strategy.create_log_indexes())
    indexes.extend(strategy.create_relation_indexes())
    
    print("# Generated Index Creation Script")
    print("# Add this to your Alembic migration file\n")
    print("def upgrade():")
    for idx in indexes:
        print(f"    op.create_index('{idx.name}', '{idx.table.name}', {[c.name for c in idx.columns]})")
    
    print("\ndef downgrade():")
    for idx in indexes:
        print(f"    op.drop_index('{idx.name}', '{idx.table.name}')")


# 使用示例
"""
# 1. 在模型中应用索引
from module_admin.entity.do.indexes import IndexStrategy

class SysUser(Base):
    __tablename__ = 'sys_user'
    # ... 字段定义 ...
    
    # 应用索引
    __table_args__ = tuple(IndexStrategy.create_user_indexes())

# 2. 分析索引使用情况
from module_admin.entity.do.indexes import IndexAnalyzer

async def analyze_indexes(db: AsyncSession):
    # 生成完整报告
    report = await IndexAnalyzer.generate_report(db)
    
    print(f"总索引数: {report['summary']['total_indexes']}")
    print(f"未使用索引: {report['summary']['unused_indexes']}")
    print(f"低使用率索引: {report['summary']['low_usage_indexes']}")
    print(f"重复索引: {len(report['duplicate_indexes'])}")
    
    # 查看优化建议
    for rec in report['recommendations']:
        print(f"[{rec['priority']}] {rec['message']}")

# 3. 生成迁移脚本
python -c "from module_admin.entity.do.indexes import generate_index_migration; generate_index_migration()"

# 4. 运行索引分析脚本
python scripts/analyze_indexes.py --output report.json
"""
