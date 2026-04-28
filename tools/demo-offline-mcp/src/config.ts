export interface ServerConfig {
  repoRoot?: string;
}

const REPO_ROOT_FLAG = '--repo-root';

export function parseServerConfig(argv: string[]): ServerConfig {
  const repoRootIndex = argv.indexOf(REPO_ROOT_FLAG);

  if (repoRootIndex === -1) {
    return {};
  }

  const repoRoot = argv[repoRootIndex + 1];

  if (!repoRoot) {
    throw new Error(`${REPO_ROOT_FLAG} requires a repository path.`);
  }

  return { repoRoot };
}

export function assertNoProviderApiKeyRequirement(): true {
  return true;
}
