import { createIssue } from '../errors.js';
import type { CompiledDemoScenarioPackage, ValidationIssue } from '../types.js';

function idSet(records: Array<Record<string, unknown>>, key: string): Set<unknown> {
  return new Set(records.map((record) => record[key]));
}

function pushIssue(
  issues: ValidationIssue[],
  path: string,
  code: string,
  actual: unknown,
  expected: string,
  fixHint: string
): void {
  issues.push(
    createIssue({
      path,
      code,
      severity: 'error',
      actual,
      expected,
      fixHint,
      autoRepairable: false,
    })
  );
}

function graphNodeKeys(graph: unknown): Set<unknown> {
  if (!graph || typeof graph !== 'object') return new Set();
  const nodes = (graph as { nodes?: unknown }).nodes;
  if (!Array.isArray(nodes)) return new Set();

  return new Set(
    nodes.flatMap((node) => {
      if (!node || typeof node !== 'object') return [];
      const record = node as Record<string, unknown>;
      return [record.id, record.label, record.name].filter((value) => value !== undefined);
    })
  );
}

function graphEdges(graph: unknown): Array<Record<string, unknown>> {
  if (!graph || typeof graph !== 'object') return [];
  const edges = (graph as { edges?: unknown; links?: unknown }).edges ?? (graph as { links?: unknown }).links;
  return Array.isArray(edges) ? (edges.filter((edge) => edge && typeof edge === 'object') as Array<Record<string, unknown>>) : [];
}

export function validateRuntimeInvariants(scenarioPackage: CompiledDemoScenarioPackage): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const projects = scenarioPackage.project.projects;
  const versions = scenarioPackage.project.versions;
  const topologies = scenarioPackage.project.topologies;
  const sessions = scenarioPackage.simulation.sessions;
  const projectIds = idSet(projects, 'projectId');
  const versionIds = idSet(versions, 'versionId');
  const sessionIds = idSet(sessions, 'sessionId');

  if (projects.length < 1) {
    pushIssue(issues, 'project.projects', 'project_minimum_records_missing', projects.length, '>= 1', 'Generate at least one visible project.');
  }

  versions.forEach((version, index) => {
    if (!projectIds.has(version.projectId)) {
      pushIssue(
        issues,
        `project.versions[${index}].projectId`,
        'project_version_project_missing',
        version.projectId,
        'projectId from project.projects',
        'Ensure every version references an existing project.'
      );
    }
  });

  projects
    .filter((project) => project.status !== '1')
    .forEach((project, index) => {
      if (!versions.some((version) => version.projectId === project.projectId)) {
        pushIssue(
          issues,
          `project.projects[${index}].projectId`,
          'visible_project_without_version',
          project.projectId,
          'At least one version for each visible project',
          'Generate at least one project version for every visible project.'
        );
      }
    });

  topologies.forEach((topology, index) => {
    if (!projectIds.has(topology.projectId)) {
      pushIssue(
        issues,
        `project.topologies[${index}].projectId`,
        'topology_project_missing',
        topology.projectId,
        'projectId from project.projects',
        'Ensure every topology references an existing project.'
      );
    }

    if (topology.versionId !== undefined && !versionIds.has(topology.versionId)) {
      pushIssue(
        issues,
        `project.topologies[${index}].versionId`,
        'topology_version_missing',
        topology.versionId,
        'versionId from project.versions',
        'Ensure every topology references an existing version.'
      );
    }

    const nodeKeys = graphNodeKeys(topology.graph);
    const edges = graphEdges(topology.graph);
    if (!nodeKeys.size) {
      pushIssue(
        issues,
        `project.topologies[${index}].graph.nodes`,
        'topology_graph_nodes_missing',
        topology.graph,
        'At least one node',
        'Generate topology graph nodes for read-only topology viewing.'
      );
    }

    if (!edges.length) {
      pushIssue(
        issues,
        `project.topologies[${index}].graph.edges`,
        'topology_graph_edges_missing',
        topology.graph,
        'At least one edge',
        'Generate topology graph edges so read-only topology viewing has a connected relationship.'
      );
    }

    edges.forEach((edge, edgeIndex) => {
      if (!nodeKeys.has(edge.source) || !nodeKeys.has(edge.target)) {
        pushIssue(
          issues,
          `project.topologies[${index}].graph.edges[${edgeIndex}]`,
          'topology_graph_edge_endpoint_missing',
          { source: edge.source, target: edge.target },
          'source/target matching a node id, label, or name',
          'Repair topology edges so every endpoint references a graph node.'
        );
      }
    });
  });

  sessions.forEach((session, index) => {
    const version = versions.find((item) => item.versionId === session.versionId);
    if (!projectIds.has(session.projectId) || !version || version.projectId !== session.projectId) {
      pushIssue(
        issues,
        `simulation.sessions[${index}]`,
        'simulation_project_version_missing',
        { projectId: session.projectId, versionId: session.versionId },
        'Existing project/version relationship',
        'Ensure every simulation session references a valid project and version pair.'
      );
    }
  });

  const simulationCollections = [
    ['messages', scenarioPackage.simulation.messages],
    ['bandwidth', scenarioPackage.simulation.bandwidth],
    ['alarms', scenarioPackage.simulation.alarms],
    ['faults', scenarioPackage.simulation.faults],
    ['events', scenarioPackage.simulation.events],
    ['streamFrames', scenarioPackage.simulation.streamFrames],
  ] as const;

  simulationCollections.forEach(([collection, records]) => {
    records.forEach((record, index) => {
      if (!sessionIds.has(record.sessionId)) {
        pushIssue(
          issues,
          `simulation.${collection}[${index}].sessionId`,
          'simulation_record_session_missing',
          record.sessionId,
          'sessionId from simulation.sessions',
          'Ensure every simulation timeline record references an existing session.'
        );
      }
    });
  });

  const hasCompleteReadOnlyChain = projects.some((project) => {
    const version = versions.find((item) => item.projectId === project.projectId);
    if (!version) return false;
    const topology = topologies.find((item) => item.projectId === project.projectId && item.versionId === version.versionId);
    const session = sessions.find((item) => item.projectId === project.projectId && item.versionId === version.versionId);
    return Boolean(topology && session);
  });

  if (!hasCompleteReadOnlyChain) {
    pushIssue(
      issues,
      'project/simulation',
      'readonly_demo_chain_missing',
      'missing complete chain',
      'project + version + topology + simulation session',
      'Generate at least one complete project/version/topology/simulation chain.'
    );
  }

  return issues;
}
