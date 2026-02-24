"""Saga engine with persistent state storage."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from ports import IRedisClient

SAGA_PENDING = 'PENDING'
SAGA_RUNNING = 'RUNNING'
SAGA_COMPLETED = 'COMPLETED'
SAGA_COMPENSATING = 'COMPENSATING'
SAGA_FAILED = 'FAILED'
SAGA_FAILED_MANUAL = 'FAILED_NEEDS_MANUAL_INTERVENTION'

STEP_PENDING = 'PENDING'
STEP_COMPLETED = 'COMPLETED'
STEP_COMPENSATING = 'COMPENSATING'
STEP_FAILED = 'FAILED'


@dataclass
class SagaStepDefinition:
    """One saga step with action and compensation."""

    name: str
    action: Callable[[Dict[str, Any]], Awaitable[Any]]
    compensate: Callable[[Dict[str, Any]], Awaitable[Any]]


class SagaStore:
    """Store interface for saga persistence."""

    async def save(self, instance: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def get(self, saga_id: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

    async def list(self, limit: int = 100) -> List[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError


class RedisSagaStore(SagaStore):
    """Redis-backed saga store."""

    def __init__(self, redis_client: IRedisClient, key_prefix: str = 'saga:instance') -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    def _key(self, saga_id: str) -> str:
        return f'{self._key_prefix}:{saga_id}'

    async def save(self, instance: Dict[str, Any]) -> None:
        await self._redis.set(self._key(instance['id']), json.dumps(instance, ensure_ascii=False))

    async def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        payload = await self._redis.get(self._key(saga_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        return json.loads(payload)

    async def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        keys = await self._redis.keys(f'{self._key_prefix}:*')
        ordered_keys = sorted(list(keys))[: max(limit, 1)]
        instances = []
        for key in ordered_keys:
            payload = await self._redis.get(key)
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            instances.append(json.loads(payload))
        instances.sort(key=lambda item: item.get('updatedAt', ''), reverse=True)
        return instances


class InMemorySagaStore(SagaStore):
    """Fallback store for test or degraded mode."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def save(self, instance: Dict[str, Any]) -> None:
        async with self._lock:
            self._data[instance['id']] = json.loads(json.dumps(instance, ensure_ascii=False))

    async def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            item = self._data.get(saga_id)
            if item is None:
                return None
            return json.loads(json.dumps(item, ensure_ascii=False))

    async def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        async with self._lock:
            values = list(self._data.values())
        values.sort(key=lambda item: item.get('updatedAt', ''), reverse=True)
        return values[: max(limit, 1)]


class SagaEngine:
    """Saga executor with compensation support."""

    def __init__(self, store: SagaStore) -> None:
        self._store = store

    async def execute(
        self,
        name: str,
        payload: Dict[str, Any],
        steps: Iterable[SagaStepDefinition],
    ) -> Dict[str, Any]:
        step_defs = list(steps)
        saga_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        instance = {
            'id': saga_id,
            'name': name,
            'status': SAGA_RUNNING,
            'payload': payload,
            'steps': [
                {
                    'name': step.name,
                    'status': STEP_PENDING,
                    'error': None,
                }
                for step in step_defs
            ],
            'error': None,
            'createdAt': now,
            'updatedAt': now,
        }
        await self._store.save(instance)

        completed_indices: List[int] = []
        for index, step in enumerate(step_defs):
            try:
                await step.action(payload)
                instance['steps'][index]['status'] = STEP_COMPLETED
                instance['updatedAt'] = datetime.utcnow().isoformat()
                completed_indices.append(index)
                await self._store.save(instance)
            except Exception as exc:
                instance['steps'][index]['status'] = STEP_FAILED
                instance['steps'][index]['error'] = str(exc)
                instance['status'] = SAGA_COMPENSATING
                instance['error'] = str(exc)
                instance['updatedAt'] = datetime.utcnow().isoformat()
                await self._store.save(instance)

                compensation_failed = await self._compensate(instance, step_defs, completed_indices)
                if compensation_failed:
                    instance['status'] = SAGA_FAILED_MANUAL
                else:
                    instance['status'] = SAGA_FAILED
                instance['updatedAt'] = datetime.utcnow().isoformat()
                await self._store.save(instance)
                return instance

        instance['status'] = SAGA_COMPLETED
        instance['updatedAt'] = datetime.utcnow().isoformat()
        await self._store.save(instance)
        return instance

    async def _compensate(
        self,
        instance: Dict[str, Any],
        step_defs: List[SagaStepDefinition],
        completed_indices: List[int],
    ) -> bool:
        compensation_failed = False
        for index in reversed(completed_indices):
            step = step_defs[index]
            try:
                instance['steps'][index]['status'] = STEP_COMPENSATING
                instance['updatedAt'] = datetime.utcnow().isoformat()
                await self._store.save(instance)

                await step.compensate(instance['payload'])
                instance['steps'][index]['status'] = STEP_FAILED
                instance['steps'][index]['error'] = 'compensated'
                instance['updatedAt'] = datetime.utcnow().isoformat()
                await self._store.save(instance)
            except Exception as exc:
                compensation_failed = True
                instance['steps'][index]['status'] = STEP_FAILED
                instance['steps'][index]['error'] = f'compensate_failed:{exc}'
                instance['updatedAt'] = datetime.utcnow().isoformat()
                await self._store.save(instance)
        return compensation_failed

    async def list_instances(self, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._store.list(limit=limit)

    async def get_instance(self, saga_id: str) -> Optional[Dict[str, Any]]:
        return await self._store.get(saga_id)

    async def compensate(self, saga_id: str) -> Dict[str, Any]:
        instance = await self._store.get(saga_id)
        if instance is None:
            raise ValueError(f'saga not found: {saga_id}')

        instance['status'] = SAGA_COMPENSATING
        instance['updatedAt'] = datetime.utcnow().isoformat()
        for step in reversed(instance.get('steps', [])):
            if step.get('status') == STEP_COMPLETED:
                step['status'] = STEP_COMPENSATING
                step['error'] = 'manual_compensation_requested'
        await self._store.save(instance)

        instance['status'] = SAGA_FAILED_MANUAL
        instance['updatedAt'] = datetime.utcnow().isoformat()
        await self._store.save(instance)
        return instance
