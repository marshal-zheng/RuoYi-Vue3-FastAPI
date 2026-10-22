import pytest
from pydantic import ValidationError

from common.remark_document_v1 import plain_to_remark
from module_admin.entity.vo.post_vo import PostModel, PostQueryModel
from module_admin.entity.vo.user_vo import UserDetailModel, UserInfoModel
from module_admin.entity.vo.user_write_vo import UserUpdateModel
from modules.system.application.read_models.post_read_models import PostDetailReadModel


def test_json_writes_preserve_document_and_explicit_null_and_omission():
    raw = plain_to_remark('line\n\n ', identity_key='sys_user:8:remark')
    value = UserUpdateModel(userId=8, remark=raw)
    assert value.model_dump(exclude_unset=True)['remark'] == raw
    assert 'remark' not in UserUpdateModel(userId=8).model_dump(exclude_unset=True)
    assert UserUpdateModel(userId=8, remark=None).model_dump(exclude_unset=True)['remark'] is None
    with pytest.raises(ValidationError):
        UserUpdateModel(userId=8, remark='old text')
    with pytest.raises(ValidationError):
        PostModel(postId=1, remarkText='forged')
    assert 'remark' not in PostQueryModel.model_fields
    output = PostDetailReadModel(postId=1, remark=raw).model_dump(by_alias=True)
    assert output['remarkText'] == 'line\n\n '


def test_legacy_identity_and_user_detail_nested_reads_keep_server_projection():
    raw = plain_to_remark('nested role/post', identity_key='nested:8:remark')
    user = UserInfoModel(userId=8, role=[{'roleId': 2, 'remark': raw}])
    assert user.model_dump(by_alias=True)['role'][0]['remarkText'] == 'nested role/post'
    detail = UserDetailModel(
        data=user,
        posts=[{'postId': 4, 'remark': raw}],
        roles=[{'roleId': 2, 'remark': raw}],
    ).model_dump(by_alias=True)
    assert detail['posts'][0]['remarkText'] == 'nested role/post'
    assert detail['roles'][0]['remarkText'] == 'nested role/post'
