#!/usr/bin/env python3
"""检查部门表数据的 del_flag 状态"""

from config.database import get_sync_engine
from sqlalchemy import text

def check_dept_data():
    engine = get_sync_engine()
    with engine.connect() as conn:
        # 检查 del_flag 分布
        result = conn.execute(text('SELECT del_flag, COUNT(*) as cnt FROM sys_dept GROUP BY del_flag'))
        print('=== del_flag 分布 ===')
        for row in result:
            print(f'del_flag={row[0]}, count={row[1]}')
        
        # 检查 status 和 del_flag 组合
        result = conn.execute(text('SELECT status, del_flag, COUNT(*) as cnt FROM sys_dept GROUP BY status, del_flag'))
        print('\n=== status + del_flag 分布 ===')
        for row in result:
            print(f'status={row[0]}, del_flag={row[1]}, count={row[2]}')
        
        # 检查是否有 del_flag='0' 的数据
        result = conn.execute(text("SELECT COUNT(*) FROM sys_dept WHERE del_flag='0'"))
        count = result.scalar()
        print(f'\n=== del_flag=\'0\' 的记录数: {count} ===')
        
        # 显示前几条数据
        result = conn.execute(text("SELECT dept_id, dept_name, del_flag, status FROM sys_dept LIMIT 5"))
        print('\n=== 前5条部门数据 ===')
        for row in result:
            print(f'dept_id={row[0]}, dept_name={row[1]}, del_flag={row[2]}, status={row[3]}')

if __name__ == '__main__':
    check_dept_data()
