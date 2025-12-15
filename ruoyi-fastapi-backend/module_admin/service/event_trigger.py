"""
事件触发服务
管理事件配置并在仿真运行中检查触发条件
支持设备间指令发送、自检、上电等人为动作触发
"""
import time
import uuid
from typing import Dict, List, Optional, Callable


class EventTriggerService:
    """
    事件触发器（内存实现）
    在每个 tick 中检查事件条件并执行动作回调
    支持手动触发和条件触发
    """

    def __init__(self):
        # {session_id: {event_id: event_data}}
        self._events: Dict[str, Dict[str, dict]] = {}
        # 动作执行回调
        self._action_executor: Optional[Callable[[str, dict], dict]] = None

    def set_action_executor(self, executor: Callable[[str, dict], dict]):
        """设置动作执行器回调"""
        self._action_executor = executor

    def add_event(self, session_id: str, event: dict) -> dict:
        event_id = event.get("event_id") or str(uuid.uuid4())
        
        # 解析条件配置
        condition = event.get("condition", {})
        if not condition and event.get("conditionType"):
            condition = {
                "type": event.get("conditionType"),
                "value": event.get("conditionValue", {})
            }
        
        # 解析动作配置
        action = event.get("action", {})
        if not action and event.get("actionType"):
            action = {
                "type": event.get("actionType"),
                "params": event.get("actionParams", {})
            }
        
        event_data = {
            "event_id": event_id,
            "session_id": session_id,
            "name": event.get("name", "事件"),
            "condition": condition,
            "action": action,
            "status": "pending",
            "trigger_count": 0,
            "last_trigger_time": None,
            "create_time": time.time(),
        }
        if session_id not in self._events:
            self._events[session_id] = {}
        self._events[session_id][event_id] = event_data
        return event_data

    def update_event(self, session_id: str, event_id: str, updates: dict) -> Optional[dict]:
        """
        更新事件配置
        
        参数:
            session_id: 会话ID
            event_id: 事件ID
            updates: 更新内容
            
        返回:
            更新后的事件数据，不存在返回 None
        """
        if session_id not in self._events or event_id not in self._events[session_id]:
            return None
        
        event = self._events[session_id][event_id]
        
        # 更新名称
        if "name" in updates:
            event["name"] = updates["name"]
        
        # 更新条件
        if "condition" in updates:
            event["condition"] = updates["condition"]
        elif updates.get("conditionType"):
            event["condition"] = {
                "type": updates.get("conditionType"),
                "value": updates.get("conditionValue", {})
            }
        
        # 更新动作
        if "action" in updates:
            event["action"] = updates["action"]
        elif updates.get("actionType"):
            event["action"] = {
                "type": updates.get("actionType"),
                "params": updates.get("actionParams", {})
            }
        
        # 更新状态
        if "status" in updates:
            event["status"] = updates["status"]
        
        return event

    def trigger_event(self, session_id: str, event_id: str) -> Optional[dict]:
        """
        手动触发事件
        
        参数:
            session_id: 会话ID
            event_id: 事件ID
            
        返回:
            触发结果，包含执行的动作结果
        """
        if session_id not in self._events or event_id not in self._events[session_id]:
            return None
        
        event = self._events[session_id][event_id]
        now = time.time()
        
        # 更新触发状态
        event["status"] = "triggered"
        event["trigger_count"] += 1
        event["last_trigger_time"] = now
        
        # 执行动作
        action = event.get("action", {})
        action_result = None
        if action and self._action_executor:
            action_result = self._action_executor(session_id, action)
        
        return {
            "event_id": event_id,
            "name": event["name"],
            "action": action,
            "action_result": action_result,
            "trigger_time": now,
            "trigger_count": event["trigger_count"],
        }

    def remove_event(self, session_id: str, event_id: str) -> bool:
        if session_id in self._events and event_id in self._events[session_id]:
            del self._events[session_id][event_id]
            return True
        return False

    def list_events(self, session_id: str) -> List[dict]:
        return list(self._events.get(session_id, {}).values())
    
    def get_event(self, session_id: str, event_id: str) -> Optional[dict]:
        """获取单个事件"""
        if session_id in self._events:
            return self._events[session_id].get(event_id)
        return None

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
        检查并触发事件（条件触发）
        """
        triggered = []
        events = self._events.get(session_id, {})
        for event in events.values():
            if event["status"] == "disabled":
                continue
            # 已触发的事件不再自动触发（但可以手动触发）
            if event["status"] == "triggered":
                continue

            matched = self._match_condition(event.get("condition", {}), now, message_count, bandwidth_snapshot)
            if condition_matcher:
                matched = matched or condition_matcher(event, bandwidth_snapshot)

            if matched:
                event["status"] = "triggered"
                event["trigger_count"] += 1
                event["last_trigger_time"] = now
                triggered.append(event)
                
                # 执行动作
                action = event.get("action", {})
                if action:
                    if self._action_executor:
                        self._action_executor(session_id, action)
                    elif action_executor:
                        action_executor(action)
        return triggered

    def _match_condition(
        self, condition: dict, now: float, message_count: int, bandwidth_snapshot: List[dict]
    ) -> bool:
        ctype = condition.get("type")
        value = condition.get("value", {})
        
        # 兼容两种格式：value 可能是字典或直接值
        if isinstance(value, dict):
            time_val = value.get("time", 0)
            count_val = value.get("count", 0)
            threshold_val = value.get("threshold", 0)
        else:
            time_val = value
            count_val = value
            threshold_val = value

        if ctype == "time":
            return now >= float(time_val or 0)
        if ctype == "message_count":
            return message_count >= int(count_val or 0)
        if ctype == "bandwidth_threshold":
            threshold = float(threshold_val or 0)
            return any(point.get("bandwidth_mbps", 0) >= threshold for point in bandwidth_snapshot)
        if ctype == "message_content":
            # 报文内容匹配需要在消息处理时检查，这里只返回 False
            return False
        return False
    
    def reset_event(self, session_id: str, event_id: str) -> bool:
        """
        重置事件状态为待触发
        
        参数:
            session_id: 会话ID
            event_id: 事件ID
            
        返回:
            是否成功
        """
        if session_id in self._events and event_id in self._events[session_id]:
            self._events[session_id][event_id]["status"] = "pending"
            return True
        return False
    
    def clear_session_events(self, session_id: str):
        """清除会话的所有事件"""
        if session_id in self._events:
            del self._events[session_id]
