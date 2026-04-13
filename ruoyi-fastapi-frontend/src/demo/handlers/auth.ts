import { http, type HttpHandler } from 'msw';

import { getDemoOfflineDb } from '@/demo/db';
import { AuthRepository } from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthService } from '@/demo/services';

import {
  createDemoApiPath,
  demoErrorResponse,
  demoJsonResponse,
  getDemoRequestToken,
  readDemoRequestBody,
} from './utils';

export interface CreateDemoAuthHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

function createAuthService(): DemoAuthService {
  return new DemoAuthService(new AuthRepository(getDemoOfflineDb()));
}

export function createDemoAuthHandlers({
  config,
  logger,
}: CreateDemoAuthHandlersOptions): HttpHandler[] {
  const path = (value: string) => createDemoApiPath(config, value);

  return [
    http.get(path('/captchaImage'), () => {
      logger.debug('demo-offline 处理验证码接口。', {
        handler: 'auth:captcha',
      });
      return demoJsonResponse(
        config,
        'auth:captcha',
        {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: createAuthService().getCaptcha(),
        },
        200
      );
    }),
    http.post(path('/login'), async ({ request }) => {
      try {
        const body = await readDemoRequestBody<{
          username?: string;
          password?: string;
        }>(request);
        logger.info('demo-offline 处理登录接口。', {
          handler: 'auth:login',
          username: body.username,
        });

        return demoJsonResponse(config, 'auth:login', await createAuthService().login(body));
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'auth:login');
      }
    }),
    http.get(path('/getInfo'), async ({ request }) => {
      try {
        return demoJsonResponse(
          config,
          'auth:getInfo',
          await createAuthService().getInfo(getDemoRequestToken(request))
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'auth:getInfo');
      }
    }),
    http.post(path('/auth/refresh'), async ({ request }) => {
      try {
        return demoJsonResponse(
          config,
          'auth:refresh',
          await createAuthService().refresh(getDemoRequestToken(request))
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'auth:refresh');
      }
    }),
    http.post(path('/auth/csrf-token'), async ({ request }) => {
      try {
        return demoJsonResponse(
          config,
          'auth:csrf-token',
          await createAuthService().getCsrfToken(getDemoRequestToken(request))
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'auth:csrf-token');
      }
    }),
    http.post(path('/auth/ws-ticket'), async ({ request }) => {
      try {
        const body = await readDemoRequestBody<{
          sessionId?: string;
          session_id?: string;
        }>(request);

        return demoJsonResponse(
          config,
          'auth:ws-ticket',
          await createAuthService().issueWsTicket(getDemoRequestToken(request), body)
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'auth:ws-ticket');
      }
    }),
    http.post(path('/auth/logout'), async ({ request }) =>
      demoJsonResponse(
        config,
        'auth:logout',
        await createAuthService().logout(getDemoRequestToken(request))
      )
    ),
    http.post(path('/logout'), async ({ request }) =>
      demoJsonResponse(
        config,
        'auth:logout-compat',
        await createAuthService().logout(getDemoRequestToken(request))
      )
    ),
  ];
}
