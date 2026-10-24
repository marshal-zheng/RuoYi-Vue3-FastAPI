"""Cross-context ports for this bounded context.

Rules:
- Declare protocol contracts only.
- Do not import other context infrastructure implementations.
"""

from __future__ import annotations

from fastapi import Depends

from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.application.services.login_service import LoginService


async def get_current_user(
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
) -> CurrentUserModel:
    """Identity auth port for current-user resolution."""
    return current_user


__all__ = ['get_current_user']
