from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
STOP_SCRIPT = REPO_ROOT / 'scripts' / 'stop.sh'
FUNCTIONS_START = 'listening_port_pids() {'
FUNCTIONS_END = "echo '🛑 停止 RuoYi-Vue3-FastAPI 开发服务'"


def _write_stop_functions(tmp_path: Path) -> Path:
    script_text = STOP_SCRIPT.read_text(encoding='utf-8')
    start = script_text.index(FUNCTIONS_START)
    end = script_text.index(FUNCTIONS_END)
    functions_path = tmp_path / 'stop_functions.sh'
    functions_path.write_text(script_text[start:end], encoding='utf-8')
    return functions_path


def _run_stop_functions(
    tmp_path: Path,
    *,
    prelude: str,
    body: str,
) -> subprocess.CompletedProcess[str]:
    functions_path = _write_stop_functions(tmp_path)
    script = f"""
set -e
PROJECT_ROOT='/tmp/repo'
APP_PORT='8088'
FRONTEND_PORT='80'
STOP_TIMEOUT_SECONDS='3'
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


def test_stop_script_recognizes_repo_backend_process(tmp_path: Path) -> None:
    result = _run_stop_functions(
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


def test_stop_script_rejects_foreign_frontend_process(tmp_path: Path) -> None:
    result = _run_stop_functions(
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


def test_stop_script_waits_until_process_exits(tmp_path: Path) -> None:
    counter_path = tmp_path / 'kill-counter.txt'
    result = _run_stop_functions(
        tmp_path,
        prelude=(
            f"COUNTER_PATH='{counter_path}'\n"
            """
kill() {
    if [ "$1" = "-0" ]; then
        local current=0
        if [ -f "$COUNTER_PATH" ]; then
            current="$(cat "$COUNTER_PATH")"
        fi
        current=$((current + 1))
        printf '%s' "$current" > "$COUNTER_PATH"
        if [ "$current" -ge 2 ]; then
            return 1
        fi
        return 0
    fi
    return 0
}
sleep() {
    :
}
"""
        ),
        body='wait_for_process_stop 789 3',
    )

    assert result.returncode == 0
