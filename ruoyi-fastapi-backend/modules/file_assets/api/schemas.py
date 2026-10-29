"""Public file asset DTOs (camelCase JSON); bucket, key and storage details are never exposed."""

from __future__ import annotations

from pydantic import Field

from module_admin.entity.vo.base import CamelModelBase


class AssetDescriptorModel(CamelModelBase):
    asset_id: str = Field(description='资产ID（UUID）')
    name: str = Field(description='安全显示名')
    media_type: str = Field(description='登记的规范媒体类型')
    size: int = Field(description='存储字节数')
    content_url: str = Field(description='稳定同源内容地址，每次使用都鉴权')


class AssetMetadataBatchRequest(CamelModelBase):
    asset_ids: list[str] = Field(max_length=100, description='资产ID列表，最多 100 个')


class AssetMetadataBatchResponse(CamelModelBase):
    items: list[AssetDescriptorModel] = Field(description='按输入顺序返回当前可见的资产')
    unavailable_ids: list[str] = Field(description='不存在或不可见的资产ID（不区分原因）')


class AvatarUploadResponse(CamelModelBase):
    avatar_asset_id: str = Field(description='头像资产ID')
    avatar_url: str = Field(description='头像稳定内容地址')


def descriptor_model(descriptor) -> AssetDescriptorModel:
    return AssetDescriptorModel(
        asset_id=descriptor.asset_id,
        name=descriptor.name,
        media_type=descriptor.media_type,
        size=descriptor.size,
        content_url=descriptor.content_url,
    )


UPLOAD_REQUEST_BODY = {
    'requestBody': {
        'required': True,
        'content': {
            'multipart/form-data': {
                'schema': {
                    'title': 'FileAssetUploadForm',
                    'type': 'object',
                    'required': ['file', 'purpose'],
                    'properties': {
                        'file': {'type': 'string', 'format': 'binary', 'description': '单个文件'},
                        'purpose': {'type': 'string', 'maxLength': 64, 'description': '服务端登记的上传用途'},
                        'ownerId': {
                            'type': 'string',
                            'maxLength': 128,
                            'description': '编辑已有业务对象时的业务ID，新建时省略',
                        },
                    },
                }
            }
        },
    }
}

AVATAR_REQUEST_BODY = {
    'requestBody': {
        'required': True,
        'content': {
            'multipart/form-data': {
                'schema': {
                    'title': 'AvatarUploadForm',
                    'type': 'object',
                    'required': ['avatarfile'],
                    'properties': {'avatarfile': {'type': 'string', 'format': 'binary', 'description': '头像图片'}},
                }
            }
        },
    }
}

CONTENT_RESPONSES = {
    200: {
        'description': '文件内容（图片用途 inline，其余 attachment）',
        'content': {'application/octet-stream': {'schema': {'type': 'string', 'format': 'binary'}}},
    },
    304: {'description': 'If-None-Match 命中（已鉴权，不访问存储）'},
}
