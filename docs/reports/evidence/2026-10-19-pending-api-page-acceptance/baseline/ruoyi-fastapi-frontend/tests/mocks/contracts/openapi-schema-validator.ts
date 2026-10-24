import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import Ajv, { type ErrorObject } from 'ajv';

type JsonRecord = Record<string, unknown>;

export interface ValidateOpenApiResponseOptions {
  method: string;
  openapiPath: string;
  status?: number;
  body: unknown;
  openApiPath?: string;
}

export interface ValidationResult {
  ok: boolean;
  skipped?: boolean;
  reason?: string;
  errors?: Array<{
    path: string;
    message: string;
    keyword: string;
  }>;
}

interface OpenApiOperation {
  responses?: Record<string, OpenApiResponse>;
}

interface OpenApiResponse {
  content?: Record<
    string,
    {
      schema?: JsonRecord;
    }
  >;
}

interface OpenApiDocument {
  paths?: Record<string, Record<string, OpenApiOperation>>;
  components?: {
    schemas?: Record<string, JsonRecord>;
  };
}

const DEFAULT_OPENAPI_PATH = resolve(process.cwd(), '../shared/openapi.json');

const cachedOpenApis = new Map<string, OpenApiDocument>();

function readOpenApiDocument(openApiPath = DEFAULT_OPENAPI_PATH): OpenApiDocument {
  if (!cachedOpenApis.has(openApiPath)) {
    cachedOpenApis.set(
      openApiPath,
      JSON.parse(readFileSync(openApiPath, 'utf8')) as OpenApiDocument
    );
  }
  return cachedOpenApis.get(openApiPath) as OpenApiDocument;
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isEmptySchema(schema: unknown): boolean {
  return isRecord(schema) && Object.keys(schema).length === 0;
}

function pickResponse(operation: OpenApiOperation, status: number): OpenApiResponse | undefined {
  const responses = operation.responses ?? {};
  const statusKey = String(status);
  if (responses[statusKey]) return responses[statusKey];

  const first2xx = Object.keys(responses)
    .filter((key) => /^2\d\d$/.test(key))
    .sort()[0];
  if (first2xx) return responses[first2xx];

  return responses.default ?? Object.values(responses)[0];
}

function resolveJsonPointer(document: OpenApiDocument, ref: string): JsonRecord | undefined {
  if (!ref.startsWith('#/')) return undefined;
  const segments = ref
    .slice(2)
    .split('/')
    .map((segment) => segment.replace(/~1/g, '/').replace(/~0/g, '~'));
  let current: unknown = document;
  for (const segment of segments) {
    if (!isRecord(current)) return undefined;
    current = current[segment];
  }
  return isRecord(current) ? current : undefined;
}

function dereferenceSchema(
  schema: unknown,
  document: OpenApiDocument,
  seenRefs = new Set<string>()
): unknown {
  if (Array.isArray(schema)) {
    return schema.map((item) => dereferenceSchema(item, document, seenRefs));
  }
  if (!isRecord(schema)) return schema;

  const ref = typeof schema.$ref === 'string' ? schema.$ref : undefined;
  if (ref) {
    if (seenRefs.has(ref)) return {};
    const target = resolveJsonPointer(document, ref);
    if (!target) return schema;
    const nextSeenRefs = new Set(seenRefs);
    nextSeenRefs.add(ref);
    const dereferenced = dereferenceSchema(target, document, nextSeenRefs);
    const siblings = Object.fromEntries(Object.entries(schema).filter(([key]) => key !== '$ref'));
    return Object.keys(siblings).length
      ? { ...(dereferenced as JsonRecord), ...siblings }
      : dereferenced;
  }

  return Object.fromEntries(
    Object.entries(schema).map(([key, value]) => [
      key,
      dereferenceSchema(value, document, seenRefs),
    ])
  );
}

function normalizeAjvErrors(
  errors: ErrorObject[] | null | undefined
): NonNullable<ValidationResult['errors']> {
  return (errors ?? []).map((error) => ({
    path: error.instancePath || '/',
    message: error.message ?? 'schema validation failed',
    keyword: error.keyword,
  }));
}

export function validateOpenApiResponse(options: ValidateOpenApiResponseOptions): ValidationResult {
  const document = readOpenApiDocument(options.openApiPath);
  const method = options.method.toLowerCase();
  const operation = document.paths?.[options.openapiPath]?.[method];
  if (!operation) {
    return {
      ok: false,
      errors: [
        {
          path: '/',
          message: `${options.method.toUpperCase()} ${options.openapiPath} is not in shared/openapi.json`,
          keyword: 'operation',
        },
      ],
    };
  }

  const response = pickResponse(operation, options.status ?? 200);
  const content = response?.content ?? {};
  const contentTypes = Object.keys(content);
  const jsonContentType =
    contentTypes.find((type) => type.toLowerCase() === 'application/json') ??
    contentTypes.find((type) => type.toLowerCase().endsWith('+json'));

  if (!contentTypes.length) {
    return { ok: true, skipped: true, reason: 'response schema is missing' };
  }
  if (!jsonContentType) {
    return {
      ok: true,
      skipped: true,
      reason: `non-json response: ${contentTypes.join(', ')}`,
    };
  }

  const schema = content[jsonContentType]?.schema;
  if (!schema || isEmptySchema(schema)) {
    return { ok: true, skipped: true, reason: 'response schema is empty' };
  }

  const ajv = new Ajv({
    allErrors: true,
    strict: false,
    validateFormats: false,
    validateSchema: false,
  });
  const validator = ajv.compile(dereferenceSchema(schema, document) as JsonRecord);
  const ok = validator(options.body);
  return ok
    ? { ok: true }
    : {
        ok: false,
        errors: normalizeAjvErrors(validator.errors),
      };
}
