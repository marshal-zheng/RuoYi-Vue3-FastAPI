from fastapi import Request
from config.enums import RedisInitKeyConfig
from config.env import SecurityConfig
from exceptions.exception import ValidationException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.online_vo import DeleteOnlineModel, OnlineQueryModel
from modules.identity.application.services.security_token_service import SecurityTokenService
from utils.common_util import CamelCaseUtil


class OnlineService:
    """
    在线用户管理模块服务层
    """

    async def get_online_list_services(self, request: Request, query_object: OnlineQueryModel):
        """
        获取在线用户表信息service

        :param request: Request对象
        :param query_object: 查询参数对象
        :return: 在线用户列表信息
        """
        access_token_keys = await request.app.state.redis.keys(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}*')
        if not access_token_keys:
            access_token_keys = []
        access_token_values_list = [await request.app.state.redis.get(key) for key in access_token_keys]
        security_service = getattr(request.app.state, 'security_token_service', None)
        online_info_list = []
        for item in access_token_values_list:
            token = item.decode('utf-8') if isinstance(item, bytes) else str(item)
            if not token or not isinstance(security_service, SecurityTokenService):
                continue
            try:
                payload = await security_service.verify_access_token(
                    token,
                    audience=SecurityConfig.security_jwt_audience_api,
                    enforce_replay=False,
                    enforce_session=False,
                )
            except Exception:
                continue
            login_info = payload.get('login_info') or {}
            online_dict = dict(
                token_id=payload.get('session_id') or '',
                user_name=payload.get('user_name'),
                dept_name=payload.get('dept_name'),
                ipaddr=login_info.get('ipaddr'),
                login_location=login_info.get('loginLocation'),
                browser=login_info.get('browser'),
                os=login_info.get('os'),
                login_time=login_info.get('loginTime'),
            )
            if query_object.user_name and not query_object.ipaddr:
                if query_object.user_name == payload.get('user_name'):
                    online_info_list = [online_dict]
                    break
            elif not query_object.user_name and query_object.ipaddr:
                if query_object.ipaddr == payload.get('login_info').get('ipaddr'):
                    online_info_list = [online_dict]
                    break
            elif query_object.user_name and query_object.ipaddr:
                if query_object.user_name == payload.get('user_name') and query_object.ipaddr == payload.get(
                    'login_info'
                ).get('ipaddr'):
                    online_info_list = [online_dict]
                    break
            else:
                online_info_list.append(online_dict)

        return CamelCaseUtil.transform_result(online_info_list)

    async def delete_online_services(self, request: Request, page_object: DeleteOnlineModel):
        """
        强退在线用户信息service

        :param request: Request对象
        :param page_object: 强退在线用户对象
        :return: 强退在线用户校验结果
        """
        if page_object.token_ids:
            token_id_list = page_object.token_ids.split(',')
            security_service = getattr(request.app.state, 'security_token_service', None)
            for token_id in token_id_list:
                await request.app.state.redis.delete(f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{token_id}')
                if isinstance(security_service, SecurityTokenService):
                    await security_service.revoke_user_session(token_id)
            return CrudResponseModel(is_success=True, message='强退成功')
        else:
            raise ValidationException(
                user_message='传入session_id为空',
                developer_message='Token IDs parameter is empty',
                field='token_ids'
            )
