from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModelBase(BaseModel):
    """
    统一的 API 模型基类

    - Python 内部字段使用 snake_case
    - 对外 JSON 输出使用 camelCase
    - 输入同时兼容 snake_case 与 camelCase
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )
