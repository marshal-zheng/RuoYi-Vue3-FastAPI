"""
故障注入服务（真实仿真版）
支持链路/节点级故障、丢包、延时、带宽限制、数据篡改等
"""
import random
import time
import uuid
from typing import Dict, List, Optional, Tuple


class FaultInjector:
    """
    维护会话故障状态，提供判定与增量事件
    """

    def __init__(self):
        # 故障表: {session_id: {fault_id: fault_data}}
        self._faults: Dict[str, Dict[str, dict]] = {}
        # 事件表: {session_id: [event...]}
        self._fault_events: Dict[str, List[dict]] = {}
        # 速率状态: {session_id: {target_id: {'last': ts, 'interval': sec}}}
        self._rate_state: Dict[str, Dict[str, dict]] = {}
        # 目标索引: {session_id: {'edge': {edge_id: set(fault_id)}, 'node': {...}, 'port': {...}}}
        self._fault_index: Dict[str, Dict[str, Dict[str, set]]] = {}

    # ==================== 公共接口 ====================
    def inject_fault(self, session_id: str, fault_type: str, target_id: str, params: Optional[dict] = None) -> dict:
        """
        新增/更新故障规则；支持延迟生效与持续时长
        幂等逻辑：同session+target+type的active/pending故障会更新而非新增
        """
        params = params or {}
        now = self._now()
        normalized_params = self._normalize_params(params)

        priority = int(normalized_params.get("priority", 0))
        target_type = (normalized_params.get("target_type") or "edge").lower()
        targets = self._extract_targets(target_type, target_id, normalized_params)

        start_after = float(normalized_params.get("start_after_ms", 0)) / 1000.0
        duration = normalized_params.get("duration_ms")
        start_at = now + max(0.0, start_after)
        end_at = start_at + (float(duration) / 1000.0) if duration is not None else None

        session_faults = self._faults.setdefault(session_id, {})

        # 幂等查找：按 target_id + fault_type 查找现有的 active/pending 故障
        existing = self._find_existing_fault(session_id, target_id, fault_type)
        
        if existing:
            # 更新现有故障的参数，重置计时
            self._remove_from_index(session_id, existing)
            existing.update(
                {
                    "fault_type": fault_type,
                    "target_type": target_type,
                    "target_id": target_id,
                    "targets": targets,
                    "target_name": normalized_params.get("target_name") or normalized_params.get("targetName"),
                    "params": normalized_params,
                    "priority": priority,
                    "start_at": start_at,
                    "end_at": end_at,
                    "status": "pending" if start_after > 0 else "active",
                    "update_time": now,
                    "_action": "updated",  # 标识为更新操作
                }
            )
            self._index_fault(session_id, existing)
            self._append_event(session_id, "updated", existing)
            return existing

        # 新增故障
        fault_id = normalized_params.get("fault_id") or str(uuid.uuid4())
        fault = {
            "fault_id": fault_id,
            "session_id": session_id,
            "fault_type": fault_type,
            "target_type": target_type,
            "target_id": target_id,
            "targets": targets,
            "target_name": normalized_params.get("target_name") or normalized_params.get("targetName"),
            "params": normalized_params,
            "priority": priority,
            "status": "pending" if start_after > 0 else "active",
            "create_time": now,
            "start_at": start_at,
            "end_at": end_at,
            "_action": "created",  # 标识为新增操作
        }
        session_faults[fault_id] = fault
        self._index_fault(session_id, fault)
        self._append_event(session_id, "created", fault)
        return fault

    def _find_existing_fault(self, session_id: str, target_id: str, fault_type: str) -> Optional[dict]:
        """
        查找同 target_id + fault_type 的 active/pending 故障
        """
        session_faults = self._faults.get(session_id, {})
        for fault in session_faults.values():
            if fault.get("status") not in ("active", "pending"):
                continue
            if fault.get("target_id") == target_id and fault.get("fault_type") == fault_type:
                return fault
        return None

    def clear_fault(self, session_id: str, fault_id: str) -> bool:
        faults = self._faults.get(session_id, {})
        if fault_id in faults:
            faults[fault_id]["status"] = "cleared"
            self._append_event(session_id, "cleared", faults[fault_id])
            self._remove_from_index(session_id, faults[fault_id])
            return True
        return False

    def clear_all_faults(self, session_id: str) -> int:
        """
        清除指定 session 的所有 active/pending 故障
        @return: 清除的故障数量
        """
        faults = list(self._faults.get(session_id, {}).values())
        cleared_count = 0
        for fault in faults:
            if fault.get("status") in ("active", "pending"):
                fault["status"] = "cleared"
                self._append_event(session_id, "cleared", fault)
                self._remove_from_index(session_id, fault)
                cleared_count += 1

        # 清理索引与速率状态，避免残留引用
        if session_id in self._fault_index:
            self._fault_index[session_id] = {"edge": {}, "node": {}, "port": {}}
        if session_id in self._rate_state:
            self._rate_state.pop(session_id, None)
        return cleared_count

    def clear_faults_by_target(self, session_id: str, target_id: str) -> int:
        """
        清除指定 session 和 target 的所有 active/pending 故障
        @return: 清除的故障数量
        """
        faults = self._faults.get(session_id, {})
        cleared_count = 0
        for fault in faults.values():
            if fault.get("target_id") != target_id:
                continue
            if fault.get("status") in ("active", "pending"):
                fault["status"] = "cleared"
                self._append_event(session_id, "cleared", fault)
                self._remove_from_index(session_id, fault)
                cleared_count += 1
        return cleared_count

    def list_faults(self, session_id: str) -> List[dict]:
        self._refresh_status(session_id)
        return list(self._faults.get(session_id, {}).values())

    def get_new_events(self, session_id: str, offset: int) -> Tuple[List[dict], int]:
        events = self._fault_events.get(session_id, [])
        if offset < 0:
            offset = 0
        if offset > len(events):
            offset = len(events)
        new_events = events[offset:]
        return new_events, len(events)

    # ==================== 判定逻辑 ====================
    def apply_effects(self, session_id: str, edge_id: str, message: dict) -> dict:
        """
        应用故障效果，返回 {drop: bool, delay: float, payload_hex: str, reasons: List[str]}
        """
        self._refresh_status(session_id)
        sender = message.get("sender_node_id") or message.get("senderNodeId")
        receiver = message.get("receiver_node_id") or message.get("receiverNodeId")
        sender_port = message.get("sender_port_id") or message.get("senderPortId")
        receiver_port = message.get("receiver_port_id") or message.get("receiverPortId")

        active_faults = self._pick_faults(session_id, edge_id, sender, receiver, sender_port, receiver_port)

        drop = False
        delay_sec = 0.0
        payload_hex = message.get("payload_hex") or message.get("payloadHex") or ""
        reasons = []
        error_frame = False

        for fault in active_faults:
            ftype = fault["fault_type"]
            params = fault.get("params", {})

            if ftype == "disconnect":
                drop = True
                reasons.append("disconnect")
                break

            if ftype == "device_failure":
                drop = True
                reasons.append("device_failure")
                break

            if ftype == "packet_loss":
                rate = params.get("loss_rate", 0.0)
                if random.random() < max(0.0, min(rate, 1.0)):
                    drop = True
                    reasons.append("packet_loss")
                    break

            if ftype == "delay":
                delay_ms = params.get("delay_ms", 0.0)
                jitter_ms = params.get("jitter_ms", 0.0)
                jitter = random.uniform(-jitter_ms, jitter_ms) if jitter_ms else 0.0
                delay_sec += max(0.0, delay_ms + jitter) / 1000.0
                reasons.append("delay")

            if ftype == "bandwidth_limit":
                if self._hit_rate_limit(session_id, params.get("rate_key") or edge_id, params):
                    drop = True
                    reasons.append("bandwidth_limit")
                    break

            if ftype == "payload_corrupt":
                payload_hex = self._mutate_payload(payload_hex, params)
                reasons.append("payload_corrupt")

            if ftype == "noise_frame":
                payload_hex = self._noise_payload(payload_hex, params)
                reasons.append("noise_frame")

            if ftype == "error_frame":
                error_frame = True
                reasons.append("error_frame")

        return {
            "drop": drop,
            "delay": delay_sec,
            "payload_hex": payload_hex,
            "error_frame": error_frame,
            "reasons": reasons,
        }

    def should_drop(self, session_id: str, edge_id: str) -> bool:
        result = self.apply_effects(session_id, edge_id, {})
        return result["drop"]

    def get_delay(self, session_id: str, edge_id: str) -> float:
        result = self.apply_effects(session_id, edge_id, {})
        return result["delay"]

    def is_disconnected(self, session_id: str, edge_id: str) -> bool:
        self._refresh_status(session_id)
        for fault in self._iter_faults(session_id):
            targets = fault.get("targets") or {}
            hit = edge_id == fault.get("target_id") or edge_id in targets.get("edge", set())
            if fault["fault_type"] == "disconnect" and hit:
                return True
        return False

    def is_device_failed(self, session_id: str, node_id: str) -> bool:
        self._refresh_status(session_id)
        for fault in self._iter_faults(session_id):
            targets = fault.get("targets") or {}
            hit = node_id == fault.get("target_id") or node_id in targets.get("node", set())
            if fault["fault_type"] == "device_failure" and hit:
                return True
        return False

    # ==================== 辅助方法 ====================
    def _refresh_status(self, session_id: str) -> None:
        now = self._now()
        session_faults = self._faults.get(session_id, {})
        for fault in session_faults.values():
            if fault["status"] == "cleared":
                continue
            if fault["status"] == "pending" and now >= fault["start_at"]:
                fault["status"] = "active"
                self._append_event(session_id, "activated", fault)
                self._index_fault(session_id, fault)
            if fault.get("end_at") and now >= fault["end_at"] and fault["status"] == "active":
                fault["status"] = "expired"
                self._append_event(session_id, "expired", fault)
                self._remove_from_index(session_id, fault)

    def _iter_faults(self, session_id: str):
        for fault in self._faults.get(session_id, {}).values():
            if fault["status"] != "active":
                continue
            yield fault

    def _pick_faults(
        self,
        session_id: str,
        edge_id: Optional[str],
        sender: Optional[str],
        receiver: Optional[str],
        sender_port: Optional[str],
        receiver_port: Optional[str],
    ) -> List[dict]:
        idx = self._fault_index.get(session_id, {})
        candidates: List[dict] = []
        session_faults = self._faults.get(session_id, {})

        def _collect(ids: List[str], key: str):
            for _id in ids:
                if not _id:
                    continue
                fault_ids = idx.get(key, {}).get(_id, set())
                for fid in fault_ids:
                    fault = session_faults.get(fid)
                    if fault and fault.get("status") == "active":
                        candidates.append(fault)

        _collect([edge_id], "edge")
        _collect([sender, receiver], "node")
        _collect([sender_port, receiver_port], "port")

        if not candidates:
            candidates = list(self._iter_faults(session_id))

        candidates = sorted(
            candidates,
            key=lambda f: (-int(f.get("priority", 0)), f.get("start_at", 0)),
        )
        return candidates

    def _append_event(self, session_id: str, action: str, fault: dict) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "action": action,
            "fault": fault,
            "timestamp": self._now(),
        }
        self._fault_events.setdefault(session_id, []).append(event)

    def _hit_rate_limit(self, session_id: str, target_id: str, params: dict) -> bool:
        qps = params.get("messages_per_second")
        if not qps:
            return False
        interval = 1.0 / max(0.1, float(qps))
        now = self._now()
        state = self._rate_state.setdefault(session_id, {}).setdefault(target_id, {"last": 0.0, "interval": interval})
        state["interval"] = interval
        if now - state["last"] < interval:
            return True
        state["last"] = now
        return False

    def _mutate_payload(self, payload_hex: str, params: dict) -> str:
        if not payload_hex:
            return payload_hex
        bit_flip_count = int(params.get("bit_flip_count", 1))
        if bit_flip_count <= 0:
            return payload_hex
        try:
            data = bytearray.fromhex(payload_hex)
        except Exception:
            return payload_hex

        for _ in range(min(bit_flip_count, len(data) * 8)):
            byte_idx = random.randint(0, len(data) - 1)
            bit_idx = random.randint(0, 7)
            data[byte_idx] ^= 1 << bit_idx
        return data.hex().upper()

    def _noise_payload(self, payload_hex: str, params: dict) -> str:
        length = len(payload_hex) // 2 if payload_hex else int(params.get("length", 8))
        length = max(1, min(length, 64))
        return "".join(f"{random.randint(0, 255):02X}" for _ in range(length))

    @staticmethod
    def _normalize_params(params: dict) -> dict:
        normalized = dict(params)
        if "lossRate" in normalized:
            normalized["loss_rate"] = float(normalized.pop("lossRate")) / 100.0
        if "loss_rate" in normalized and normalized["loss_rate"] > 1:
            normalized["loss_rate"] = normalized["loss_rate"] / 100.0
        if "delayMs" in normalized:
            normalized["delay_ms"] = float(normalized.pop("delayMs"))
        if "jitterMs" in normalized:
            normalized["jitter_ms"] = float(normalized.pop("jitterMs"))
        if "messagesPerSecond" in normalized:
            normalized["messages_per_second"] = float(normalized.pop("messagesPerSecond"))
        if "bitFlipCount" in normalized:
            normalized["bit_flip_count"] = int(normalized.pop("bitFlipCount"))
        if "durationMs" in normalized:
            normalized["duration_ms"] = float(normalized.pop("durationMs"))
        if "startAfterMs" in normalized:
            normalized["start_after_ms"] = float(normalized.pop("startAfterMs"))
        if "priority" in normalized:
            normalized["priority"] = int(normalized.get("priority", 0))
        return normalized

    def _extract_targets(self, target_type: str, target_id: str, params: dict) -> Dict[str, set]:
        targets = {"edge": set(), "node": set(), "port": set()}
        if target_type not in targets:
            target_type = "edge"
        if target_id:
            targets[target_type].add(str(target_id))

        def _collect(key: str, tkey: str):
            ids = params.get(key)
            if ids is None:
                return
            if not isinstance(ids, list):
                ids = [ids]
            for _id in ids:
                targets[tkey].add(str(_id))

        _collect("edge_ids", "edge")
        _collect("node_ids", "node")
        _collect("port_ids", "port")
        return targets

    def _index_fault(self, session_id: str, fault: dict) -> None:
        if fault.get("status") != "active" and fault.get("status") != "pending":
            return
        idx = self._fault_index.setdefault(session_id, {"edge": {}, "node": {}, "port": {}})
        targets = fault.get("targets") or {}
        for key in ("edge", "node", "port"):
            for tid in targets.get(key, []):
                idx[key].setdefault(tid, set()).add(fault["fault_id"])

    def _remove_from_index(self, session_id: str, fault: dict) -> None:
        idx = self._fault_index.get(session_id, {})
        targets = fault.get("targets") or {}
        for key in ("edge", "node", "port"):
            for tid in targets.get(key, []):
                if tid in idx.get(key, {}):
                    idx[key][tid].discard(fault["fault_id"])
                    if not idx[key][tid]:
                        idx[key].pop(tid, None)


    @staticmethod
    def _now() -> float:
        return time.time()
