#!/usr/bin/env python3
"""
批量为 VO 模型添加 populate_by_name=True 配置
"""
import re
from pathlib import Path

def fix_model_config(file_path: Path):
    """为 model_config 添加 populate_by_name=True"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # 模式1: 只有 alias_generator=to_camel
    pattern1 = r'(model_config\s*=\s*ConfigDict\(alias_generator=to_camel)(\))'
    replacement1 = r'\1, populate_by_name=True\2'
    content = re.sub(pattern1, replacement1, content)
    
    # 模式2: alias_generator=to_camel, from_attributes=True
    pattern2 = r'(model_config\s*=\s*ConfigDict\(alias_generator=to_camel,\s*from_attributes=True)(\))'
    replacement2 = r'\1, populate_by_name=True\2'
    content = re.sub(pattern2, replacement2, content)
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"✓ Fixed: {file_path.name}")
        return True
    else:
        print(f"- Skipped: {file_path.name} (already has populate_by_name or no match)")
        return False

def main():
    vo_dir = Path(__file__).parent.parent / 'module_admin' / 'entity' / 'vo'
    
    if not vo_dir.exists():
        print(f"Error: Directory not found: {vo_dir}")
        return
    
    print(f"Scanning VO files in: {vo_dir}\n")
    
    fixed_count = 0
    for vo_file in sorted(vo_dir.glob('*_vo.py')):
        if fix_model_config(vo_file):
            fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
