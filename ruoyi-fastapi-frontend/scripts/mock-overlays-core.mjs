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

import {
  buildMockContractReport,
  operationKey,
  pathPatternsMatch,
  resolveFrontendRoot,
} from "./mock-contracts-core.mjs";

export const OVERLAY_STATE_TYPES = [
  "empty",
  "latency",
  "problem",
  "forbidden",
  "timeout",
  "unsupported",
  "readonly",
];

const CORE_MATRIX_REQUIREMENTS = [
  {
    code: "project-list-empty",
    description: "项目列表空态",
  },
  {
    code: "project-create-500",
    description: "项目写入错误",
  },
  {
    code: "version-list-empty",
    description: "版本列表空态",
  },
  {
    code: "topology-save-500",
    description: "拓扑保存错误",
  },
  {
    code: "simulation-start-unsupported",
    description: "simulation unsupported 控制状态",
  },
];

function readJson(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Unable to read JSON ${filePath}: ${message}`);
  }
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

function getSchemaValidator(frontendRoot) {
  const schemaPath = path.join(
    frontendRoot,
    "src/mocks/overlays/registry.schema.json",
  );
  if (!existsSync(schemaPath)) {
    throw new Error(
      `Missing overlay registry schema at ${path.relative(path.dirname(frontendRoot), schemaPath)}`,
    );
  }
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  return ajv.compile(readJson(schemaPath));
}

function formatSchemaError(error) {
  const location = error.instancePath || "/";
  const detail =
    error.keyword === "additionalProperties" && error.params?.additionalProperty
      ? `unknown property ${error.params.additionalProperty}`
      : (error.message ?? "schema validation failed");
  return `${location}: ${detail}`;
}

function validateOverlayDocument(
  parsed,
  file,
  frontendRoot,
  repoRoot,
  validate,
) {
  if (validate(parsed)) return;
  const details = (validate.errors ?? []).map(formatSchemaError).join("; ");
  throw new Error(
    `${path.relative(repoRoot, file)} does not match registry.schema.json: ${details}`,
  );
}

export function loadOverlayRegistryEntries(
  frontendRoot = resolveFrontendRoot(),
) {
  const repoRoot = path.dirname(frontendRoot);
  const registryRoot = path.join(frontendRoot, "src/mocks/overlays/registry");
  if (!existsSync(registryRoot)) {
    throw new Error(
      `Missing overlay registry directory at ${path.relative(repoRoot, registryRoot)}`,
    );
  }

  const validate = getSchemaValidator(frontendRoot);
  const entries = [];
  for (const file of walkJsonFiles(registryRoot)) {
    const parsed = readJson(file);
    validateOverlayDocument(parsed, file, frontendRoot, repoRoot, validate);
    parsed.forEach((entry) => {
      entries.push({
        ...entry,
        registryFile: path.relative(repoRoot, file),
      });
    });
  }

  return sortOverlayEntries(entries);
}

function sortOverlayEntries(entries) {
  return [...entries].sort(
    (left, right) =>
      Number(right.coreMatrix) - Number(left.coreMatrix) ||
      left.target.openapiPath.localeCompare(right.target.openapiPath) ||
      left.target.method.localeCompare(right.target.method) ||
      left.id.localeCompare(right.id),
  );
}

function sortIssue(left, right) {
  return (
    (left.overlayId ?? "").localeCompare(right.overlayId ?? "") ||
    (left.openapiPath ?? "").localeCompare(right.openapiPath ?? "") ||
    (left.method ?? "").localeCompare(right.method ?? "") ||
    left.code.localeCompare(right.code) ||
    left.message.localeCompare(right.message)
  );
}

function addIssue(target, code, entry, message) {
  target.push({
    code,
    overlayId: entry?.id,
    method: entry?.target?.method,
    openapiPath: entry?.target?.openapiPath,
    handlerTag: entry?.target?.handlerTag,
    file: entry?.registryFile,
    message,
  });
}

function testPathExists(repoRoot, frontendRoot, testPath) {
  if (!testPath || path.isAbsolute(testPath)) return false;
  return (
    existsSync(path.resolve(repoRoot, testPath)) ||
    existsSync(path.resolve(frontendRoot, testPath))
  );
}

function validateComposition(entry, byId, failures) {
  const compatible = entry.composition?.compatibleWith ?? [];
  const conflicts = entry.composition?.conflictsWith ?? [];

  for (const id of [...compatible, ...conflicts]) {
    if (!byId.has(id)) {
      addIssue(
        failures,
        "composition-overlay-not-found",
        entry,
        `${id} is not present in overlay registry.`,
      );
    }
  }

  if (compatible.includes(entry.id) || conflicts.includes(entry.id)) {
    addIssue(
      failures,
      "composition-self-reference",
      entry,
      "Overlay composition cannot reference itself.",
    );
  }

  for (const id of compatible) {
    if (conflicts.includes(id)) {
      addIssue(
        failures,
        "composition-contradiction",
        entry,
        `${id} is both compatible and conflicting.`,
      );
    }
  }
}

function validateContractAlignment(
  entry,
  contractByKey,
  repoRoot,
  frontendRoot,
  failures,
  warnings,
) {
  const key = operationKey(entry.target.method, entry.target.openapiPath);
  const contract = contractByKey.get(key);

  if (!contract) {
    addIssue(
      failures,
      "target-contract-not-found",
      entry,
      `${key} is not present in contract coverage registry.`,
    );
    return;
  }

  if (["missing", "real-only"].includes(contract.status)) {
    if (
      !(
        entry.stateType === "unsupported" &&
        entry.contract?.exception === "unhandled-api"
      )
    ) {
      addIssue(
        failures,
        "target-contract-not-mockable",
        entry,
        `${key} is ${contract.status}; overlays can only target mock-handled/unsupported entries or explicit unhandled-api probes.`,
      );
    }
  }

  if (contract.handlerTag !== entry.target.handlerTag) {
    addIssue(
      failures,
      "handler-tag-mismatch",
      entry,
      `Overlay handlerTag ${entry.target.handlerTag} does not match contract handlerTag ${contract.handlerTag ?? "<missing>"}.`,
    );
  }

  if (
    contract.mswPath &&
    !pathPatternsMatch(contract.openapiPath, entry.target.mswPath)
  ) {
    addIssue(
      failures,
      "msw-path-mismatch",
      entry,
      `${entry.target.mswPath} does not match OpenAPI path ${contract.openapiPath}.`,
    );
  }

  if (!entry.tests?.length) {
    addIssue(
      failures,
      "missing-tests",
      entry,
      "Overlay entries require at least one test file.",
    );
  } else {
    for (const testPath of entry.tests) {
      if (!testPathExists(repoRoot, frontendRoot, testPath)) {
        addIssue(
          failures,
          "missing-test-file",
          entry,
          `Referenced test file does not exist: ${testPath}`,
        );
      }
    }
  }

  if (
    ["schema-unavailable", "local-schema-validated", "not-applicable"].includes(
      contract.schemaStatus,
    ) &&
    !entry.contract?.exception &&
    !["problem", "forbidden", "timeout", "unsupported"].includes(
      entry.stateType,
    )
  ) {
    addIssue(
      warnings,
      "schema-exception-unmarked",
      entry,
      `${key} has schemaStatus=${contract.schemaStatus}; mark contract.exception when this overlay should not count as OpenAPI schema-validated coverage.`,
    );
  }
}

function validatePairConflicts(entries, failures) {
  for (let leftIndex = 0; leftIndex < entries.length; leftIndex += 1) {
    for (
      let rightIndex = leftIndex + 1;
      rightIndex < entries.length;
      rightIndex += 1
    ) {
      const left = entries[leftIndex];
      const right = entries[rightIndex];
      const sameEndpoint =
        left.target.method === right.target.method &&
        left.target.openapiPath === right.target.openapiPath;
      const sameHandler = left.target.handlerTag === right.target.handlerTag;
      const leftCompat = left.composition?.compatibleWith?.includes(right.id);
      const rightCompat = right.composition?.compatibleWith?.includes(left.id);
      const leftConflict = left.composition?.conflictsWith?.includes(right.id);
      const rightConflict = right.composition?.conflictsWith?.includes(left.id);

      if (
        (sameEndpoint || sameHandler) &&
        !leftCompat &&
        !rightCompat &&
        !leftConflict &&
        !rightConflict
      ) {
        addIssue(
          failures,
          "implicit-overlay-conflict",
          right,
          `${right.id} shares target with ${left.id}; add compatibleWith or conflictsWith metadata.`,
        );
      }

      if ((leftCompat || rightCompat) && (leftConflict || rightConflict)) {
        addIssue(
          failures,
          "composition-contradiction",
          right,
          `${left.id} and ${right.id} are both compatible and conflicting.`,
        );
      }
    }
  }
}

function addCoreMatrixFailures(entries, failures) {
  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  for (const requirement of CORE_MATRIX_REQUIREMENTS) {
    const entry = byId.get(requirement.code);
    if (!entry) {
      failures.push({
        code: "core-matrix-missing",
        overlayId: requirement.code,
        message: `Core matrix overlay missing: ${requirement.description}.`,
      });
      continue;
    }
    if (!entry.coreMatrix || !entry.e2eEnabled) {
      addIssue(
        failures,
        "core-matrix-disabled",
        entry,
        `${requirement.description} must be coreMatrix=true and e2eEnabled=true.`,
      );
    }
  }
}

function addCriticalCoverageWarnings(entries, contractEntries, warnings) {
  const coveredTargets = new Set(
    entries.map((entry) =>
      operationKey(entry.target.method, entry.target.openapiPath),
    ),
  );
  for (const contract of contractEntries) {
    if (!contract.critical) continue;
    if (!["mock-handled", "unsupported-501"].includes(contract.status))
      continue;
    const key = operationKey(contract.method, contract.openapiPath);
    if (coveredTargets.has(key)) continue;
    warnings.push({
      code: "critical-overlay-missing",
      method: contract.method,
      openapiPath: contract.openapiPath,
      handlerTag: contract.handlerTag,
      message: `${key} is critical but has no page-state overlay yet; non-Core coverage is warning-only in this phase.`,
    });
  }
}

export function buildMockOverlayReport(options = {}) {
  const frontendRoot = resolveFrontendRoot(options.cwd ?? process.cwd());
  const repoRoot = path.dirname(frontendRoot);
  const entries = loadOverlayRegistryEntries(frontendRoot);
  const contractReport = buildMockContractReport({ cwd: frontendRoot });
  const contractByKey = new Map(
    contractReport.entries.map((entry) => [
      operationKey(entry.method, entry.openapiPath),
      entry,
    ]),
  );
  const failures = [];
  const warnings = [];
  const byId = new Map();

  for (const entry of entries) {
    if (byId.has(entry.id)) {
      addIssue(
        failures,
        "duplicate-overlay-id",
        entry,
        `${entry.id} is duplicated by ${byId.get(entry.id)} and ${entry.registryFile}.`,
      );
    }
    byId.set(entry.id, entry.registryFile);
  }

  for (const entry of entries) {
    validateComposition(entry, byId, failures);
    validateContractAlignment(
      entry,
      contractByKey,
      repoRoot,
      frontendRoot,
      failures,
      warnings,
    );
  }

  validatePairConflicts(entries, failures);
  addCoreMatrixFailures(entries, failures);
  addCriticalCoverageWarnings(entries, contractReport.entries, warnings);

  const byStateType = Object.fromEntries(
    OVERLAY_STATE_TYPES.map((stateType) => [stateType, 0]),
  );
  entries.forEach((entry) => {
    byStateType[entry.stateType] += 1;
  });

  return {
    summary: {
      overlayCount: entries.length,
      coreMatrix: entries.filter((entry) => entry.coreMatrix).length,
      e2eEnabled: entries.filter((entry) => entry.e2eEnabled).length,
      byStateType,
      failures: failures.length,
      warnings: warnings.length,
    },
    entries,
    failures: failures.sort(sortIssue),
    warnings: warnings.sort(sortIssue),
  };
}

export function formatSummary(report) {
  const lines = [
    "Mock overlay registry summary",
    `Overlays: total=${report.summary.overlayCount}, coreMatrix=${report.summary.coreMatrix}, e2eEnabled=${report.summary.e2eEnabled}`,
    `State types: ${OVERLAY_STATE_TYPES.map((stateType) => `${stateType}=${report.summary.byStateType[stateType] ?? 0}`).join(", ")}`,
    `Issues: failures=${report.summary.failures}, warnings=${report.summary.warnings}`,
  ];

  if (report.failures.length) {
    lines.push("", "Failures:");
    report.failures.forEach((failure) => {
      lines.push(
        `- [${failure.code}] ${failure.overlayId ?? ""} ${failure.method ?? ""} ${failure.openapiPath ?? ""} ${failure.handlerTag ? `(${failure.handlerTag}) ` : ""}${failure.message}`.trim(),
      );
    });
  }

  if (report.warnings.length) {
    lines.push("", "Warnings:");
    report.warnings.forEach((warning) => {
      lines.push(
        `- [${warning.code}] ${warning.overlayId ?? ""} ${warning.method ?? ""} ${warning.openapiPath ?? ""} ${warning.handlerTag ? `(${warning.handlerTag}) ` : ""}${warning.message}`.trim(),
      );
    });
  }

  return `${lines.join("\n")}\n`;
}

export function formatMarkdown(report) {
  const entryRows = report.entries.map(
    (entry) =>
      `| ${entry.id} | ${entry.stateType} | ${entry.target.method} | ${entry.target.openapiPath} | ${entry.target.handlerTag} | ${entry.pages.join("<br>")} | ${entry.tests.join("<br>")} | ${entry.coreMatrix ? "yes" : "no"} | ${entry.e2eEnabled ? "yes" : "no"} | ${entry.risk} |`,
  );

  const lines = [
    "# Mock Overlay Coverage",
    "",
    `- Overlays: ${report.summary.overlayCount}`,
    `- Core matrix: ${report.summary.coreMatrix}`,
    `- E2E enabled: ${report.summary.e2eEnabled}`,
    `- Failures: ${report.summary.failures}`,
    `- Warnings: ${report.summary.warnings}`,
    "",
    "## Entries",
    "",
    "| Overlay | State | Method | Path | Handler | Pages | Tests | Core | E2E | Risk |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ...entryRows,
  ];

  if (report.failures.length) {
    lines.push("", "## Failures", "");
    report.failures.forEach((failure) => {
      lines.push(
        `- **${failure.code}** ${failure.overlayId ?? ""}: ${failure.message}`,
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
