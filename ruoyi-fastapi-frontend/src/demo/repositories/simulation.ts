import type { DemoOfflineDb } from '@/demo/db';
import type {
  DemoSimulationAlarm,
  DemoSimulationBandwidth,
  DemoSimulationEvent,
  DemoSimulationFault,
  DemoSimulationFrame,
  DemoSimulationMessage,
  DemoSimulationSession,
} from '@/demo/scenarios';
import type { UpdateSpec } from 'dexie';

export class SimulationRepository {
  constructor(private readonly db: DemoOfflineDb) {}

  listSessions(): Promise<DemoSimulationSession[]> {
    return this.db.simulationSessions.toArray();
  }

  getSession(sessionId: string): Promise<DemoSimulationSession | undefined> {
    return this.db.simulationSessions.get(sessionId);
  }

  async findSessionByProjectVersion(
    projectId: number,
    versionId: number
  ): Promise<DemoSimulationSession | undefined> {
    const sessions = await this.db.simulationSessions
      .where('projectId')
      .equals(projectId)
      .toArray();

    return sessions
      .filter((session) => session.versionId === versionId)
      .sort(
        (left, right) =>
          Date.parse(String(right.updateTime ?? '')) - Date.parse(String(left.updateTime ?? ''))
      )[0];
  }

  saveSession(session: DemoSimulationSession): Promise<string> {
    return this.db.simulationSessions.put(session);
  }

  async updateSession(
    sessionId: string,
    patch: Partial<DemoSimulationSession>
  ): Promise<DemoSimulationSession> {
    await this.db.simulationSessions.update(sessionId, patch as UpdateSpec<DemoSimulationSession>);
    const updated = await this.getSession(sessionId);

    if (!updated) {
      throw new Error(`Demo simulation session "${sessionId}" was not found after update.`);
    }

    return updated;
  }

  listMessages(sessionId: string): Promise<DemoSimulationMessage[]> {
    return this.db.simulationMessages.where('sessionId').equals(sessionId).toArray();
  }

  listBandwidth(sessionId: string): Promise<DemoSimulationBandwidth[]> {
    return this.db.simulationBandwidth.where('sessionId').equals(sessionId).toArray();
  }

  listAlarms(sessionId: string): Promise<DemoSimulationAlarm[]> {
    return this.db.simulationAlarms.where('sessionId').equals(sessionId).toArray();
  }

  listFaults(sessionId: string): Promise<DemoSimulationFault[]> {
    return this.db.simulationFaults.where('sessionId').equals(sessionId).toArray();
  }

  listEvents(sessionId: string): Promise<DemoSimulationEvent[]> {
    return this.db.simulationEvents.where('sessionId').equals(sessionId).toArray();
  }

  listFrames(sessionId: string): Promise<DemoSimulationFrame[]> {
    return this.db.simulationFrames.where('sessionId').equals(sessionId).sortBy('order');
  }
}
