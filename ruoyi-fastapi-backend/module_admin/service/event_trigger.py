"""
事件触发服务
管理事件配置并在仿真运行中检查触发条件
"""
import time
import uuid
from typing import Dict, List, Optional, Callable


class EventTriggerService:
    """
    事件触发器（内存实现）
    在每个 tick 中检查事件条件并执行动作回调
    """

    def __init__(self):
        # {session_id: {event_id: event_data}}
        self._events: Dict[str, Dict[str, dict]] = {}

    def add_event(self, session_id: str, event: dict) -> dict:
        event_id = event.get("event_id") or str(uuid.uuid4())
        event_data = {
            "event_id": event_id,
            "session_id": session_id,
            "name": event.get("name", "事件"),
            "condition": event.get("condition", {}),
            "action": event.get("action", {}),
            "status": "pending",
            "trigger_count": 0,
            "last_trigger_time": None,
            "create_time": time.time(),
        }
        if session_id not in self._events:
            self._events[session_id] = {}
        self._events[session_id][event_id] = event_data
        return event_data

    def remove_event(self, session_id: str, event_id: str) -> bool:
        if session_id in self._events and event_id in self._events[session_id]:
            del self._events[session_id][event_id]
            return True
        return False

    def list_events(self, session_id: str) -> List[dict]:
        return list(self._events.get(session_id, {}).values())

    def evaluate(
        self,
        session_id: str,
        now: float,
        message_count: int,
        bandwidth_snapshot: List[dict],
        condition_matcher: Optional[Callable[[dict, List[dict]], bool]] = None,
        action_executor: Optional[Callable[[dict], None]] = None,
    ) -> List[dict]:
        """
        检查并触发事件
        """
        triggered = []
        events = self._events.get(session_id, {})
        for event in events.values():
            if event["status"] == "disabled":
                continue

            matched = self._match_condition(event.get("condition", {}), now, message_count, bandwidth_snapshot)
            if condition_matcher:
                matched = matched or condition_matcher(event, bandwidth_snapshot)

            if matched:
                event["status"] = "triggered"
                event["trigger_count"] += 1
                event["last_trigger_time"] = now
                triggered.append(event)
                if action_executor:
                    action_executor(event.get("action", {}))
        return triggered

    def _match_condition(
        self, condition: dict, now: float, message_count: int, bandwidth_snapshot: List[dict]
    ) -> bool:
        ctype = condition.get("type")
        value = condition.get("value")

        if ctype == "time":
            return now >= float(value)
        if ctype == "message_count":
            return message_count >= int(value or 0)
        if ctype == "bandwidth_threshold":
            threshold = float(value or 0)
            return any(point.get("bandwidth_mbps", 0) >= threshold for point in bandwidth_snapshot)
        if ctype == "message_content":
            keyword = str(value or "").lower()
            return bool(keyword)
        return False
