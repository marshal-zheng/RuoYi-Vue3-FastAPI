import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, type Page, type Response } from "@playwright/test";

interface ContractRegistryEntry {
  method: string;
  openapiPath: string;
  handlerTag?: string;
  status: string;
  critical: boolean;
}

export interface MockApiRecord {
  method: string;
  url: string;
  path: string;
  pathname: string;
  status?: number;
  handler?: string;
  overlay?: string;
  mockResponse?: string;
  failed?: string;
  step: string;
}

let contractRegistryEntries: ContractRegistryEntry[] | undefined;

function isApiUrl(url: string) {
  try {
    return new URL(url).pathname.startsWith("/api/");
  } catch {
    return false;
  }
}

function toRecordUrl(url: string) {
  const parsed = new URL(url);
  return `${parsed.origin}${parsed.pathname}${parsed.search}`;
}

function getRegistryRoot() {
  const candidates = [
    resolve(process.cwd(), "src/mocks/contracts/coverage/registry"),
    resolve(
      process.cwd(),
      "ruoyi-fastapi-frontend/src/mocks/contracts/coverage/registry",
    ),
  ];
  const registryRoot = candidates.find((candidate) => existsSync(candidate));
  if (!registryRoot) {
    throw new Error(
      `Unable to locate mock contract coverage registry. Tried:\n${candidates.join("\n")}`,
    );
  }
  return registryRoot;
}

function loadContractRegistry() {
  if (contractRegistryEntries) {
    return contractRegistryEntries;
  }

  const registryRoot = getRegistryRoot();
  contractRegistryEntries = readdirSync(registryRoot)
    .filter((file) => file.endsWith(".json"))
    .flatMap((file) => {
      const content = readFileSync(resolve(registryRoot, file), "utf8");
      return JSON.parse(content) as ContractRegistryEntry[];
    });

  return contractRegistryEntries;
}

function isExpectedUnhandledApi(record: MockApiRecord) {
  return (
    record.method === "GET" &&
    record.path === "/api/__demo_e2e_missing_probe" &&
    record.status === 501 &&
    record.handler === "unhandled-api"
  );
}

function registryMatchesFor(record: MockApiRecord) {
  if (!record.handler) {
    return [];
  }
  return loadContractRegistry().filter(
    (entry) => entry.handlerTag === record.handler,
  );
}

function summarize(records: MockApiRecord[]) {
  return records
    .map((record) => {
      const status = record.status ?? "FAILED";
      const handler = record.handler || "missing-handler";
      const overlay = record.overlay ? ` overlay=${record.overlay}` : "";
      const failed = record.failed ? ` failed=${record.failed}` : "";
      return `${record.step}: ${record.method} ${record.pathname} -> ${status} ${handler}${overlay}${failed}`;
    })
    .join("\n");
}

export function attachMockNetworkRecorder(page: Page) {
  const records: MockApiRecord[] = [];
  let currentStep = "setup";

  page.on("response", (response) => {
    const request = response.request();
    if (!isApiUrl(response.url())) {
      return;
    }

    const url = new URL(response.url());
    const headers = response.headers();
    records.push({
      method: request.method(),
      url: toRecordUrl(response.url()),
      path: url.pathname,
      pathname: `${url.pathname}${url.search}`,
      status: response.status(),
      handler: headers["x-mock-handler"],
      overlay: headers["x-mock-overlay"],
      mockResponse: headers["x-mock-response"],
      step: currentStep,
    });
  });

  page.on("requestfailed", (request) => {
    if (!isApiUrl(request.url())) {
      return;
    }
    const url = new URL(request.url());
    records.push({
      method: request.method(),
      url: toRecordUrl(request.url()),
      path: url.pathname,
      pathname: `${url.pathname}${url.search}`,
      failed: request.failure()?.errorText || "request failed",
      step: currentStep,
    });
  });

  return {
    records,
    setStep(step: string) {
      currentStep = step;
    },
    waitForMockResponse(
      tag: string | RegExp,
      options: { timeout?: number } = {},
    ) {
      return page.waitForResponse((response) => {
        if (!isApiUrl(response.url())) {
          return false;
        }
        const handler = response.headers()["x-mock-handler"] || "";
        return typeof tag === "string" ? handler === tag : tag.test(handler);
      }, options);
    },
    waitForOverlayResponse(
      overlayId: string | RegExp,
      options: { timeout?: number } = {},
    ) {
      return page.waitForResponse((response) => {
        if (!isApiUrl(response.url())) {
          return false;
        }
        const overlay = response.headers()["x-mock-overlay"] || "";
        return typeof overlayId === "string"
          ? overlay === overlayId
          : overlayId.test(overlay);
      }, options);
    },
    async expectHandlersSeen(tags: Array<string | RegExp>) {
      for (const tag of tags) {
        const found = records.some((record) => {
          const handler = record.handler || "";
          return typeof tag === "string" ? handler === tag : tag.test(handler);
        });
        expect(
          found,
          `Expected mock handler ${String(tag)}.\n${summarize(records)}`,
        ).toBe(true);
      }
    },
    assertNoRealBackendRequests() {
      const pageOrigin = new URL(page.url()).origin;
      const realBackendRequests = records.filter((record) => {
        const origin = new URL(record.url).origin;
        return origin !== pageOrigin;
      });
      expect(
        realBackendRequests,
        `demo-offline made API requests outside preview origin:\n${summarize(realBackendRequests)}`,
      ).toEqual([]);
    },
    assertCriticalResponsesTagged() {
      const invalid = records.filter((record) => {
        if (isExpectedUnhandledApi(record)) {
          return false;
        }
        if (record.failed) {
          return true;
        }
        if (!record.mockResponse || !record.handler) {
          return true;
        }
        if (
          record.status !== undefined &&
          record.status >= 400 &&
          !record.handler.includes("unsupported") &&
          !record.overlay
        ) {
          return true;
        }
        return false;
      });
      expect(
        invalid,
        `Invalid mock API responses:\n${summarize(invalid)}`,
      ).toEqual([]);
    },
    assertOverlayResponsesTagged() {
      const invalid = records.filter((record) => {
        if (!record.overlay) {
          return false;
        }
        if (record.failed) {
          return true;
        }
        if (!record.mockResponse || !record.handler) {
          return true;
        }
        if (record.status === 501 && record.handler === "unhandled-api") {
          return true;
        }
        return false;
      });
      expect(
        invalid,
        `Invalid overlay API responses:\n${summarize(invalid)}`,
      ).toEqual([]);
    },
    assertNoUnexpectedUnhandledApis() {
      const unexpected = records.filter(
        (record) =>
          record.handler === "unhandled-api" && !isExpectedUnhandledApi(record),
      );
      expect(
        unexpected,
        `Unexpected unhandled demo-offline API calls:\n${summarize(unexpected)}`,
      ).toEqual([]);
    },
    assertConsumedApisCoveredByCriticalRegistry() {
      const uncovered = records.filter((record) => {
        if (isExpectedUnhandledApi(record)) {
          return false;
        }
        if (!record.handler || record.handler === "unhandled-api") {
          return true;
        }
        const matches = registryMatchesFor(record);
        return !matches.some(
          (entry) => entry.critical && entry.status !== "missing",
        );
      });
      const details = uncovered
        .map((record) => {
          const matches = registryMatchesFor(record);
          const registryState = matches.length
            ? matches
                .map(
                  (entry) =>
                    `${entry.method} ${entry.openapiPath} status=${entry.status} critical=${entry.critical}`,
                )
                .join("; ")
            : "no registry entry for handler";
          return `${record.step}: ${record.method} ${record.pathname} handler=${record.handler || "missing-handler"} registry=${registryState}`;
        })
        .join("\n");
      expect(
        uncovered,
        `E2E consumed API without critical registry coverage. Update src/mocks/contracts/coverage/registry before expanding demo-offline coverage.\n${details}`,
      ).toEqual([]);
    },
    summary() {
      return summarize(records);
    },
  };
}

export async function responseJson(response: Response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

export async function probeUnhandledApi(page: Page) {
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/__demo_e2e_missing_probe");
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = await response.text();
    }

    return {
      status: response.status,
      handler: response.headers.get("X-Mock-Handler"),
      mockResponse: response.headers.get("X-Mock-Response"),
      body,
    };
  });

  expect(result.status).toBe(501);
  expect(result.handler).toBe("unhandled-api");
  expect(result.mockResponse).toBe("true");
  expect(JSON.stringify(result.body)).toContain("MOCK_API_NOT_IMPLEMENTED");
}
