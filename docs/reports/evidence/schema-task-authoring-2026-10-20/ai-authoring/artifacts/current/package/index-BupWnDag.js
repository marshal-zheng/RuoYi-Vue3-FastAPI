"use strict";
function record(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function safeJson(value, path = "$", definition = true, depth = 0) {
  if (depth > 40)
    throw new Error(`JSON exceeds supported nesting limit at ${path}`);
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number" && Number.isFinite(value)) return;
  if (typeof value === "string") {
    if (definition && (/^\s*(\$(FN|FNX|EXEC|GLOBAL):|\[\[FORM-CREATE-PREFIX-|function\s*\()|\{\{/.test(
      value
    ) || /^\s*function\s+/.test(value)))
      throw new Error(`Executable definition text at ${path}`);
    return;
  }
  if (Array.isArray(value))
    return value.forEach(
      (item, i) => safeJson(item, `${path}[${i}]`, definition, depth + 1)
    );
  if (record(value) && Object.getPrototypeOf(value) === Object.prototype) {
    for (const [key, item] of Object.entries(value)) {
      if (["__proto__", "prototype", "constructor"].includes(key))
        throw new Error(`Unsafe key at ${path}`);
      safeJson(item, `${path}.${key}`, definition, depth + 1);
    }
    return;
  }
  throw new Error(`Non-JSON definition at ${path}`);
}
function copy(value) {
  safeJson(value, "$", false);
  return JSON.parse(JSON.stringify(value));
}
function equal(left, right) {
  if (left === right) return true;
  if (Array.isArray(left) && Array.isArray(right))
    return left.length === right.length && left.every((item, index) => equal(item, right[index]));
  if (record(left) && record(right))
    return Object.keys(left).length === Object.keys(right).length && Object.keys(left).every(
      (key) => Object.hasOwn(right, key) && equal(left[key], right[key])
    );
  return false;
}
exports.copy = copy;
exports.equal = equal;
exports.record = record;
exports.safeJson = safeJson;
