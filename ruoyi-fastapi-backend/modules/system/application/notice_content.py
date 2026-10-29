"""Notice HTML: one sanitization policy and the asset references extracted from its final form.

The HTML is the content source of truth; the binding table is a server-maintained reference index.
Unsupported images (external URLs, data: URLs, other formats) and embeds are rejected instead of being
silently dropped, so a successful save never loses what the editor showed.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import nh3

from exceptions.exception import ValidationException
from modules.file_assets.ports import normalize_asset_id

NOTICE_CONTENT_MAX_BYTES = 1024 * 1024
NOTICE_CONTENT_FIELD = 'notice_content'
_CONTENT_SRC = re.compile(r'/file-assets/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/content')
_EMBED_TAGS = frozenset({'iframe', 'video', 'audio', 'object', 'embed', 'frame', 'frameset', 'source', 'svg', 'math'})
_HEADINGS = frozenset({'h1', 'h2', 'h3', 'h4', 'h5', 'h6'})
_ALIGN = {'ql-align-center', 'ql-align-right', 'ql-align-justify'}
_INDENT = {f'ql-indent-{level}' for level in range(1, 9)}
_BLOCK_CLASSES = _ALIGN | _INDENT | {'ql-direction-rtl'}
_STYLE_PROPERTIES = frozenset({'color', 'background-color'})
# Quill writes named colors, hex or rgb()/rgba() values; nothing that can reference a resource.
_STYLE_VALUE = re.compile(r'#[0-9a-fA-F]{3,8}|rgba?\(\s*[0-9.%\s,]+\)|[a-zA-Z]{3,24}')

ALLOWED_TAGS = frozenset(
    {'p', 'br', 'span', 'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'sub', 'sup', 'blockquote', 'pre', 'code'}
    | {'ol', 'ul', 'li', 'a', 'img'}
    | _HEADINGS
)
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'target'},
    'img': {'src', 'alt'},
    'span': {'style'},
    'p': {'style'},
    'li': {'data-list'},
    'pre': {'spellcheck'},
    **{heading: {'style'} for heading in _HEADINGS},
}
ALLOWED_CLASSES = {
    'p': _BLOCK_CLASSES,
    'li': _BLOCK_CLASSES,
    'blockquote': _BLOCK_CLASSES,
    'pre': {'ql-syntax'},
    'span': {'ql-size-small', 'ql-size-large', 'ql-size-huge', 'ql-font-serif', 'ql-font-monospace'},
    'ol': _INDENT,
    'ul': _INDENT,
    **dict.fromkeys(_HEADINGS, _BLOCK_CLASSES),
}


def _invalid(message: str) -> ValidationException:
    return ValidationException(user_message=message, field=NOTICE_CONTENT_FIELD)


class _ReferenceScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images: list[str | None] = []
        self.embeds: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs).get('src'))
        elif tag in _EMBED_TAGS:
            self.embeds.append(tag)

    handle_startendtag = handle_starttag


def _scan(html: str) -> _ReferenceScanner:
    scanner = _ReferenceScanner()
    scanner.feed(html)
    scanner.close()
    return scanner


def _asset_id_of(src: str | None) -> str | None:
    match = _CONTENT_SRC.fullmatch((src or '').strip())
    return normalize_asset_id(match.group(1)) if match else None


def _safe_style(value: str) -> str | None:
    kept = []
    for declaration in value.split(';'):
        name, _, raw = declaration.partition(':')
        name, raw = name.strip().lower(), raw.strip()
        if name in _STYLE_PROPERTIES and _STYLE_VALUE.fullmatch(raw):
            kept.append(f'{name}: {raw}')
    return '; '.join(kept) or None


def _attribute_filter(tag: str, attribute: str, value: str) -> str | None:
    if attribute == 'style':
        return _safe_style(value)
    if tag == 'img' and attribute == 'src':
        return value if _asset_id_of(value) else None
    if tag == 'a' and attribute == 'target':
        return '_blank' if value == '_blank' else None
    return value


def sanitize_notice_html(raw: str | None) -> tuple[str | None, list[str]]:
    """Return (sanitized HTML, asset ids in first-occurrence order); reject what cannot be kept."""
    if raw is None:
        return None, []
    if len(raw.encode('utf-8')) > NOTICE_CONTENT_MAX_BYTES:
        raise _invalid('公告内容超过 1 MiB 上限')
    before = _scan(raw)
    if before.embeds:
        raise _invalid('公告内容不支持视频或其他嵌入内容')
    if any(_asset_id_of(src) is None for src in before.images):
        raise _invalid('公告内容包含外部图片或未上传完成的图片，请通过编辑器上传后再保存')
    cleaned = nh3.clean(
        raw,
        tags=set(ALLOWED_TAGS),
        clean_content_tags={'script', 'style', 'template', 'noscript'},
        attributes={tag: set(values) for tag, values in ALLOWED_ATTRIBUTES.items()},
        attribute_filter=_attribute_filter,
        allowed_classes={tag: set(values) for tag, values in ALLOWED_CLASSES.items()},
        filter_style_properties=set(_STYLE_PROPERTIES),
        url_schemes={'http', 'https', 'mailto'},
        link_rel='noopener noreferrer',
        strip_comments=True,
    )
    after = _scan(cleaned)
    asset_ids: list[str] = []
    for src in after.images:
        asset_id = _asset_id_of(src)
        if asset_id is None:  # pragma: no cover - the pre-scan already rejected these
            raise _invalid('公告内容包含无法保存的图片')
        if asset_id not in asset_ids:
            asset_ids.append(asset_id)
    if len(cleaned.encode('utf-8')) > NOTICE_CONTENT_MAX_BYTES:
        raise _invalid('公告内容超过 1 MiB 上限')
    return cleaned, asset_ids
