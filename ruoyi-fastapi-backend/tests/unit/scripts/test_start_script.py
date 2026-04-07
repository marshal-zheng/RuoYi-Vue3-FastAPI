from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
START_SCRIPT = REPO_ROOT / 'scripts' / 'start.sh'
FUNCTIONS_START = 'extract_status_field() {'
FUNCTIONS_END = 'echo "🚀 启动 RuoYi-Vue3-FastAPI 项目"'
RUNTIME_PRELUDE_END = '# 检查并启动系统服务'


def _write_start_workflow_functions(tmp_path: Path) -> Path:
    script_text = START_SCRIPT.read_text(encoding='utf-8')
    start = script_text.index(FUNCTIONS_START)
    end = script_text.index(FUNCTIONS_END)
    functions_path = tmp_path / 'start_workflow_functions.sh'
    functions_path.write_text(script_text[start:end], encoding='utf-8')
    return functions_path


def _write_start_runtime_prelude(tmp_path: Path) -> Path:
    script_text = START_SCRIPT.read_text(encoding='utf-8')
    start = script_text.index(FUNCTIONS_END)
    end = script_text.index(RUNTIME_PRELUDE_END)
    runtime_path = tmp_path / 'start_runtime_prelude.sh'
    runtime_path.write_text(script_text[start:end], encoding='utf-8')
    return runtime_path


def _run_start_workflow(
    tmp_path: Path,
    *,
    status_lines: list[str],
    command_outputs: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    functions_path = _write_start_workflow_functions(tmp_path)
    branches = [
        """if [ "$*" = "scripts/db.py status" ]; then
cat <<'EOF'
{status_output}
EOF
return 0
fi""".format(status_output='\n'.join(status_lines))
    ]

    for command, output in command_outputs.items():
        branches.append(
            f"""if [ "$*" = "{command}" ]; then
{output}
return 0
fi"""
        )

    script = """
set -e
RED=''
GREEN=''
YELLOW=''
BLUE=''
NC=''
python() {{
{branches}
echo "unexpected python args: $*" >&2
return 1
}}
source "{functions_path}"
run_backend_db_workflow
""".format(
        branches='\n'.join(branches),
        functions_path=functions_path,
    )

    return subprocess.run(
        ['/bin/bash', '-lc', script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_start_functions(
    tmp_path: Path,
    *,
    prelude: str,
    body: str,
) -> subprocess.CompletedProcess[str]:
    functions_path = _write_start_workflow_functions(tmp_path)
    script = f"""
set -e
PROJECT_ROOT='/tmp/repo'
{prelude}
source "{functions_path}"
{body}
"""

    return subprocess.run(
        ['/bin/bash', '-lc', script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_start_runtime_prelude(
    tmp_path: Path,
    *,
    prelude: str,
    body: str,
) -> subprocess.CompletedProcess[str]:
    runtime_path = _write_start_runtime_prelude(tmp_path)
    script = f"""
set -e
PROJECT_ROOT='/tmp/repo'
{prelude}
source "{runtime_path}"
{body}
"""

    return subprocess.run(
        ['/bin/bash', '-lc', script],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_start_script_dispatches_migration_mode(tmp_path: Path) -> None:
    result = _run_start_workflow(
        tmp_path,
        status_lines=[
            'workflow_mode=migration',
            'db_target=mysql://127.0.0.1:3306/ruoyi-fastapi',
            'db_dev_sync_engine=atlas',
            'startup_action=deploy',
            'deploy_path=python scripts/db.py deploy --revision head',
        ],
        command_outputs={
            'scripts/db.py deploy --revision head': "echo 'deploy_result=success'",
        },
    )

    assert result.returncode == 0
    assert 'workflow_mode=migration' in result.stdout
    assert '当前为 migration 模式' in result.stdout
    assert 'deploy --revision head' in result.stdout
    assert 'deploy_result=success' in result.stdout
    assert '✅ 正式迁移执行完成' in result.stdout


def test_start_script_dispatches_development_mode_with_dev_sync(tmp_path: Path) -> None:
    result = _run_start_workflow(
        tmp_path,
        status_lines=[
            'workflow_mode=development',
            'db_target=mysql://127.0.0.1:3306/ruoyi-fastapi',
            'db_dev_sync_engine=atlas',
            'startup_action=dev-sync',
            'dev_sync_path=python scripts/db.py dev-sync',
            'deploy_path=python scripts/db.py deploy --revision head',
        ],
        command_outputs={
            'scripts/db.py dev-sync --invoked-by-startup': "echo 'dev_sync_result=success'",
        },
    )

    assert result.returncode == 0
    assert 'workflow_mode=development' in result.stdout
    assert '当前为 development 模式' in result.stdout
    assert '启动前执行统一 dev-sync' in result.stdout
    assert 'dev_sync_result=success' in result.stdout
    assert '✅ 启动前统一 dev-sync 执行完成' in result.stdout


def test_start_script_requires_dev_sync_path_for_dev_mode(tmp_path: Path) -> None:
    result = _run_start_workflow(
        tmp_path,
        status_lines=[
            'workflow_mode=development',
            'db_target=mysql://127.0.0.1:3306/ruoyi-fastapi',
            'db_dev_sync_engine=atlas',
            'startup_action=dev-sync',
            'deploy_path=python scripts/db.py deploy --revision head',
        ],
        command_outputs={},
    )

    assert result.returncode == 1
    assert '❌ 无法解析 dev_sync_path' in result.stdout


def test_start_script_blocks_startup_when_dev_sync_fails(tmp_path: Path) -> None:
    result = _run_start_workflow(
        tmp_path,
        status_lines=[
            'workflow_mode=development',
            'db_target=mysql://127.0.0.1:3306/ruoyi-fastapi',
            'db_dev_sync_engine=atlas',
            'startup_action=dev-sync',
            'dev_sync_path=python scripts/db.py dev-sync',
            'deploy_path=python scripts/db.py deploy --revision head',
        ],
        command_outputs={
            'scripts/db.py dev-sync --invoked-by-startup': "echo 'dev_sync_result=failed'\nreturn 1",
        },
    )

    assert result.returncode == 1
    assert 'dev_sync_result=failed' in result.stdout
    assert '❌ 启动前 dev-sync 执行失败' in result.stdout


def test_start_script_recognizes_existing_repo_backend_process(tmp_path: Path) -> None:
    result = _run_start_functions(
        tmp_path,
        prelude="""
ps() {
    if [ "$*" = "-p 123 -o command=" ]; then
        echo "Python app.py"
        return 0
    fi
    return 1
}
lsof() {
    if [ "$*" = "-a -p 123 -d cwd -Fn" ]; then
        printf 'p123\nfcwd\nn/tmp/repo/ruoyi-fastapi-backend\n'
        return 0
    fi
    return 1
}
""",
        body='is_backend_process_for_repo 123',
    )

    assert result.returncode == 0


def test_start_script_rejects_unrelated_frontend_listener(tmp_path: Path) -> None:
    result = _run_start_functions(
        tmp_path,
        prelude="""
ps() {
    if [ "$*" = "-p 456 -o command=" ]; then
        echo "node /opt/other/vite"
        return 0
    fi
    return 1
}
""",
        body="""
if is_frontend_process_for_repo 456; then
    exit 1
fi
""",
    )

    assert result.returncode == 0


def test_start_script_waits_for_listener_before_reporting_success(tmp_path: Path) -> None:
    counter_path = tmp_path / 'lsof-counter.txt'
    result = _run_start_functions(
        tmp_path,
        prelude=(
            f"COUNTER_PATH='{counter_path}'\n"
            """
lsof() {
    local current=0
    if [ -f "$COUNTER_PATH" ]; then
        current="$(cat "$COUNTER_PATH")"
    fi
    current=$((current + 1))
    printf '%s' "$current" > "$COUNTER_PATH"
    if [ "$current" -ge 2 ]; then
        echo "789"
    fi
}
kill() {
    return 0
}
sleep() {
    :
}
"""
        ),
        body='wait_for_listener_or_exit 789 8088 3',
    )

    assert result.returncode == 0


def test_start_script_clears_legacy_dev_menu_sync_env_before_runtime_boot(tmp_path: Path) -> None:
    result = _run_start_runtime_prelude(
        tmp_path,
        prelude="""
export DEV_MENU_SYNC=true
export VITE_DEV_MENU_SYNC=1
export VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS=1000
""",
        body="""
[ -z "${DEV_MENU_SYNC+x}" ]
[ -z "${VITE_DEV_MENU_SYNC+x}" ]
[ -z "${VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS+x}" ]
""",
    )

    assert result.returncode == 0
    assert '旧菜单热同步开关仅保留兼容记录，不再注入运行时' in result.stdout
