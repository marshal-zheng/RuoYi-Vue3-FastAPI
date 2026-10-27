"""Closed public field-AI contracts. Error messages never contain input values."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from common.ai_context import AIErrorCode, document_tokens
from module_admin.entity.vo.remark_vo import RemarkValue

Identifier = Annotated[str, Field(pattern=r'^[a-zA-Z][a-zA-Z0-9]{0,63}$')]
UUIDText = Annotated[
    str, Field(pattern=r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
]
Revision = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
PersonalKind = Literal['phone', 'email', 'id', 'address', 'other']

ValueText = Annotated[str, Field(min_length=1, max_length=300)]


class Exact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class PublicItem(Exact):
    id: Identifier
    label: str = Field(min_length=1, max_length=80)
    sensitivity: Literal['public']
    value: ValueText | Annotated[list[ValueText], Field(min_length=1, max_length=50)]


class PersonalItem(PublicItem):
    sensitivity: Literal['personal']
    kind: PersonalKind


WireItem = Annotated[PublicItem | PersonalItem, Field(discriminator='sensitivity')]


class TextFieldAIRequest(Exact):
    version: Literal['ai-context/v1']
    requestId: UUIDText
    captureId: UUIDText
    manifestRevision: Revision
    policyRevision: Revision
    scope: str = Field(pattern=r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$', max_length=96)
    purpose: Identifier
    action: Literal['draft', 'rewrite', 'include-context']
    selectedContextIds: list[Identifier] = Field(max_length=16)
    profile: Literal['basic-rich-text']
    instruction: str = Field(min_length=1, max_length=2000, pattern=r'\S')
    target: Literal['document', 'selection']
    document: RemarkValue
    selection: RemarkValue
    candidate: RemarkValue
    context: list[WireItem] = Field(max_length=16)

    @model_validator(mode='before')
    @classmethod
    def original_document_tokens(cls, value):
        # Check original node boundaries before the codec can merge adjacent text nodes.
        if isinstance(value, dict):
            for key in ('document', 'selection', 'candidate'):
                document_tokens(value.get(key))
        return value

    @model_validator(mode='after')
    def target_and_selection(self):
        if (self.target == 'selection') != (self.selection is not None):
            raise ValueError('invalid target selection')
        if len(set(self.selectedContextIds)) != len(self.selectedContextIds):
            raise ValueError('duplicate selection')
        if (self.action == 'include-context') != bool(self.selectedContextIds):
            raise ValueError('invalid action selection')
        return self


class TextFieldAIPolicy(Exact):
    personal: Literal['mask', 'never', 'plain']
    maxItems: Literal[16] = 16
    maxChars: Literal[6000] = 6000


class TextFieldAIStatus(Exact):
    available: bool
    contract: Literal['ai-context/v1'] = 'ai-context/v1'
    manifestRevision: Revision | None = None
    policyRevision: Revision | None = None
    policy: TextFieldAIPolicy | None = None
    providerClass: Literal['first-party', 'contract-bound', 'third-party'] | None = None


class Notice(Exact):
    code: Literal['information-unavailable']
    contextIds: list[Identifier] = Field(max_length=16)

    @model_validator(mode='after')
    def unique_ids(self):
        if len(set(self.contextIds)) != len(self.contextIds):
            raise ValueError('duplicate notice ids')
        return self


class ResultMeta(Exact):
    promptVersion: Literal['text-field/v1'] = 'text-field/v1'
    model: str = Field(min_length=1, max_length=128)
    contextIds: list[Identifier] = Field(max_length=16)


class EventBase(Exact):
    requestId: UUIDText
    captureId: UUIDText


class DeltaEvent(EventBase):
    type: Literal['delta'] = 'delta'
    text: str = Field(min_length=1, max_length=5000)


class ResultEvent(EventBase):
    type: Literal['result'] = 'result'
    document: RemarkValue
    notices: list[Notice] = Field(max_length=16)
    meta: ResultMeta

    @model_validator(mode='after')
    def nonempty(self):
        if self.document is None and not self.notices:
            raise ValueError('empty result')
        return self


class ErrorEvent(EventBase):
    type: Literal['error'] = 'error'
    code: AIErrorCode
    message: str = Field(min_length=1, max_length=200)


TextFieldAIEvent = Annotated[DeltaEvent | ResultEvent | ErrorEvent, Field(discriminator='type')]


class TextFieldAIProblem(Exact):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    errorCode: int
    requestId: str | None = None
    traceId: str | None = None
    aiCode: AIErrorCode | None = None
