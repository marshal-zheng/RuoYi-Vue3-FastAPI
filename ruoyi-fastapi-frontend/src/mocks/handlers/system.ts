// @ts-nocheck
import { http, HttpResponse } from 'msw'

import type { MockStrategy } from '../types'
import { createDeptTree, createDictData, createSystemRoutes } from '../factories'
import { resultSuccess } from '../utils/response'
import { withBackendFallback } from '../utils/with-backend-fallback'

const systemRoutes = createSystemRoutes()

export function createSystemHandlers(strategy: MockStrategy) {
  return [
    http.get('/dev-api/getRouters', ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess(systemRoutes)),
        { strategy, tag: 'system:getRouters' }
      )
    ),
    http.get(
      '/dev-api/system/dict/data/type/:dictType',
      ({ request, params }) => {
        const dictType = String(params.dictType ?? '')
        return withBackendFallback(
          request,
          () =>
            HttpResponse.json(
              resultSuccess({
                data: createDictData(dictType)
              })
            ),
          { strategy, tag: `system:dict:${dictType}` }
        )
      }
    ),
    http.get('/dev-api/system/dept/treeselect', ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess(createDeptTree())),
        { strategy, tag: 'system:deptTree' }
      )
    )
  ]
}
