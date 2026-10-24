"""Exact OpenAPI models for the remark-a-v1 subset of ZXUI Document v2."""

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictInt,
    ValidationError,
    computed_field,
    model_serializer,
    model_validator,
)
from pydantic_core import PydanticCustomError

from common.remark_document_v1 import RemarkError, remark_display_text, validate_remark
from module_admin.entity.vo.base import CamelModelBase


class _Exact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, serialize_by_alias=True)


class LinkAttrs(_Exact):
    href: str
    target: Literal['_blank']
    rel: Literal['noopener noreferrer nofollow']
    class_: None = Field(alias='class')
    title: None


class LinkMark(_Exact):
    type: Literal['link']
    attrs: LinkAttrs


class TextStyleAttrs(_Exact):
    fontFamily: None
    fontSize: None
    # Mirrors remark_document_v1.TEXT_COLORS, which admits the document first.
    color: Literal['red', 'orange', 'green', 'blue', 'purple', 'gray']


class TextStyleMark(_Exact):
    type: Literal['textStyle']
    attrs: TextStyleAttrs


class BoldMark(_Exact):
    type: Literal['bold']


class ItalicMark(_Exact):
    type: Literal['italic']


Mark = Annotated[LinkMark | TextStyleMark | BoldMark | ItalicMark, Field(discriminator='type')]


class TextNode(_Exact):
    type: Literal['text']
    text: str
    marks: list[Mark] | None = None

    @model_serializer(mode='wrap')
    def serialize_node(self, handler):
        result = handler(self)
        if self.marks is None:
            result.pop('marks', None)
        return result


class HardBreakNode(TextNode):
    type: Literal['hardBreak']
    text: None = Field(default=None, exclude=True)


class BlockAttrs(_Exact):
    blockId: str = Field(pattern=r'^[a-z][a-z0-9]*_[a-z0-9]+$', min_length=4, max_length=64)


class ParagraphAttrs(BlockAttrs):
    textAlign: None


class ParagraphNode(_Exact):
    type: Literal['paragraph']
    attrs: ParagraphAttrs
    content: list[Annotated[TextNode | HardBreakNode, Field(discriminator='type')]] | None = None

    @model_serializer(mode='wrap')
    def serialize_node(self, handler):
        result = handler(self)
        if self.content is None:
            result.pop('content', None)
        return result


class OrderedAttrs(BlockAttrs):
    start: StrictInt = Field(ge=1, le=1000000)
    type: None


class ListItemNode(_Exact):
    type: Literal['listItem']
    attrs: BlockAttrs
    content: list[Annotated['ParagraphNode | BulletListNode | OrderedListNode', Field(discriminator='type')]]


class BulletListNode(_Exact):
    type: Literal['bulletList']
    attrs: BlockAttrs
    content: list[ListItemNode] = Field(min_length=1)


class OrderedListNode(_Exact):
    type: Literal['orderedList']
    attrs: OrderedAttrs
    content: list[ListItemNode] = Field(min_length=1)


class DocumentRoot(_Exact):
    type: Literal['doc']
    content: list[Annotated[ParagraphNode | BulletListNode | OrderedListNode, Field(discriminator='type')]] = Field(
        min_length=1
    )


class DocumentBody(_Exact):
    format: Literal['json']
    content: DocumentRoot


class DocumentMeta(_Exact):
    schemaVersion: Literal['stable-block-identity/v2']


def _admit_remark(value):
    if isinstance(value, RemarkDocument):
        value = value.model_dump(mode='json')
    try:
        return validate_remark(value)
    except RemarkError as error:
        if error.code == 'version':
            category = 'version'
        elif error.code.startswith('link-'):
            category = 'link'
        elif error.code in {
            'characters',
            'bytes',
            'nodes',
            'list-depth',
            'tree-depth',
            'container-depth',
            'resource-limit',
        }:
            category = 'budget'
        else:
            category = 'structure'
        typed_error = PydanticCustomError(
            f'remark_{category}',
            '{path}: {reason}',
            {'path': error.path, 'reason': error.code},
        )
        # Rebase the codec's root on the actual Pydantic field. The existing
        # ProblemDetails handler can consume loc/type without parsing messages.
        location = tuple(int(part) if part.isdigit() else part for part in error.path.split('.')[1:])
        raise ValidationError.from_exception_data(
            'RemarkDocument', [{'type': typed_error, 'loc': location, 'input': None}]
        ) from None


class RemarkDocument(_Exact):
    @model_validator(mode='before')
    @classmethod
    def admit(cls, value):
        return _admit_remark(value)

    version: Literal[2]
    body: DocumentBody
    annotations: list[object] = Field(max_length=0)
    assets: list[object] = Field(max_length=0)
    meta: DocumentMeta


for model in (ListItemNode, BulletListNode, OrderedListNode, DocumentRoot, DocumentBody, RemarkDocument):
    model.model_rebuild()

# Field-level pre-validation bounds recursion and normalizes only the defined empty paragraph.
RemarkValue = Annotated[
    RemarkDocument | None,
    BeforeValidator(_admit_remark),
]


class RemarkReadProjection(BaseModel):
    @computed_field(alias='remarkText', return_type=str, json_schema_extra={'readOnly': True})
    @property
    def remark_text(self) -> str:
        return remark_display_text(self.remark)


class RemarkWriteGuard(CamelModelBase):
    @model_validator(mode='before')
    @classmethod
    def reject_derived_text(cls, value):
        if (
            isinstance(value, dict)
            and 'remark_text' not in cls.model_computed_fields
            and ('remarkText' in value or 'remark_text' in value)
        ):
            raise ValidationError.from_exception_data(
                cls.__name__,
                [
                    {
                        'type': PydanticCustomError(
                            'remark_readonly',
                            '{path}: read-only',
                            {'path': 'remarkText', 'reason': 'read-only'},
                        ),
                        'loc': ('remarkText',),
                        'input': None,
                    }
                ],
            )
        return value
