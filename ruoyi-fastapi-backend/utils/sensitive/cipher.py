import base64
import hashlib
import hmac
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config.env import SensitiveConfig, JwtConfig
from utils.log_util import logger


class SensitiveDataCipher:
    """
    Reversible encryption for sensitive fields.

    Uses AES-GCM with a key from SENSITIVE_DATA_KEY (fallback to JWT_SECRET_KEY).
    A deterministic nonce (HMAC-derived) enables equality lookups.
    """

    _aesgcm = None
    _nonce_key = None
    _hash_key = None
    _prefix = None
    _aad = b'sensitive-data'
    _warned_fallback = False

    @classmethod
    def _get_prefix(cls) -> str:
        if cls._prefix is None:
            prefix = getattr(SensitiveConfig, 'sensitive_data_prefix', '')
            cls._prefix = prefix or 'enc:v1:'
        return cls._prefix

    @classmethod
    def _ensure_ready(cls) -> None:
        if cls._aesgcm is not None:
            return
        master_key = (SensitiveConfig.sensitive_data_key or '').strip()
        used_fallback = False
        if not master_key:
            master_key = (JwtConfig.jwt_secret_key or '').strip()
            used_fallback = True
        if not master_key:
            raise ValueError('SENSITIVE_DATA_KEY is not configured')
        if used_fallback and not cls._warned_fallback:
            logger.warning('SENSITIVE_DATA_KEY is empty; fallback to JWT_SECRET_KEY for encryption')
            cls._warned_fallback = True
        enc_key = hashlib.sha256(f'enc:{master_key}'.encode('utf-8')).digest()
        nonce_key = hashlib.sha256(f'nonce:{master_key}'.encode('utf-8')).digest()
        hash_key = hashlib.sha256(f'hash:{master_key}'.encode('utf-8')).digest()
        cls._aesgcm = AESGCM(enc_key)
        cls._nonce_key = nonce_key
        cls._hash_key = hash_key

    @classmethod
    def is_encrypted(cls, value: str) -> bool:
        return isinstance(value, str) and value.startswith(cls._get_prefix())

    @classmethod
    def _derive_nonce(cls, plaintext: bytes) -> bytes:
        cls._ensure_ready()
        return hmac.new(cls._nonce_key, plaintext, hashlib.sha256).digest()[:12]

    @classmethod
    def encrypt(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == '':
            return value
        if not isinstance(value, str):
            return value
        if not SensitiveConfig.sensitive_data_enabled:
            return value
        if cls.is_encrypted(value):
            return value

        try:
            plaintext = value.encode('utf-8')
            if getattr(SensitiveConfig, 'sensitive_data_deterministic', True):
                nonce = cls._derive_nonce(plaintext)
            else:
                nonce = os.urandom(12)
            ciphertext = cls._aesgcm.encrypt(nonce, plaintext, cls._aad)
            payload = base64.urlsafe_b64encode(nonce + ciphertext).decode('ascii')
            return f"{cls._get_prefix()}{payload}"
        except Exception as exc:
            logger.error(f'Sensitive data encrypt failed: {exc}')
            raise

    @classmethod
    def decrypt(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == '':
            return value
        if not isinstance(value, str):
            return value
        if not cls.is_encrypted(value):
            return value
        try:
            cls._ensure_ready()
            payload = value[len(cls._get_prefix()):]
            raw = base64.urlsafe_b64decode(payload.encode('ascii'))
            if len(raw) <= 12:
                raise ValueError('Invalid encrypted payload')
            nonce = raw[:12]
            ciphertext = raw[12:]
            plaintext = cls._aesgcm.decrypt(nonce, ciphertext, cls._aad)
            return plaintext.decode('utf-8')
        except Exception as exc:
            logger.error(f'Sensitive data decrypt failed: {exc}')
            raise

    @classmethod
    def hash(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == '':
            return value
        if not isinstance(value, str):
            return value
        cls._ensure_ready()
        return hmac.new(cls._hash_key, value.encode('utf-8'), hashlib.sha256).hexdigest()
