#!/usr/bin/env node

import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import http from "node:http";
import net from "node:net";
import { setTimeout as delay } from "node:timers/promises";

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 4173;
const DEFAULT_BASE_URL = `http://${DEFAULT_HOST}:${DEFAULT_PORT}`;
const DIST_INDEX = new URL("../dist-demo-offline/index.html", import.meta.url);
let activePreviewProcess;

function printUsage() {
  console.log(`Usage: yarn e2e:demo-offline [options] [playwright options]

Options:
  --skip-build              Reuse an existing dist-demo-offline build.
  --base-url <url>          Reuse an existing static preview service.
  --port <port>             Preview port when this runner starts Vite preview.
  --config <path>           Playwright config file. Defaults to playwright.demo-offline.config.ts.
  --suite-name <name>       Suite name used in runner logs.
  --headed                  Forwarded to Playwright.
  --debug                   Forwarded to Playwright.
  --grep <pattern>          Forwarded to Playwright.
`);
}

function parseArgs(argv) {
  const options = {
    skipBuild: false,
    baseUrl: "",
    port: DEFAULT_PORT,
    config: "playwright.demo-offline.config.ts",
    suiteName: "core",
    playwrightArgs: [],
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--help" || arg === "-h") {
      printUsage();
      process.exit(0);
    }

    if (arg === "--skip-build") {
      options.skipBuild = true;
      continue;
    }

    if (arg === "--base-url") {
      options.baseUrl = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (arg.startsWith("--base-url=")) {
      options.baseUrl = arg.slice("--base-url=".length);
      continue;
    }

    if (arg === "--port") {
      options.port = Number(argv[index + 1] ?? DEFAULT_PORT);
      index += 1;
      continue;
    }

    if (arg.startsWith("--port=")) {
      options.port = Number(arg.slice("--port=".length));
      continue;
    }

    if (arg === "--config") {
      options.config = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (arg.startsWith("--config=")) {
      options.config = arg.slice("--config=".length);
      continue;
    }

    if (arg === "--suite-name") {
      options.suiteName = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (arg.startsWith("--suite-name=")) {
      options.suiteName = arg.slice("--suite-name=".length);
      continue;
    }

    options.playwrightArgs.push(arg);
  }

  if (
    !Number.isInteger(options.port) ||
    options.port <= 0 ||
    options.port > 65535
  ) {
    throw new Error(`Invalid --port value. Received: ${options.port}`);
  }

  if (options.baseUrl) {
    try {
      new URL(options.baseUrl);
    } catch {
      throw new Error(`Invalid --base-url value. Received: ${options.baseUrl}`);
    }
  }

  if (!options.config) {
    throw new Error("--config requires a Playwright config path");
  }

  if (!options.suiteName) {
    throw new Error("--suite-name requires a non-empty name");
  }

  return options;
}

function spawnCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: options.stdio ?? "inherit",
      env: {
        ...process.env,
        ...(options.env ?? {}),
      },
      shell: process.platform === "win32",
    });

    child.on("error", reject);
    child.on("exit", (code, signal) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(
        new Error(
          `${command} ${args.join(" ")} failed with ${signal ?? `exit code ${code}`}`,
        ),
      );
    });
  });
}

function requestUrl(url) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (response) => {
      response.resume();
      resolve(response.statusCode ?? 0);
    });
    request.on("error", reject);
    request.setTimeout(2000, () => {
      request.destroy(new Error("HTTP preview request timed out"));
    });
  });
}

async function waitForHttpReady(url, previewProcess) {
  const deadline = Date.now() + 30_000;
  let lastError;

  while (Date.now() < deadline) {
    if (previewProcess?.exitCode !== null) {
      throw new Error(
        `Static preview exited before it became ready. Check whether the port is already in use.`,
      );
    }

    try {
      const status = await requestUrl(url);
      if (status >= 200 && status < 500) {
        return;
      }
      lastError = new Error(`HTTP ${status}`);
    } catch (error) {
      lastError = error;
    }
    await delay(500);
  }

  throw new Error(
    `Static preview did not become ready at ${url}. Last error: ${
      lastError instanceof Error ? lastError.message : String(lastError)
    }`,
  );
}

async function assertDistExists() {
  try {
    await fs.access(DIST_INDEX);
  } catch {
    throw new Error(
      "dist-demo-offline/index.html is missing. Run yarn build:demo-offline or remove --skip-build.",
    );
  }
}

function assertPreviewPortAvailable(host, port) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", (error) => {
      reject(
        new Error(
          `Preview port ${host}:${port} is already in use. Stop the existing service or pass --port ${port + 1}. Original error: ${error.message}`,
        ),
      );
    });
    server.once("listening", () => {
      server.close(() => resolve());
    });
    server.listen(port, host);
  });
}

function startPreview(port) {
  const child = spawn(
    "yarn",
    [
      "vite",
      "preview",
      "--mode",
      "demo-offline",
      "--host",
      DEFAULT_HOST,
      "--port",
      String(port),
      "--strictPort",
    ],
    {
      stdio: "inherit",
      shell: process.platform === "win32",
    },
  );
  activePreviewProcess = child;
  return child;
}

async function stopPreview(child) {
  if (!child || child.exitCode !== null) {
    return;
  }
  child.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    delay(5000).then(() => {
      if (child.exitCode === null) {
        child.kill("SIGKILL");
      }
    }),
  ]);
  if (activePreviewProcess === child) {
    activePreviewProcess = undefined;
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const baseUrl = options.baseUrl || `http://${DEFAULT_HOST}:${options.port}`;
  let previewProcess;

  try {
    if (!options.skipBuild) {
      console.log(
        `[demo-offline-e2e:${options.suiteName}] Building dist-demo-offline with yarn build:demo-offline...`,
      );
      await spawnCommand("yarn", ["build:demo-offline"]);
    }

    await assertDistExists();

    if (options.baseUrl) {
      console.log(
        `[demo-offline-e2e:${options.suiteName}] Reusing static preview at ${baseUrl}...`,
      );
    } else {
      console.log(
        `[demo-offline-e2e:${options.suiteName}] Starting static preview at ${baseUrl}...`,
      );
      await assertPreviewPortAvailable(DEFAULT_HOST, options.port);
      previewProcess = startPreview(options.port);
    }

    await waitForHttpReady(baseUrl, previewProcess);

    console.log(
      `[demo-offline-e2e:${options.suiteName}] Running Playwright Chromium suite...`,
    );
    await spawnCommand(
      "yarn",
      [
        "playwright",
        "test",
        `--config=${options.config}`,
        ...options.playwrightArgs,
      ],
      {
        env: {
          DEMO_OFFLINE_E2E_BASE_URL: baseUrl,
        },
      },
    );
  } catch (error) {
    console.error("[demo-offline-e2e] Failed.");
    console.error(error instanceof Error ? error.message : error);
    console.error(
      [
        "Fix hints:",
        "- Install Chromium with: yarn playwright install chromium",
        "- Rebuild the static bundle with: yarn build:demo-offline",
        `- Free the preview port or choose another one with: yarn e2e:demo-offline --port ${DEFAULT_PORT + 1}`,
        "- Ensure the preview URL serves dist-demo-offline over HTTP, not file:// or yarn dev.",
      ].join("\n"),
    );
    process.exitCode = 1;
  } finally {
    await stopPreview(previewProcess);
  }
}

function handleSignal(signal) {
  if (activePreviewProcess && activePreviewProcess.exitCode === null) {
    activePreviewProcess.kill("SIGTERM");
  }
  process.exit(signal === "SIGINT" ? 130 : 143);
}

process.once("SIGINT", () => handleSignal("SIGINT"));
process.once("SIGTERM", () => handleSignal("SIGTERM"));

main();
