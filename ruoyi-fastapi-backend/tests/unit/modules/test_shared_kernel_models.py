from __future__ import annotations

from shared.kernel import ApiResponse, PageResponse


def test_api_response_model_dump_uses_camel_alias() -> None:
    response = ApiResponse[dict](code=200, msg='ok', data={'user_name': 'alice'})

    payload = response.model_dump(by_alias=True)

    assert payload['code'] == 200
    assert payload['msg'] == 'ok'
    assert payload['data']['user_name'] == 'alice'



def test_page_response_defaults() -> None:
    response = PageResponse[int](rows=[1, 2, 3], total=3)

    payload = response.model_dump(by_alias=True)

    assert payload == {
        'rows': [1, 2, 3],
        'total': 3,
        'code': 200,
        'msg': 'success',
    }
