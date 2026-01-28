#!/usr/bin/env python3
"""
修复 eval() 安全漏洞的脚本

将所有 eval(data_scope_sql) 替换为安全的实现
"""
import os
import re
from pathlib import Path


def fix_eval_in_file(file_path: Path) -> bool:
    """
    修复单个文件中的 eval() 使用
    
    Returns:
        是否进行了修改
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换 eval(data_scope_sql) 为安全的实现
        # 模式 1: 在 where 子句中直接使用
        pattern1 = r'eval\(data_scope_sql\),'
        replacement1 = 'data_scope_sql if (data_scope_sql != "True" and data_scope_sql is not True) else True,'
        content = re.sub(pattern1, replacement1, content)
        
        # 模式 2: 在 conditions 列表中
        pattern2 = r'conditions\.append\(eval\(data_scope_sql\)\)'
        replacement2 = '''# 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)'''
        content = re.sub(pattern2, replacement2, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """主函数"""
    # 获取后端目录
    backend_dir = Path(__file__).parent.parent
    
    # 需要修复的目录
    dirs_to_fix = [
        backend_dir / 'module_admin' / 'dao',
        backend_dir / 'module_admin' / 'repository',
    ]
    
    fixed_files = []
    
    for dir_path in dirs_to_fix:
        if not dir_path.exists():
            continue
        
        # 遍历所有 Python 文件
        for py_file in dir_path.rglob('*.py'):
            if fix_eval_in_file(py_file):
                fixed_files.append(py_file)
                print(f"✓ Fixed: {py_file.relative_to(backend_dir)}")
    
    print(f"\n修复完成！共修复 {len(fixed_files)} 个文件")
    
    if fixed_files:
        print("\n修复的文件列表：")
        for f in fixed_files:
            print(f"  - {f.relative_to(backend_dir)}")


if __name__ == '__main__':
    main()
