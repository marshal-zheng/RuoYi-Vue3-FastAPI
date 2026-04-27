"""Cross-module event handlers wired through ports contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from module_admin.entity.vo.project_vo import ProjectPageQueryModel
from ports import IProjectService
from utils.log_util import logger

if TYPE_CHECKING:
    from container import AppContainer
    from events.domain_events import DomainEvent


class ProjectReadSideProjectionHandler:
    """Sample cross-module orchestration handler using project ports."""

    def __init__(self, container: 'AppContainer') -> None:
        self._container = container

    async def __call__(self, event: 'DomainEvent') -> None:
        user_ids = event.payload.get('user_ids')
        if not user_ids:
            return

        async with self._container.create_task_session() as task_session:
            project_service: IProjectService = self._container.resolve_service('project_service', task_session)
            project_result = await project_service.get_project_list_services(
                ProjectPageQueryModel(page=1, pageSize=1),
                is_page=True,
            )
            project_total = int(getattr(project_result, 'total', 0) or 0)
            logger.bind(
                event='event_handler_project_projection',
                event_id=event.event_id,
                trace_id=event.metadata.get('trace_id'),
                user_ids=user_ids,
                project_total=project_total,
            ).info('event_handler_project_projection_synced')
