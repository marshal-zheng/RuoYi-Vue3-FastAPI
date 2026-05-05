#!/usr/bin/env node
import {
  buildMockOverlayReport,
  formatMarkdown,
  formatSummary,
  writeReportFile,
} from "./mock-overlays-core.mjs";

function parseArgs(argv) {
  const options = {
    strict: false,
    format: "summary",
    writeReport: undefined,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--strict") {
      options.strict = true;
    } else if (arg.startsWith("--format=")) {
      options.format = arg.slice("--format=".length);
    } else if (arg === "--write-report") {
      options.writeReport = argv[index + 1];
      index += 1;
    } else if (arg.startsWith("--write-report=")) {
      options.writeReport = arg.slice("--write-report=".length);
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!["summary", "json", "markdown"].includes(options.format)) {
    throw new Error(
      `Unsupported --format=${options.format}; expected summary, json, or markdown`,
    );
  }
  if (options.writeReport !== undefined && !options.writeReport) {
    throw new Error("--write-report requires a path");
  }

  return options;
}

function help() {
  return "Usage: node scripts/check-mock-overlays.mjs [--strict] [--format=summary|json|markdown] [--write-report <path>]\n";
}

function render(report, format) {
  if (format === "json") {
    return `${JSON.stringify(report, null, 2)}\n`;
  }
  if (format === "markdown") {
    return formatMarkdown(report);
  }
  return formatSummary(report);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(help());
    process.exit(0);
  }

  const report = buildMockOverlayReport({ cwd: process.cwd() });
  const output = render(report, options.format);
  process.stdout.write(output);

  if (options.writeReport) {
    writeReportFile(options.writeReport, output);
  }

  if (options.strict && report.failures.length > 0) {
    process.exit(1);
  }
} catch (error) {
  process.stderr.write(
    `${error instanceof Error ? error.message : String(error)}\n`,
  );
  process.exit(2);
}
