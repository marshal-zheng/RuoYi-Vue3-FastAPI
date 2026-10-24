"""Finite request contract for AI authoring of the seven management remark fields."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from module_admin.entity.vo.remark_vo import RemarkValue

RemarkAIScene = Literal['user', 'role', 'post', 'dictType', 'dictData', 'config', 'genTable']
ContextText = Annotated[str, StringConstraints(strict=True, max_length=300)]
ContextValue = ContextText | Annotated[list[ContextText], Field(max_length=50)]

CONTEXT_FIELDS = {
    'user': frozenset({'userName', 'nickName', 'deptName', 'postNames', 'roleNames', 'status'}),
    'role': frozenset({'roleName', 'roleKey', 'menuNames', 'status'}),
    'post': frozenset({'postName', 'postCode', 'status'}),
    'dictType': frozenset({'dictName', 'dictType', 'status'}),
    'dictData': frozenset({'dictName', 'dictType', 'dictLabel', 'dictValue', 'status'}),
    'config': frozenset({'configName', 'configKey', 'configType'}),
    'genTable': frozenset({'tableName', 'tableComment', 'className', 'functionAuthor'}),
}


class RemarkAIRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    scene: RemarkAIScene
    instruction: str = Field(min_length=1, max_length=2000)
    target: Literal['document', 'selection']
    document: RemarkValue
    selection: RemarkValue = None
    candidate: RemarkValue = None
    context: dict[str, ContextValue] = Field(default_factory=dict, max_length=8)

    @field_validator('instruction')
    @classmethod
    def require_instruction(cls, value):
        if not value.strip():
            raise ValueError('请填写备注写作要求')
        return value.strip()

    @model_validator(mode='after')
    def check_scope(self):
        if self.target == 'selection' and self.selection is None:
            raise ValueError('局部修改需要非空选区')
        if self.target == 'document' and self.selection is not None:
            raise ValueError('全文修改不接收选区')
        if not self.context.keys() <= CONTEXT_FIELDS[self.scene]:
            # Never interpolate unknown keys or values: they may contain private form data.
            raise ValueError('备注上下文包含该场景不允许的字段')
        length = sum(
            len(part) for value in self.context.values() for part in ([value] if isinstance(value, str) else value)
        )
        if length > 6000:
            raise ValueError('备注上下文不能超过 6000 字')
        return self


class RemarkAIStatus(BaseModel):
    available: bool
