import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import ts from "typescript";

export const HTTP_METHODS = [
  "GET",
  "POST",
  "PUT",
  "DELETE",
  "PATCH",
  "OPTIONS",
  "HEAD",
];
export const HTTP_METHOD_SET = new Set(HTTP_METHODS);
export const OPENAPI_METHOD_SET = new Set(
  HTTP_METHODS.map((method) => method.toLowerCase()),
);

export const CONTRACT_COVERAGE_STATUSES = [
  "mock-handled",
  "real-only",
  "unsupported-501",
  "legacy-local-contract",
  "missing",
];

export const CONTRACT_SCHEMA_STATUSES = [
  "openapi-validated",
  "schema-unavailable",
  "binary-response",
  "local-schema-validated",
  "not-applicable",
];

export function resolveFrontendRoot(cwd = process.cwd()) {
  const directPackage = path.join(cwd, "package.json");
  if (
    existsSync(directPackage) &&
    path.basename(cwd) === "ruoyi-fastapi-frontend"
  ) {
    return cwd;
  }

  const nested = path.join(cwd, "ruoyi-fastapi-frontend");
  if (existsSync(path.join(nested, "package.json"))) {
    return nested;
  }

  throw new Error(`Unable to locate ruoyi-fastapi-frontend from ${cwd}`);
}

export function resolveRepoRoot(cwd = process.cwd()) {
  const frontendRoot = resolveFrontendRoot(cwd);
  return path.dirname(frontendRoot);
}

export function operationKey(method, openapiPath) {
  return `${String(method).toUpperCase()} ${openapiPath}`;
}

function readJson(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Unable to read JSON ${filePath}: ${message}`);
  }
}

const registrySchemaValidators = new Map();

function getRegistrySchemaValidator(frontendRoot) {
  const schemaPath = path.join(
    frontendRoot,
    "src/mocks/contracts/coverage/registry.schema.json",
  );
  if (!registrySchemaValidators.has(schemaPath)) {
    if (!existsSync(schemaPath)) {
      throw new Error(
        `Missing contract registry schema at ${path.relative(path.dirname(frontendRoot), schemaPath)}`,
      );
    }
    const ajv = new Ajv2020({ allErrors: true, strict: false });
    registrySchemaValidators.set(schemaPath, ajv.compile(readJson(schemaPath)));
  }
  return registrySchemaValidators.get(schemaPath);
}

function formatSchemaError(error) {
  const location = error.instancePath || "/";
  const detail =
    error.keyword === "additionalProperties" &&
    error.params?.additionalProperty
      ? `unknown property ${error.params.additionalProperty}`
      : (error.message ?? "schema validation failed");
  return `${location}: ${detail}`;
}

function validateRegistryDocument(parsed, file, frontendRoot, repoRoot) {
  const validate = getRegistrySchemaValidator(frontendRoot);
  if (validate(parsed)) return;

  const details = (validate.errors ?? []).map(formatSchemaError).join("; ");
  throw new Error(
    `${path.relative(repoRoot, file)} does not match registry.schema.json: ${details}`,
  );
}

function stableStringify(value) {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(",")}]`;
  }

  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
    .join(",")}}`;
}

export function fingerprintOpenApi(openApiDocument) {
  return createHash("sha256")
    .update(stableStringify(openApiDocument))
    .digest("hex");
}

function isEmptySchema(schema) {
  return (
    !schema ||
    (typeof schema === "object" &&
      !Array.isArray(schema) &&
      Object.keys(schema).length === 0)
  );
}

function pickResponse(operation, preferredStatus = "200") {
  const responses = operation.responses ?? {};
  if (responses[preferredStatus]) return responses[preferredStatus];

  const first2xx = Object.keys(responses)
    .filter((status) => /^2\d\d$/.test(status))
    .sort()[0];
  if (first2xx) return responses[first2xx];

  return responses.default ?? Object.values(responses)[0];
}

function getResponseSchemaInfo(operation) {
  const response = pickResponse(operation);
  const content = response?.content ?? {};
  const contentTypes = Object.keys(content).sort();
  const jsonContentType =
    contentTypes.find((type) => type.toLowerCase() === "application/json") ??
    contentTypes.find((type) => type.toLowerCase().endsWith("+json"));

  if (!contentTypes.length) {
    return {
      responseSchemaAvailability: "missing",
      responseContentTypes: [],
    };
  }

  if (!jsonContentType) {
    return {
      responseSchemaAvailability: contentTypes.some((type) =>
        /octet-stream|zip|msword|excel|xml|text\/plain/i.test(type),
      )
        ? "binary-response"
        : "missing",
      responseContentTypes: contentTypes,
    };
  }

  const schema = content[jsonContentType]?.schema;
  return {
    responseSchemaAvailability: isEmptySchema(schema) ? "empty" : "available",
    responseContentTypes: contentTypes,
  };
}

export function readOpenApiDocument(frontendRoot = resolveFrontendRoot()) {
  const openApiPath = path.resolve(frontendRoot, "../shared/openapi.json");
  if (!existsSync(openApiPath)) {
    throw new Error(
      `Missing OpenAPI artifact at ${path.relative(path.dirname(frontendRoot), openApiPath)}. Run yarn api:generate or export shared/openapi.json.`,
    );
  }
  return readJson(openApiPath);
}

export function enumerateOpenApiOperations(openApiDocument) {
  const operations = [];
  const paths = openApiDocument.paths ?? {};

  for (const [openapiPath, pathItem] of Object.entries(paths)) {
    for (const [rawMethod, operation] of Object.entries(pathItem ?? {})) {
      if (!OPENAPI_METHOD_SET.has(rawMethod)) continue;
      const method = rawMethod.toUpperCase();
      const schemaInfo = getResponseSchemaInfo(operation ?? {});
      operations.push({
        method,
        openapiPath,
        operationId: operation?.operationId ?? "",
        tags: Array.isArray(operation?.tags) ? operation.tags : [],
        summary: operation?.summary ?? "",
        ...schemaInfo,
      });
    }
  }

  return operations.sort(
    (left, right) =>
      left.openapiPath.localeCompare(right.openapiPath) ||
      left.method.localeCompare(right.method),
  );
}

function walkJsonFiles(directory) {
  if (!existsSync(directory)) return [];
  const files = [];
  for (const entry of readdirSync(directory).sort()) {
    const absolute = path.join(directory, entry);
    const stat = statSync(absolute);
    if (stat.isDirectory()) {
      files.push(...walkJsonFiles(absolute));
    } else if (entry.endsWith(".json")) {
      files.push(absolute);
    }
  }
  return files;
}

export function loadRegistryEntries(frontendRoot = resolveFrontendRoot()) {
  const repoRoot = path.dirname(frontendRoot);
  const registryRoot = path.join(
    frontendRoot,
    "src/mocks/contracts/coverage/registry",
  );
  if (!existsSync(registryRoot)) {
    throw new Error(
      `Missing contract registry directory at ${path.relative(repoRoot, registryRoot)}`,
    );
  }

  const entries = [];
  for (const file of walkJsonFiles(registryRoot)) {
    const parsed = readJson(file);
    validateRegistryDocument(parsed, file, frontendRoot, repoRoot);
    if (!Array.isArray(parsed)) {
      throw new Error(
        `${path.relative(repoRoot, file)} must contain a JSON array`,
      );
    }
    for (const entry of parsed) {
      entries.push({
        ...entry,
        registryFile: path.relative(repoRoot, file),
      });
    }
  }

  return entries.sort(
    (left, right) =>
      left.openapiPath.localeCompare(right.openapiPath) ||
      left.method.localeCompare(right.method),
  );
}

function stripApiPrefix(value) {
  let normalized = String(value ?? "").trim();
  normalized = normalized.replace(/^https?:\/\/[^/]+/i, "");
  normalized = normalized.replace(/\?.*$/, "");
  normalized = normalized.replace(/^\*/, "");
  normalized = normalized.replace(/^<apiPrefix>/, "");
  normalized = normalized.replace(/^\/api(?=\/|$)/, "");
  normalized = normalized.replace(/\/+/g, "/");
  if (!normalized.startsWith("/")) normalized = `/${normalized}`;
  if (normalized.length > 1 && normalized.endsWith("/"))
    normalized = normalized.slice(0, -1);
  return normalized;
}

function splitPatternSegments(value) {
  const stripped = stripApiPrefix(value);
  return stripped
    .split("/")
    .filter(Boolean)
    .map((segment) => {
      if (/^:[^/]+$/.test(segment) || /^\{[^/]+\}$/.test(segment))
        return ":param";
      return segment;
    });
}

export function pathPatternsMatch(openapiPath, mswPath) {
  const openapiSegments = splitPatternSegments(openapiPath);
  const mswSegments = splitPatternSegments(mswPath);
  if (openapiSegments.length !== mswSegments.length) return false;

  return openapiSegments.every((segment, index) => {
    const other = mswSegments[index];
    if (segment === ":param" || other === ":param") {
      return segment === other;
    }
    return segment === other;
  });
}

function ensureString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function ensureStringArray(value) {
  return Array.isArray(value) && value.every((item) => ensureString(item));
}

function hasAllFields(entry, fields) {
  return fields.every((field) => ensureString(entry[field]));
}

function testPathExists(repoRoot, frontendRoot, testPath) {
  if (!ensureString(testPath) || path.isAbsolute(testPath)) return false;
  return (
    existsSync(path.resolve(repoRoot, testPath)) ||
    existsSync(path.resolve(frontendRoot, testPath))
  );
}

function isStringLiteralLike(node) {
  return ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node);
}

function getPropertyNameText(name) {
  if (!name) return undefined;
  if (ts.isIdentifier(name) || ts.isStringLiteral(name)) return name.text;
  return undefined;
}

function getHttpMethodFromExpression(expression) {
  if (!ts.isPropertyAccessExpression(expression)) return undefined;
  if (!ts.isIdentifier(expression.expression)) return undefined;
  if (expression.expression.text !== "http") return undefined;

  const method = expression.name.text.toUpperCase();
  return HTTP_METHOD_SET.has(method) ? method : undefined;
}

function getCreateApiPathLiteral(argument) {
  if (!argument || !ts.isCallExpression(argument)) return undefined;
  if (!ts.isIdentifier(argument.expression)) return undefined;
  if (argument.expression.text !== "createApiPath") return undefined;

  const pathArgument = argument.arguments[0];
  return pathArgument && isStringLiteralLike(pathArgument)
    ? pathArgument.text
    : undefined;
}

function findLiteralTag(node) {
  let literalTag;
  function visit(current) {
    if (literalTag) return;
    if (ts.isPropertyAssignment(current)) {
      const propertyName = getPropertyNameText(current.name);
      if (propertyName === "tag" && isStringLiteralLike(current.initializer)) {
        literalTag = current.initializer.text;
        return;
      }
    }
    ts.forEachChild(current, visit);
  }
  visit(node);
  return literalTag;
}

function collectRuntimeHandlerDefinitions(frontendRoot) {
  const handlerRoot = path.join(frontendRoot, "src/mocks/handlers");
  if (!existsSync(handlerRoot)) return [];

  const definitions = [];
  const repoRoot = path.dirname(frontendRoot);
  for (const file of walkTsFiles(handlerRoot)) {
    if (/\.(test|spec)\.[tj]sx?$/.test(file)) continue;
    if (path.basename(file) === "error-common.ts") continue;

    const source = readFileSync(file, "utf8");
    const sourceFile = ts.createSourceFile(
      file,
      source,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TS,
    );

    function visit(node) {
      if (ts.isCallExpression(node)) {
        const method = getHttpMethodFromExpression(node.expression);
        const mswPath = getCreateApiPathLiteral(node.arguments[0]);
        if (method && mswPath) {
          definitions.push({
            method,
            mswPath,
            handlerTag: findLiteralTag(node),
            file: path.relative(repoRoot, file),
          });
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(sourceFile);
  }
  return definitions.sort(
    (left, right) =>
      left.mswPath.localeCompare(right.mswPath) ||
      left.method.localeCompare(right.method) ||
      (left.handlerTag ?? "").localeCompare(right.handlerTag ?? ""),
  );
}

function walkTsFiles(directory) {
  if (!existsSync(directory)) return [];
  const files = [];
  for (const entry of readdirSync(directory).sort()) {
    const absolute = path.join(directory, entry);
    const stat = statSync(absolute);
    if (stat.isDirectory()) {
      files.push(...walkTsFiles(absolute));
    } else if (/\.(ts|tsx|js|jsx|vue)$/.test(entry)) {
      files.push(absolute);
    }
  }
  return files;
}

function collectLocalContractNames(frontendRoot) {
  const localContractPath = path.join(
    frontendRoot,
    "src/mocks/contracts/local.ts",
  );
  if (!existsSync(localContractPath)) return new Set();
  const source = readFileSync(localContractPath, "utf8");
  const names = new Set();
  for (const match of source.matchAll(
    /export\s+(?:interface|type|class|function|const)\s+([A-Za-z0-9_]+)/g,
  )) {
    names.add(match[1]);
  }
  return names;
}

function collectApiWrapperWarnings(frontendRoot, registryByKey) {
  const apiRoot = path.join(frontendRoot, "src/api");
  const warnings = [];
  if (!existsSync(apiRoot)) return warnings;

  const criticalPathPattern =
    /^\/(?:captchaImage|login|getInfo|getRouters|auth\/(?:logout|csrf-token|refresh)|system\/(?:menu|dict|role|dept)|project|simulation)/;

  for (const file of walkTsFiles(apiRoot)) {
    if (file.includes(`${path.sep}_generated${path.sep}`)) continue;
    const source = readFileSync(file, "utf8");
    for (const match of source.matchAll(/['"`](\/[A-Za-z0-9_./{}:-]+)['"`]/g)) {
      const literalPath = match[1];
      if (!criticalPathPattern.test(literalPath)) continue;
      const candidate = stripApiPrefix(literalPath);
      for (const entry of registryByKey.values()) {
        if (!pathPatternsMatch(entry.openapiPath, candidate)) continue;
        if (!entry.critical) {
          warnings.push({
            code: "critical-audit-signal",
            method: entry.method,
            openapiPath: entry.openapiPath,
            file: path.relative(path.dirname(frontendRoot), file),
            message: `${entry.method} ${entry.openapiPath} is referenced from a likely demo-offline wrapper but is not marked critical`,
          });
        }
      }
    }
  }

  return uniqueWarnings(warnings);
}

function uniqueWarnings(warnings) {
  const seen = new Set();
  return warnings.filter((warning) => {
    const key = `${warning.code}:${warning.method ?? ""}:${warning.openapiPath ?? ""}:${warning.file ?? ""}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function addFailure(failures, code, entry, message) {
  failures.push({
    code,
    method: entry?.method,
    openapiPath: entry?.openapiPath,
    handlerTag: entry?.handlerTag,
    file: entry?.registryFile,
    message,
  });
}

function findRuntimeHandlerDefinitions(entry, runtimeHandlerDefinitions) {
  if (!ensureString(entry.openapiPath) || !HTTP_METHOD_SET.has(entry.method)) {
    return [];
  }
  return runtimeHandlerDefinitions.filter(
    (definition) =>
      definition.method === entry.method &&
      pathPatternsMatch(entry.openapiPath, definition.mswPath),
  );
}

function validateEntry(entry, context) {
  const {
    failures,
    operationByKey,
    repoRoot,
    frontendRoot,
    runtimeHandlerDefinitions,
    localContractNames,
  } = context;
  const key = operationKey(entry.method, entry.openapiPath);
  const operation = operationByKey.get(key);

  if (!HTTP_METHOD_SET.has(entry.method)) {
    addFailure(
      failures,
      "invalid-method",
      entry,
      `Unsupported method ${entry.method}`,
    );
  }
  if (!ensureString(entry.openapiPath) || !entry.openapiPath.startsWith("/")) {
    addFailure(
      failures,
      "invalid-openapi-path",
      entry,
      "openapiPath must start with /",
    );
  }
  if (!ensureString(entry.owner)) {
    addFailure(failures, "missing-owner", entry, "owner is required");
  }
  if (!CONTRACT_COVERAGE_STATUSES.includes(entry.status)) {
    addFailure(
      failures,
      "invalid-status",
      entry,
      `Unsupported status ${entry.status}`,
    );
  }
  if (!CONTRACT_SCHEMA_STATUSES.includes(entry.schemaStatus)) {
    addFailure(
      failures,
      "invalid-schema-status",
      entry,
      `Unsupported schemaStatus ${entry.schemaStatus}`,
    );
  }
  if (typeof entry.critical !== "boolean") {
    addFailure(failures, "invalid-critical", entry, "critical must be boolean");
  }
  if (!ensureStringArray(entry.tests)) {
    addFailure(
      failures,
      "invalid-tests",
      entry,
      "tests must be an array of relative paths",
    );
  } else {
    for (const testPath of entry.tests) {
      if (!testPathExists(repoRoot, frontendRoot, testPath)) {
        addFailure(
          failures,
          "missing-test-file",
          entry,
          `Referenced test file does not exist: ${testPath}`,
        );
      }
    }
  }

  if (!operation) {
    addFailure(
      failures,
      "orphan-registry-entry",
      entry,
      `${key} is not present in shared/openapi.json`,
    );
  }

  if (
    entry.mswPath &&
    operation &&
    !pathPatternsMatch(entry.openapiPath, entry.mswPath)
  ) {
    addFailure(
      failures,
      "msw-path-mismatch",
      entry,
      `${entry.mswPath} does not match OpenAPI path ${entry.openapiPath}`,
    );
  }

  if (["mock-handled", "unsupported-501"].includes(entry.status)) {
    const runtimeHandlers = findRuntimeHandlerDefinitions(
      entry,
      runtimeHandlerDefinitions,
    );
    if (!runtimeHandlers.length) {
      addFailure(
        failures,
        "runtime-handler-not-found",
        entry,
        `${entry.method} ${entry.openapiPath} has no matching runtime handler in src/mocks/handlers`,
      );
    } else if (
      entry.handlerTag &&
      !runtimeHandlers.some(
        (definition) => definition.handlerTag === entry.handlerTag,
      )
    ) {
      const actualTags = runtimeHandlers
        .map((definition) => definition.handlerTag ?? "<missing>")
        .join(", ");
      addFailure(
        failures,
        "handler-tag-mismatch",
        entry,
        `registry handlerTag ${entry.handlerTag} does not match runtime handler tag(s): ${actualTags}`,
      );
    }
  }

  if (entry.status === "mock-handled") {
    if (!hasAllFields(entry, ["mswPath", "handlerTag"])) {
      addFailure(
        failures,
        "mock-handled-missing-metadata",
        entry,
        "mock-handled entries require mswPath and handlerTag",
      );
    }
    if (!entry.tests?.length) {
      addFailure(
        failures,
        "mock-handled-missing-tests",
        entry,
        "mock-handled entries require tests",
      );
    }
    if (entry.schemaStatus === "not-applicable") {
      addFailure(
        failures,
        "mock-handled-schema-missing",
        entry,
        "mock-handled entries require an explicit schema status",
      );
    }
  }

  if (entry.status === "unsupported-501") {
    if (!hasAllFields(entry, ["mswPath", "handlerTag", "reason"])) {
      addFailure(
        failures,
        "unsupported-missing-metadata",
        entry,
        "unsupported-501 entries require mswPath, handlerTag, and reason",
      );
    }
    if (!entry.tests?.length) {
      addFailure(
        failures,
        "unsupported-missing-tests",
        entry,
        "unsupported-501 entries require tests",
      );
    }
  }

  if (entry.status === "real-only") {
    if (entry.critical) {
      addFailure(
        failures,
        "critical-real-only",
        entry,
        "critical endpoints cannot be real-only",
      );
    }
    if (!ensureString(entry.reason)) {
      addFailure(
        failures,
        "real-only-missing-reason",
        entry,
        "real-only entries require reason",
      );
    }
  }

  if (entry.status === "legacy-local-contract") {
    if (!hasAllFields(entry, ["localContract", "reason", "migrationTarget"])) {
      addFailure(
        failures,
        "legacy-local-contract-missing-metadata",
        entry,
        "legacy-local-contract entries require localContract, reason, and migrationTarget",
      );
    }
    if (entry.localContract && !localContractNames.has(entry.localContract)) {
      addFailure(
        failures,
        "local-contract-not-found",
        entry,
        `${entry.localContract} is not exported by src/mocks/contracts/local.ts`,
      );
    }
    if (
      operation?.responseSchemaAvailability === "available" &&
      !/兼容例外|compatibility|unreliable|不可靠/.test(entry.reason ?? "")
    ) {
      addFailure(
        failures,
        "legacy-local-contract-openapi-schema-available",
        entry,
        "OpenAPI response schema is available; legacy-local-contract needs an explicit compatibility exception",
      );
    }
  }

  if (entry.status === "missing") {
    if (entry.critical) {
      addFailure(
        failures,
        "critical-missing",
        entry,
        "critical endpoints cannot be missing",
      );
    }
    if (
      !hasAllFields(entry, ["owner", "reason", "impact", "migrationTarget"])
    ) {
      addFailure(
        failures,
        "missing-debt-incomplete",
        entry,
        "missing entries require owner, reason, impact, and migrationTarget",
      );
    }
  }

  if (
    ["schema-unavailable", "binary-response"].includes(entry.schemaStatus) &&
    !ensureString(entry.reason)
  ) {
    addFailure(
      failures,
      "schema-exception-missing-reason",
      entry,
      `${entry.schemaStatus} requires reason`,
    );
  }
}

export function buildMockContractReport(options = {}) {
  const frontendRoot = resolveFrontendRoot(options.cwd ?? process.cwd());
  const repoRoot = path.dirname(frontendRoot);
  const openApiDocument = readOpenApiDocument(frontendRoot);
  const operations = enumerateOpenApiOperations(openApiDocument);
  const operationByKey = new Map(
    operations.map((operation) => [
      operationKey(operation.method, operation.openapiPath),
      operation,
    ]),
  );
  const registryEntries = loadRegistryEntries(frontendRoot);
  const failures = [];
  const warnings = [];
  const runtimeHandlerDefinitions = collectRuntimeHandlerDefinitions(frontendRoot);
  const localContractNames = collectLocalContractNames(frontendRoot);
  const seenEntryKeys = new Map();
  const seenHandlerTags = new Map();

  for (const entry of registryEntries) {
    const key = operationKey(entry.method, entry.openapiPath);
    if (seenEntryKeys.has(key)) {
      addFailure(
        failures,
        "duplicate-registry-entry",
        entry,
        `${key} is duplicated in ${seenEntryKeys.get(key)} and ${entry.registryFile}`,
      );
    }
    seenEntryKeys.set(key, entry.registryFile);

    if (
      ["mock-handled", "unsupported-501"].includes(entry.status) &&
      entry.handlerTag
    ) {
      if (seenHandlerTags.has(entry.handlerTag)) {
        addFailure(
          failures,
          "duplicate-handler-tag",
          entry,
          `${entry.handlerTag} is duplicated by ${seenHandlerTags.get(entry.handlerTag)} and ${key}`,
        );
      }
      seenHandlerTags.set(entry.handlerTag, key);
    }
  }

  for (const operation of operations) {
    const key = operationKey(operation.method, operation.openapiPath);
    if (!seenEntryKeys.has(key)) {
      addFailure(
        failures,
        "missing-registry-entry",
        operation,
        `${key} has no registry entry`,
      );
    }
  }

  const context = {
    failures,
    operationByKey,
    repoRoot,
    frontendRoot,
    runtimeHandlerDefinitions,
    localContractNames,
  };
  registryEntries.forEach((entry) => validateEntry(entry, context));

  const registryByKey = new Map(
    registryEntries.map((entry) => [
      operationKey(entry.method, entry.openapiPath),
      entry,
    ]),
  );
  warnings.push(...collectApiWrapperWarnings(frontendRoot, registryByKey));

  const zeroStatusCounts = Object.fromEntries(
    CONTRACT_COVERAGE_STATUSES.map((status) => [status, 0]),
  );
  const byStatus = registryEntries.reduce((accumulator, entry) => {
    if (entry.status in accumulator) accumulator[entry.status] += 1;
    return accumulator;
  }, zeroStatusCounts);

  const criticalFailures = failures.filter((failure) =>
    [
      "critical-missing",
      "critical-real-only",
      "mock-handled-missing-metadata",
      "runtime-handler-not-found",
      "handler-tag-mismatch",
      "missing-test-file",
    ].includes(failure.code),
  ).length;

  const entries = registryEntries
    .map((entry) => {
      const operation = operationByKey.get(
        operationKey(entry.method, entry.openapiPath),
      );
      return {
        ...entry,
        operationId: operation?.operationId ?? "",
        tags: operation?.tags ?? [],
        summary: operation?.summary ?? "",
        responseSchemaAvailability:
          operation?.responseSchemaAvailability ?? "missing",
        responseContentTypes: operation?.responseContentTypes ?? [],
      };
    })
    .sort(
      (left, right) =>
        left.openapiPath.localeCompare(right.openapiPath) ||
        left.method.localeCompare(right.method),
    );

  return {
    artifact: {
      path: "shared/openapi.json",
      openapi: openApiDocument.openapi ?? "",
      title: openApiDocument.info?.title,
      version: openApiDocument.info?.version,
      fingerprint: fingerprintOpenApi(openApiDocument),
      operationCount: operations.length,
    },
    summary: {
      operationCount: operations.length,
      byStatus,
      criticalTotal: registryEntries.filter((entry) => entry.critical).length,
      criticalFailures,
      schemaValidated: registryEntries.filter(
        (entry) => entry.schemaStatus === "openapi-validated",
      ).length,
      schemaUnavailable: registryEntries.filter(
        (entry) => entry.schemaStatus === "schema-unavailable",
      ).length,
      binaryResponses: registryEntries.filter(
        (entry) => entry.schemaStatus === "binary-response",
      ).length,
      localContracts: registryEntries.filter(
        (entry) => entry.status === "legacy-local-contract",
      ).length,
    },
    entries,
    failures: failures.sort(sortIssue),
    warnings: warnings.sort(sortIssue),
  };
}

function sortIssue(left, right) {
  return (
    (left.openapiPath ?? "").localeCompare(right.openapiPath ?? "") ||
    (left.method ?? "").localeCompare(right.method ?? "") ||
    left.code.localeCompare(right.code) ||
    left.message.localeCompare(right.message)
  );
}

export function formatSummary(report) {
  const lines = [
    "Mock contract coverage summary",
    `OpenAPI: ${report.artifact.openapi} ${report.artifact.title ?? ""} ${report.artifact.version ?? ""}`.trim(),
    `Fingerprint: ${report.artifact.fingerprint}`,
    `Operations: ${report.summary.operationCount}`,
    `Statuses: ${CONTRACT_COVERAGE_STATUSES.map((status) => `${status}=${report.summary.byStatus[status] ?? 0}`).join(", ")}`,
    `Critical: total=${report.summary.criticalTotal}, failures=${report.summary.criticalFailures}`,
    `Schema: openapi-validated=${report.summary.schemaValidated}, schema-unavailable=${report.summary.schemaUnavailable}, binary-response=${report.summary.binaryResponses}`,
    `Local contracts: ${report.summary.localContracts}`,
  ];

  if (report.failures.length) {
    lines.push("", "Failures:");
    report.failures.forEach((failure) => {
      lines.push(
        `- [${failure.code}] ${failure.method ?? ""} ${failure.openapiPath ?? ""} ${failure.handlerTag ? `(${failure.handlerTag}) ` : ""}${failure.message}`.trim(),
      );
    });
  }

  if (report.warnings.length) {
    lines.push("", "Warnings:");
    report.warnings.forEach((warning) => {
      lines.push(
        `- [${warning.code}] ${warning.method ?? ""} ${warning.openapiPath ?? ""} ${warning.file ? `${warning.file}: ` : ""}${warning.message}`.trim(),
      );
    });
  }

  return `${lines.join("\n")}\n`;
}

export function formatMarkdown(report) {
  const statusRows = CONTRACT_COVERAGE_STATUSES.map(
    (status) => `| ${status} | ${report.summary.byStatus[status] ?? 0} |`,
  );
  const entryRows = report.entries.map(
    (entry) =>
      `| ${entry.method} | ${entry.openapiPath} | ${entry.owner} | ${entry.status} | ${entry.critical ? "yes" : "no"} | ${entry.handlerTag ?? ""} | ${entry.schemaStatus} | ${entry.tests.join("<br>")} | ${entry.migrationTarget ?? entry.reason ?? ""} |`,
  );

  const lines = [
    "# Mock Contract Coverage",
    "",
    `- OpenAPI: ${report.artifact.openapi} ${report.artifact.title ?? ""} ${report.artifact.version ?? ""}`.trim(),
    `- Fingerprint: ${report.artifact.fingerprint}`,
    `- Operations: ${report.summary.operationCount}`,
    `- Critical: total ${report.summary.criticalTotal}, failures ${report.summary.criticalFailures}`,
    `- Schema: openapi-validated ${report.summary.schemaValidated}, schema-unavailable ${report.summary.schemaUnavailable}, binary-response ${report.summary.binaryResponses}`,
    `- Local contracts: ${report.summary.localContracts}`,
    "",
    "## Status Counts",
    "",
    "| Status | Count |",
    "| --- | ---: |",
    ...statusRows,
    "",
    "## Entries",
    "",
    "| Method | Path | Owner | Status | Critical | Handler Tag | Schema | Tests | Migration/Risk |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ...entryRows,
  ];

  if (report.failures.length) {
    lines.push("", "## Failures", "");
    report.failures.forEach((failure) => {
      lines.push(
        `- **${failure.code}** ${failure.method ?? ""} ${failure.openapiPath ?? ""}: ${failure.message}`,
      );
    });
  }

  if (report.warnings.length) {
    lines.push("", "## Warnings", "");
    report.warnings.forEach((warning) => {
      lines.push(
        `- **${warning.code}** ${warning.method ?? ""} ${warning.openapiPath ?? ""}: ${warning.message}`,
      );
    });
  }

  return `${lines.join("\n")}\n`;
}

export function writeReportFile(targetPath, content) {
  const absolute = path.resolve(process.cwd(), targetPath);
  mkdirSync(path.dirname(absolute), { recursive: true });
  writeFileSync(absolute, content);
}
