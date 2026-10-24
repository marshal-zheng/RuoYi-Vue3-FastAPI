"""
Multi-worker smoke tests for simulation runtime state sharing.

This test validates cross-process behavior:
1) Worker A writes session snapshot + runtime streams.
2) Worker B reads snapshot/streams from shared storage.
3) Worker B can continue consuming incrementally by offset.
"""

import asyncio
import multiprocessing as mp
import json
from pathlib import Path
import tempfile
from queue import Empty

import pytest

from module_admin.entity.do.enums import SimulationStatusEnum


class _FileProcessRedis:
    """
    Minimal async Redis-like client backed by shared files.

    This avoids Manager socket binding (restricted in sandbox) while still
    providing cross-process shared storage semantics for smoke testing.

    Supports only commands used by SimulationRuntimeStateStore.
    """

    def __init__(self, root_dir: str):
        self._root = Path(root_dir)
        self._kv_dir = self._root / "kv"
        self._list_dir = self._root / "lists"
        self._kv_dir.mkdir(parents=True, exist_ok=True)
        self._list_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(key: str) -> str:
        return key.replace("/", "__").replace(":", "__")

    def _kv_path(self, key: str) -> Path:
        return self._kv_dir / f"{self._safe_name(key)}.txt"

    def _list_path(self, key: str) -> Path:
        return self._list_dir / f"{self._safe_name(key)}.json"

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        text = path.read_text(encoding="utf-8")
        if not text:
            return default
        return json.loads(text)

    @staticmethod
    def _write_json(path: Path, payload):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    async def setex(self, key, ttl, value):
        self._kv_path(key).write_text(str(value), encoding="utf-8")
        return True

    async def get(self, key):
        path = self._kv_path(key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    async def delete(self, *keys):
        removed = 0
        for key in keys:
            kv_path = self._kv_path(key)
            list_path = self._list_path(key)
            if kv_path.exists():
                kv_path.unlink()
                removed += 1
            if list_path.exists():
                list_path.unlink()
                removed += 1
        return removed

    async def rpush(self, key, *values):
        path = self._list_path(key)
        rows = list(self._read_json(path, []))
        rows.extend(values)
        self._write_json(path, rows)
        return len(rows)

    async def llen(self, key):
        return len(list(self._read_json(self._list_path(key), [])))

    async def lrange(self, key, start, end):
        rows = list(self._read_json(self._list_path(key), []))
        size = len(rows)
        if size == 0:
            return []

        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)
        if start > end:
            return []
        return rows[start : end + 1]

    async def ltrim(self, key, start, end):
        path = self._list_path(key)
        rows = list(self._read_json(path, []))
        size = len(rows)
        if size == 0:
            self._write_json(path, [])
            return True

        if start < 0:
            start = max(0, size + start)
        if end < 0:
            end = size + end
        end = min(end, size - 1)

        if start > end:
            self._write_json(path, [])
            return True

        self._write_json(path, rows[start : end + 1])
        return True

    async def expire(self, key, ttl):
        return True


def _make_runtime_store(shared_root: str):
    from module_admin.service.simulation_runtime_state import init_simulation_runtime_state_store

    redis_client = _FileProcessRedis(shared_root)
    return init_simulation_runtime_state_store(
        redis_client=redis_client,
        session_ttl=3600,
        stream_ttl=3600,
        max_stream_items=1000,
    )


def _writer_worker(shared_root: str, session_id: str, start_seq: int, count: int, write_snapshot: bool):
    async def _run():
        store = _make_runtime_store(shared_root)

        if write_snapshot:
            await store.save_session_snapshot(
                session_id,
                {
                    "status": SimulationStatusEnum.RUNNING.value,
                    "engine_present": True,
                    "speed": 1.0,
                },
            )

        messages = [{"seq": seq, "messageId": f"m-{seq}"} for seq in range(start_seq, start_seq + count)]
        bandwidth = [{"seq": seq, "portId": "p1", "bandwidthMbps": 12.3} for seq in range(start_seq, start_seq + count)]
        alarms = [{"seq": seq, "alarmType": "packet_loss"} for seq in range(start_seq, start_seq + count)]
        faults = [{"seq": seq, "eventType": "fault_created"} for seq in range(start_seq, start_seq + count)]

        await store.append_events(session_id, "messages", messages)
        await store.append_events(session_id, "bandwidth", bandwidth)
        await store.append_events(session_id, "alarms", alarms)
        await store.append_events(session_id, "faults", faults)

    asyncio.run(_run())


def _reader_worker(shared_root: str, session_id: str, offset: int, limit: int, out_queue):
    async def _run():
        store = _make_runtime_store(shared_root)
        snapshot = await store.get_session_snapshot(session_id)
        messages, new_offset = await store.get_events_since(session_id, "messages", offset=offset, limit=limit)
        faults, _ = await store.get_events_since(session_id, "faults", offset=0, limit=1000)
        return {
            "status": (snapshot or {}).get("status"),
            "message_seqs": [item["seq"] for item in messages],
            "fault_count": len(faults),
            "offset": new_offset,
        }

    out_queue.put(asyncio.run(_run()))


def _run_process(ctx, target, args, timeout_sec: int = 15):
    proc = ctx.Process(target=target, args=args)
    proc.start()
    proc.join(timeout_sec)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        raise AssertionError(f"process timeout: {target.__name__}")
    assert proc.exitcode == 0, f"process failed: {target.__name__}, exit={proc.exitcode}"


@pytest.mark.integration
def test_simulation_runtime_state_shared_across_workers():
    """
    Smoke test:
    - worker-1 writes snapshot + 3 events
    - worker-2 reads all events and records offset
    - worker-1 appends 2 more events
    - worker-2 reads only incremental events from previous offset
    """
    ctx = mp.get_context("spawn")

    with tempfile.TemporaryDirectory() as shared_root:
        out_queue = ctx.Queue()
        session_id = "sim-multi-worker-smoke"

        _run_process(ctx, _writer_worker, (shared_root, session_id, 1, 3, True))
        _run_process(ctx, _reader_worker, (shared_root, session_id, 0, 100, out_queue))

        try:
            first_read = out_queue.get(timeout=3)
        except Empty as exc:
            raise AssertionError("first read result missing") from exc

        assert first_read["status"] == SimulationStatusEnum.RUNNING.value
        assert first_read["message_seqs"] == [1, 2, 3]
        assert first_read["offset"] == 3
        assert first_read["fault_count"] == 3

        _run_process(ctx, _writer_worker, (shared_root, session_id, 4, 2, False))
        _run_process(ctx, _reader_worker, (shared_root, session_id, first_read["offset"], 100, out_queue))

        try:
            second_read = out_queue.get(timeout=3)
        except Empty as exc:
            raise AssertionError("second read result missing") from exc

        assert second_read["status"] == SimulationStatusEnum.RUNNING.value
        assert second_read["message_seqs"] == [4, 5]
        assert second_read["offset"] == 5
        assert second_read["fault_count"] == 5
