import { http, HttpResponse } from "msw";

import { createApiPath } from "../constants";
import { mockDataset, type MockDevice } from "../data";
import type { MockOpenApiPage } from "../contracts";
import type { MockRuntimeHandler, MockStrategy } from "../types";
import { getSearchParams } from "../utils/request";
import { pagination, resultSuccess } from "../utils/response";
import { withBackendFallback } from "../utils/with-backend-fallback";

function toPositiveNumber(value: string | null, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function listDevices(request: Request): MockOpenApiPage<MockDevice> {
  const searchParams = getSearchParams(request);
  const page = toPositiveNumber(searchParams.get("page"), 1);
  const pageSize = toPositiveNumber(
    searchParams.get("pageSize") ?? searchParams.get("page_size"),
    10,
  );
  const keyword = (
    searchParams.get("deviceName") ??
    searchParams.get("device_name") ??
    ""
  ).trim();
  const type = (
    searchParams.get("deviceType") ??
    searchParams.get("device_type") ??
    ""
  ).trim();

  const filtered = mockDataset.device.devices.filter((device) => {
    if (keyword && !device.deviceName.includes(keyword)) return false;
    if (type && device.deviceType !== type) return false;
    return true;
  });

  return {
    items: pagination(page, pageSize, filtered),
    total: filtered.length,
    page,
    pageSize,
  };
}

export function createDeviceHandlers(
  strategy: MockStrategy,
): MockRuntimeHandler[] {
  return [
    http.get(createApiPath("/device/list"), ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess(listDevices(request))),
        { strategy, tag: "device:list" },
      ),
    ),
  ];
}
