"""Static raster image validation and server-side re-encoding (orientation fixed, metadata removed)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PIL import Image, ImageOps, UnidentifiedImageError

from modules.file_assets.domain.errors import AssetInvalidError, AssetUnsupportedTypeError
from modules.file_assets.domain.models import ImageProfile
from modules.file_assets.domain.types import MAX_IMAGE_BYTES

if TYPE_CHECKING:
    from pathlib import Path

MAX_PIXELS = 25_000_000
MAX_SIDE = 8192
AVATAR_MAX_SIDE = 512
DEGRADED_MAX_SIDE = 4096
_FORMATS = {'JPEG': 'jpeg', 'PNG': 'png', 'WEBP': 'webp'}
_MEDIA_TYPES = {'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}


@dataclass(frozen=True)
class ImageInspection:
    type_id: str
    width: int
    height: int


@dataclass(frozen=True)
class NormalizedImage:
    path: Path
    type_id: str
    media_type: str
    source_size: tuple[int, int]
    output_size: tuple[int, int]
    degraded: bool
    downscaled: bool


def _open(path: Path) -> Image.Image:
    try:
        return Image.open(path)
    except UnidentifiedImageError:
        raise AssetUnsupportedTypeError('CONTENT_NOT_IMAGE', '文件内容不是受支持的图片') from None
    except Image.DecompressionBombError:
        raise AssetInvalidError('IMAGE_DIMENSIONS_EXCEEDED', '图片像素超出允许范围') from None
    except OSError:
        raise AssetInvalidError('IMAGE_CORRUPT', '图片已损坏或无法解码') from None


def inspect_image(path: Path) -> ImageInspection:
    """Validate the decoded format and bounds without trusting extension or declared MIME."""
    with _open(path) as image:
        type_id = _FORMATS.get(str(image.format or ''))
        if type_id is None:
            raise AssetUnsupportedTypeError('CONTENT_NOT_IMAGE', '仅支持 JPEG、PNG、WebP 静态图片')
        width, height = image.size
        # Header-only checks precede pixel decoding (pixel-bomb protection).
        if width <= 0 or height <= 0 or width > MAX_SIDE or height > MAX_SIDE or width * height > MAX_PIXELS:
            raise AssetInvalidError('IMAGE_DIMENSIONS_EXCEEDED', '图片尺寸或像素超出允许范围')
        if getattr(image, 'is_animated', False) or getattr(image, 'n_frames', 1) > 1:
            raise AssetUnsupportedTypeError('ANIMATED_IMAGE_UNSUPPORTED', '不支持动画图片')
        try:
            image.load()
        except Image.DecompressionBombError:
            raise AssetInvalidError('IMAGE_DIMENSIONS_EXCEEDED', '图片像素超出允许范围') from None
        except (OSError, SyntaxError, ValueError):
            raise AssetInvalidError('IMAGE_CORRUPT', '图片已损坏或无法解码') from None
        return ImageInspection(type_id=type_id, width=width, height=height)


def _prepare_mode(image: Image.Image, type_id: str) -> Image.Image:
    if type_id == 'jpeg' and image.mode not in {'L', 'RGB', 'CMYK'}:
        return image.convert('RGB')
    if type_id == 'png' and image.mode not in {'1', 'L', 'LA', 'I', 'I;16', 'P', 'RGB', 'RGBA'}:
        return image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
    if type_id == 'webp' and image.mode not in {'RGB', 'RGBA'}:
        has_alpha = 'A' in image.getbands() or 'transparency' in image.info
        return image.convert('RGBA' if has_alpha else 'RGB')
    return image


def _save(image: Image.Image, target: Path, type_id: str, *, icc: bytes | None, degraded: bool) -> int:
    params: dict[str, object] = {}
    if icc:
        params['icc_profile'] = icc
    if type_id == 'jpeg':
        params.update(quality=80 if degraded else 90, optimize=True)
        image.save(target, 'JPEG', **params)
    elif type_id == 'webp':
        params.update(quality=80 if degraded else 90, method=4)
        image.save(target, 'WEBP', **params)
    else:
        # Lossless: degrade by compression effort, never by quality.
        params.update(compress_level=9, optimize=True) if degraded else params.update(compress_level=6)
        transparency = image.info.get('transparency')
        if transparency is not None:
            params['transparency'] = transparency
        image.save(target, 'PNG', **params)
    return target.stat().st_size


def normalize_image(source: Path, target: Path, profile: ImageProfile) -> NormalizedImage:
    """Transpose by EXIF orientation, drop EXIF/XMP/comments (keep ICC) and re-encode within 5 MiB."""
    with _open(source) as opened:
        source_type = _FORMATS[str(opened.format)]
        icc = opened.info.get('icc_profile')
        transparency = opened.info.get('transparency')
        image = ImageOps.exif_transpose(opened)
    source_size = image.size
    # Discard every carried metadata item; only what we pass explicitly is written.
    image.info = {} if transparency is None else {'transparency': transparency}
    type_id = source_type
    if profile is ImageProfile.AVATAR:
        type_id = 'png'
        image.thumbnail((AVATAR_MAX_SIDE, AVATAR_MAX_SIDE), Image.Resampling.LANCZOS)
    image = _prepare_mode(image, type_id)

    size = _save(image, target, type_id, icc=icc, degraded=False)
    degraded = downscaled = False
    if size > MAX_IMAGE_BYTES:
        degraded = True
        size = _save(image, target, type_id, icc=icc, degraded=True)
    if size > MAX_IMAGE_BYTES and max(image.size) > DEGRADED_MAX_SIDE:
        downscaled = True
        image.thumbnail((DEGRADED_MAX_SIDE, DEGRADED_MAX_SIDE), Image.Resampling.LANCZOS)
        size = _save(image, target, type_id, icc=icc, degraded=True)
    if size > MAX_IMAGE_BYTES:
        raise AssetInvalidError('IMAGE_NORMALIZED_TOO_LARGE', '图片规范化后仍超过 5 MiB，请压缩后重试')
    return NormalizedImage(
        path=target,
        type_id=type_id,
        media_type=_MEDIA_TYPES[type_id],
        source_size=source_size,
        output_size=image.size,
        degraded=degraded,
        downscaled=downscaled,
    )
