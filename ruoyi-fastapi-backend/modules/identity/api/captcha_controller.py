import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, Request
from container.dependencies import service_provider
from config.enums import RedisInitKeyConfig
from module_admin.entity.vo.login_vo import CaptchaCode
from modules.identity.application.services.captcha_service import CaptchaService
from utils.response_util import ResponseUtil
from utils.log_util import logger


captchaController = APIRouter()


@captchaController.get('/captchaImage')
async def get_captcha_image(
    request: Request,
    captcha_service: CaptchaService = Depends(service_provider('captcha_service', require_session=False)),
):
    captcha_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled')
        == 'true'
        else False
    )
    register_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.registerUser') == 'true'
        else False
    )
    session_id = str(uuid.uuid4())
    captcha_result = await captcha_service.create_captcha_image_service()
    image = captcha_result[0]
    computed_result = captcha_result[1]
    await request.app.state.redis.set(
        f'{RedisInitKeyConfig.CAPTCHA_CODES.key}:{session_id}', computed_result, ex=timedelta(minutes=2)
    )
    logger.info(f'编号为{session_id}的会话获取图片验证码成功')

    return ResponseUtil.ok_resource(
        CaptchaCode(captchaEnabled=captcha_enabled, registerEnabled=register_enabled, img=image, uuid=session_id)
    )
