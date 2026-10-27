# ruff: noqa: PLC0415 -- The optional provider SDK is imported only after admission.
"""Field generation admission and lifecycle; providers own only their wire protocol."""

import asyncio
import hashlib
import importlib.util
import json
from contextlib import aclosing

from common.remark_document_v1 import LIMITS
from config.env import TextFieldAISettings
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.text_field_ai_vo import Notice, ResultMeta, TextFieldAIPolicy, TextFieldAIStatus
from modules.system.application.prompts.text_field_v1 import PROMPT_VERSION, SYSTEM_PROMPT
from modules.system.application.services.ai_context_manifest import load_manifest
from modules.system.application.services.ai_context_tokens import PREFIXES, TOKEN, document_tokens, text_tokens
from modules.system.application.services.ai_providers.base import AIError
from modules.system.application.services.text_field_ai_document import normalize_output, preview_text


class TextFieldAIService:
    def __init__(self, settings: TextFieldAISettings, *, provider_factory=None):
        self.settings = settings
        self.manifest, self.manifest_revision = load_manifest(settings.ai_context_manifest_path)
        self.provider_factory = provider_factory

    def status(self):
        settings = self.settings
        available = bool(
            settings.is_configured
            and self.manifest
            and all(importlib.util.find_spec(name) for name in ('openai', 'httpx2', 'sse_starlette'))
        )
        policy = TextFieldAIPolicy(personal=settings.ai_context_personal_policy)
        revision = hashlib.sha256(
            json.dumps(
                {
                    'policy': policy.model_dump(),
                    'providerClass': settings.ai_provider_class,
                    'provider': settings.ai_provider,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        return TextFieldAIStatus(
            available=available,
            manifestRevision=self.manifest_revision,
            policyRevision=revision if available else None,
            policy=policy if available else None,
            providerClass=settings.ai_provider_class if available else None,
        )

    def canonical_scope(self, payload):
        if not self.manifest or payload.manifestRevision != self.manifest_revision:
            raise AIError('context-rejected')
        scope = self.manifest.scopes.get(payload.scope)
        if scope is None or payload.purpose not in scope.purposes:
            raise AIError('context-rejected')
        return scope

    def validate(self, payload, current_user):  # noqa: PLR0912 -- Ordered finite admission gates.
        scope = self.canonical_scope(payload)
        CheckUserInterfaceAuth(scope.permissions.values)(current_user)
        purpose = scope.purposes[payload.purpose]
        selected = set(payload.selectedContextIds)
        if not selected <= set(purpose.selectableContextIds):
            raise AIError('context-rejected')
        allowed = set() if payload.action == 'rewrite' else set(purpose.defaultContextIds) | selected
        ids = [item.id for item in payload.context]
        order = [item.id for item in scope.items if item.id in ids]
        if ids != order or len(ids) != len(set(ids)) or not set(ids) <= allowed:
            raise AIError('context-rejected')
        metadata = {item.id: item.model_dump() for item in scope.items}
        chars = 0
        tokens = text_tokens(payload.instruction)
        for item in payload.context:
            actual = item.model_dump(exclude={'value'})
            if actual != metadata[item.id]:
                raise AIError('context-rejected')
            values = item.value if isinstance(item.value, list) else [item.value]
            for value in values:
                if not value.strip() or value != value.strip():
                    raise AIError('context-rejected')
                chars += len(value)
                tokens.update(text_tokens(value))
                if item.sensitivity == 'personal':
                    if self.settings.ai_context_personal_policy == 'never':
                        raise AIError('policy-rejected')
                    if self.settings.ai_context_personal_policy == 'mask':
                        match = TOKEN.fullmatch(value)
                        if not match or match[1] != PREFIXES[item.kind]:
                            raise AIError('policy-rejected')
        if chars > 6000:
            raise AIError('context-rejected')
        for value in (payload.document, payload.selection, payload.candidate):
            tokens.update(document_tokens(value.model_dump() if value else None))
        if tokens and self.settings.ai_context_personal_policy != 'mask':
            raise AIError('policy-rejected')
        status = self.status()
        if status.policyRevision is not None and payload.policyRevision != status.policyRevision:
            raise AIError('policy-rejected')
        if not status.available:
            raise AIError('provider-unavailable')
        return tokens

    def _provider(self):
        if self.provider_factory:
            return self.provider_factory(self.settings)
        from modules.system.application.services.ai_providers.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(self.settings)

    async def produce(self, payload, allowed_tokens, emit):
        content, preview, size, stopped = '', '', 0, False
        data = payload.model_dump(mode='json')
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': json.dumps(data, ensure_ascii=False, separators=(',', ':'))},
        ]
        async with asyncio.timeout(self.settings.ai_text_field_timeout_seconds):
            async with aclosing(self._provider().stream(messages)) as chunks:
                async for chunk in chunks:
                    if chunk.finish == 'length':
                        raise AIError('output-limit')
                    if stopped and (chunk.text or chunk.finish):
                        raise AIError('invalid-output')
                    if chunk.finish is not None:
                        if chunk.finish != 'stop':
                            raise AIError('incomplete-output')
                        stopped = True
                    size += len(chunk.text.encode('utf-8'))
                    if size > LIMITS['bytes']:
                        raise AIError('output-limit')
                    content += chunk.text
                    current = preview_text(content)
                    if len(current) > LIMITS['characters']:
                        raise AIError('output-limit')
                    if current.startswith(preview) and len(current) > len(preview):
                        await emit({'type': 'delta', 'text': current[len(preview) :]})
                        preview = current
            if not stopped:
                raise AIError('incomplete-output')
            result = self.result(content, payload, allowed_tokens)
        # Only emit a final candidate after normal iteration AND complete upstream close.
        await emit(result)

    def result(self, content, payload, allowed_tokens):
        try:
            envelope = json.loads(content)
            if not isinstance(envelope, dict) or set(envelope) != {'document', 'notices'}:
                raise ValueError('invalid envelope')
            if not isinstance(envelope['notices'], list):
                raise ValueError('invalid notices')
            notices = [Notice.model_validate(item) for item in envelope['notices']]
            if len(notices) > 16:
                raise ValueError('notice limit')
            scope = self.canonical_scope(payload)
            scope_ids = {item.id for item in scope.items}
            if any(not set(notice.contextIds) <= scope_ids for notice in notices):
                raise ValueError('invalid notice ids')
            raw = envelope['document']
            if not document_tokens(raw) <= allowed_tokens:
                raise ValueError('unknown token')
            document = normalize_output(json.dumps(raw, ensure_ascii=False)) if raw is not None else None
            if document is None and not notices:
                raise ValueError('empty envelope')
            return {
                'type': 'result',
                'document': document,
                'notices': [item.model_dump() for item in notices],
                'meta': ResultMeta(
                    model=self.settings.ai_model,
                    contextIds=[item.id for item in payload.context],
                    promptVersion=PROMPT_VERSION,
                ).model_dump(),
            }
        except AIError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            raise AIError('invalid-output') from None
