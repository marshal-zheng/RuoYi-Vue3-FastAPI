from __future__ import annotations

from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_TARGETS = [
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'modules',
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'module_admin' / 'controller',
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'module_admin' / 'service',
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'module_admin' / 'repository',
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'module_generator' / 'repository',
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'module_generator' / 'templates',
]

BANNED_PATTERNS = [
    (
        re.compile(r'ResponseUtil\.(success|failure|error|unauthorized|forbidden|ok_list)\('),
        '检测到旧响应工厂出口',
    ),
    (
        re.compile(r"['\"]rows['\"]\s*:"),
        '检测到对外返回旧 rows 主字段',
    ),
    (
        re.compile(r"data\s*=\s*\{\s*['\"]message['\"]\s*:"),
        '检测到 command result data 回流旧 success message',
    ),
    (
        re.compile(r'ResponseUtil\.ok_resource\([^)]*_result\.data\b'),
        '检测到 controller 直接透传 command result data 到成功响应',
    ),
    (
        re.compile(r'PageResponseModel\(rows='),
        '检测到旧 PageResponseModel(rows=...) 输出',
    ),
    (
        re.compile(r'\.page_num\b'),
        '检测到旧 page_num 查询字段读取',
    ),
    (
        re.compile(r'\.rows\b'),
        '检测到旧 rows 结果字段读取',
    ),
    (
        re.compile(r"['\"]pageNum['\"]\s*:"),
        '检测到对外返回旧 pageNum 主字段',
    ),
    (
        re.compile(r"['\"]next_cursor['\"]\s*:"),
        '检测到旧 cursor 字段 next_cursor 对外输出',
    ),
    (
        re.compile(r"['\"]page_size['\"]\s*:"),
        '检测到旧 cursor 字段 page_size 对外输出',
    ),
    (
        re.compile(r"['\"]type['\"]\s*:\s*['\"]/problems/"),
        '检测到相对 problem type 路径',
    ),
]

SKIP_FILES = {
    REPO_ROOT / 'ruoyi-fastapi-backend' / 'server.py',
}


def iter_files():
    seen: set[Path] = set()
    for target in SCAN_TARGETS:
        if not target.exists():
            continue
        for path in target.rglob('*'):
            if path.is_dir():
                continue
            if path.suffix not in {'.py', '.jinja2'}:
                continue
            if path in SKIP_FILES:
                continue
            if target.name == 'modules' and not {'api', 'application', 'infrastructure'}.intersection(path.parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path


def main() -> int:
    errors: list[str] = []
    for file_path in iter_files():
        source = file_path.read_text(encoding='utf-8')
        for pattern, message in BANNED_PATTERNS:
            for match in pattern.finditer(source):
                line = source.count('\n', 0, match.start()) + 1
                errors.append(f'{file_path.relative_to(REPO_ROOT)}:{line}: {message}')

    if errors:
        print('Backend message governance check failed:', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1

    print('Backend message governance check passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
