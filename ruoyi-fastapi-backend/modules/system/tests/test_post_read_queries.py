from __future__ import annotations

import pytest

from module_admin.entity.vo.post_vo import PostPageQueryModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.post_query_handlers import (
    GetPostDetailQueryHandler,
    GetPostListQueryHandler,
)
from modules.system.application.queries import GetPostDetailQuery, GetPostListQuery
from modules.system.application.read_models import (
    PostDetailReadModel,
    PostItemReadModel,
    PostPageReadModel,
)
from utils.page_util import PageResponseModel


class _PostServiceStub:
    def __init__(self) -> None:
        self.list_called_with = None
        self.detail_called_with = None

    async def get_post_list_services(self, query, is_page=False):
        self.list_called_with = (query, is_page)
        if is_page:
            return PageResponseModel(
                items=[
                    {
                        'postId': 1,
                        'postCode': 'dev',
                        'postName': '研发工程师',
                        'postSort': 1,
                        'status': '0',
                    }
                ],
                page=1,
                page_size=10,
                total=1,
                has_next=False,
            )
        return [
            {
                'postId': 1,
                'postCode': 'dev',
                'postName': '研发工程师',
                'postSort': 1,
                'status': '0',
            }
        ]

    async def post_detail_services(self, post_id):
        self.detail_called_with = post_id
        return {
            'postId': post_id,
            'postCode': 'dev',
            'postName': '研发工程师',
            'postSort': 1,
            'status': '0',
        }


@pytest.mark.asyncio
async def test_post_query_handlers_success() -> None:
    post_service = _PostServiceStub()
    list_handler = GetPostListQueryHandler(post_service)
    detail_handler = GetPostDetailQueryHandler(post_service)

    list_result = await list_handler.handle(
        GetPostListQuery(
            query=PostPageQueryModel(page=1, pageSize=10),
            is_page=True,
            operator='admin',
        )
    )
    detail_result = await detail_handler.handle(GetPostDetailQuery(post_id=1, operator='admin'))

    assert isinstance(list_result, PostPageReadModel)
    assert isinstance(list_result.items[0], PostItemReadModel)
    assert isinstance(detail_result, PostDetailReadModel)
    assert list_result.items[0].post_code == 'dev'
    assert detail_result.post_id == 1


@pytest.mark.asyncio
async def test_system_mediator_dispatches_post_read_queries() -> None:
    post_service = _PostServiceStub()
    mediator = provide_system_mediator(post_service=post_service)

    list_result = await mediator.query(
        GetPostListQuery(
            query=PostPageQueryModel(page=1, pageSize=10),
            is_page=True,
        )
    )
    detail_result = await mediator.query(GetPostDetailQuery(post_id=1))

    assert isinstance(list_result, PostPageReadModel)
    assert isinstance(detail_result, PostDetailReadModel)
    assert list_result.items[0].post_code == 'dev'
