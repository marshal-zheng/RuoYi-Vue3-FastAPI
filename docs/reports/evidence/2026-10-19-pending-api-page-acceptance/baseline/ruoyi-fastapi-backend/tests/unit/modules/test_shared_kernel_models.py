from __future__ import annotations

from shared.kernel import PageResponse, ResourceResponse


def test_resource_response_model_dump_uses_camel_alias() -> None:
    response = ResourceResponse[dict](data={'user_name': 'alice'})

    payload = response.model_dump(by_alias=True)

    assert payload['data']['user_name'] == 'alice'



def test_page_response_defaults() -> None:
    response = PageResponse[int](items=[1, 2, 3], total=3, page=2, pageSize=20)

    payload = response.model_dump(by_alias=True)

    assert payload == {
        'items': [1, 2, 3],
        'total': 3,
        'page': 2,
        'pageSize': 20,
    }
