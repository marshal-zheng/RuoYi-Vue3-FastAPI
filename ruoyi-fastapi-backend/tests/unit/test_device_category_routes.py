"""Exercise the registered router: static option routes must not be captured as ids."""

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from module_admin.controller.device_category_controller import device_category_router
from module_admin.service.device_category_service import DeviceCategoryService


@pytest.fixture
def category_app():
    app = FastAPI()
    app.include_router(device_category_router)
    service = AsyncMock(spec=DeviceCategoryService)
    service.get_device_category_options_services.return_value = [{'device_category_id': 8, 'name': 'Network'}]
    service.check_device_category_name_unique_services.return_value = True
    service.device_category_detail_services.return_value = {'device_category_id': 8, 'name': 'Network'}
    for route in app.routes:
        if isinstance(route, APIRoute):
            for dependency in route.dependant.dependencies:
                if dependency.name == 'device_category_service':
                    app.dependency_overrides[dependency.call] = lambda: service
                else:
                    app.dependency_overrides[dependency.call] = lambda: None
    return app, service


async def test_options_route_returns_collection_and_never_calls_detail(category_app):
    app, service = category_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/device/category/options')
    assert response.status_code == 200
    assert response.json() == {'items': [{'deviceCategoryId': 8, 'name': 'Network'}]}
    service.get_device_category_options_services.assert_awaited_once_with()
    service.device_category_detail_services.assert_not_awaited()


async def test_name_check_route_receives_excluded_category_id(category_app):
    app, service = category_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/device/category/checkNameUnique', params={'name': 'Network', 'category_id': 8})
    assert response.status_code == 200
    assert response.json() is True
    service.check_device_category_name_unique_services.assert_awaited_once_with('Network', 8)
    service.device_category_detail_services.assert_not_awaited()


async def test_numeric_detail_route_keeps_its_resource_contract(category_app):
    app, service = category_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/device/category/8')
    assert response.status_code == 200
    assert response.json() == {'deviceCategoryId': 8, 'name': 'Network'}
    service.device_category_detail_services.assert_awaited_once_with(8)
