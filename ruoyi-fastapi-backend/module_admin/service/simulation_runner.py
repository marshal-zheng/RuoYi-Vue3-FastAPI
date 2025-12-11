"""
SimPy 仿真运行器
在独立线程中运行 RealtimeEnvironment，支持暂停、继续、单步和速度调节
"""
import threading
import time
from queue import Queue, Empty
from typing import Callable, Optional

import simpy.rt


class SimulationRunner(threading.Thread):
    """
    仿真运行器
    通过线程隔离 SimPy 环境并提供控制指令队列
    """

    def __init__(
        self,
        session_id: str,
        topology_data: dict,
        tick_callback: Callable[[float], None],
        speed: float = 1.0,
        duration: Optional[float] = None,
        tick_interval: float = 0.1,
    ):
        super().__init__(daemon=True)
        self.session_id = session_id
        self.topology_data = topology_data or {}
        self.tick_callback = tick_callback
        self.tick_interval = max(0.05, tick_interval)

        # 控制参数
        self._duration = duration
        self._paused = threading.Event()
        self._stopped = threading.Event()
        self._paused.set()  # 运行态
        
        # 缓存目标速度（用于状态查询，避免异步延迟）
        self._target_speed = max(0.5, min(speed, 4.0))

        # 环境与指令
        self.env = simpy.rt.RealtimeEnvironment(factor=self._target_speed, strict=False)
        self.command_queue: Queue = Queue()

    def run(self):
        """主循环：按固定时间片推进 SimPy 环境"""
        self._setup_world()
        last_emit = time.time()

        while not self._stopped.is_set():
            self._process_commands()

            if not self._paused.is_set():
                time.sleep(0.05)
                continue

            # 使用更短的时间片，以便speed命令能更快生效
            # 每次只推进一小段时间，这样可以更频繁地检查命令队列
            step_size = min(self.tick_interval, 0.05)
            target_time = self.env.now + step_size
            
            # 在运行前再次处理命令，确保speed修改能立即生效
            self._process_commands()
            
            self.env.run(until=target_time)

            now = time.time()
            if now - last_emit >= self.tick_interval:
                self.tick_callback(self.env.now)
                last_emit = now

            if self._duration and self.env.now >= self._duration:
                self.stop()

    def pause(self):
        """暂停运行"""
        self._paused.clear()

    def resume(self):
        """继续运行"""
        self._paused.set()

    def stop(self):
        """停止运行"""
        self._stopped.set()
        self._paused.set()

    def set_speed(self, speed: float):
        """调节仿真速度（0.5x-4x）"""
        clamped = max(0.5, min(speed, 4.0))
        self._target_speed = clamped  # 立即缓存目标速度
        self.command_queue.put(("speed", clamped))

    def step_once(self):
        """单步执行一个时间片"""
        self.command_queue.put(("step", None))

    def set_duration(self, duration: Optional[float]):
        """设置自动停止时长"""
        self._duration = duration

    def get_status(self) -> dict:
        """返回当前状态"""
        return {
            "session_id": self.session_id,
            "status": "stopped" if self._stopped.is_set() else ("running" if self._paused.is_set() else "paused"),
            "env_now": self.env.now,
            "speed": self._target_speed,  # 返回缓存的目标速度，避免异步延迟
        }

    def _process_commands(self):
        """处理控制指令"""
        while True:
            try:
                cmd, payload = self.command_queue.get_nowait()
            except Empty:
                break

            if cmd == "speed":
                clamped_speed = max(0.5, min(float(payload), 4.0))
                # 直接修改factor属性，SimPy的RealtimeEnvironment支持动态修改
                self.env.factor = clamped_speed
            elif cmd == "step":
                self._paused.set()
                self.env.run(until=self.env.now + self.tick_interval)
                self.tick_callback(self.env.now)
                self._paused.clear()

    def _setup_world(self):
        """
        预留：根据拓扑构建进程与资源
        当前版本仅保留接口，实际设备进程由上层仿真引擎驱动
        """
        return None
