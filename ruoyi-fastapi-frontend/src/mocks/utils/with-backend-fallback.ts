// @ts-nocheck
import { bypass } from 'msw'

import type { MockStrategy } from '../types'

export interface FallbackOptions {
  strategy: MockStrategy
  tag?: string
}

export async function withBackendFallback(
  request: Request,
  createMockResponse: () => Response | Promise<Response>,
  { strategy, tag }: FallbackOptions
): Promise<Response> {
  if (strategy === 'pure') {
    const mockResponse = await createMockResponse()
    return markMockResponse(mockResponse, strategy, tag)
  }

  // 先尝试直连后端；非 404 直接返回；404 或网络错误则降级为 Mock
  return fetch(bypass(request))
    .then((upstreamResponse) => {
      if (upstreamResponse.status !== 404) {
        return upstreamResponse
      }
      return Promise.resolve(createMockResponse()).then((res: Response) =>
        markMockResponse(res, strategy, tag)
      )
    })
    .catch(() =>
      Promise.resolve(createMockResponse()).then((res: Response) =>
        markMockResponse(res, strategy, tag)
      )
    )

  // 不会到达此处：返回路径已在 then/catch 中覆盖
}

export function markMockResponse(
  response: Response,
  strategy: MockStrategy,
  tag?: string
) {
  const headers = response.headers
  headers.set('X-Mock-Response', 'true')
  headers.set('X-Mock-Mode', strategy)
  if (tag) {
    headers.set('X-Mock-Handler', tag)
  }
  return response
}
