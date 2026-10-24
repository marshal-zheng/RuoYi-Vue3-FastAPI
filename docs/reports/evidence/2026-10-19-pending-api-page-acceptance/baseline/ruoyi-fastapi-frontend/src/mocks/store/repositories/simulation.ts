import type {
  MockSimulationEvent,
  MockSimulationFrame,
  MockSimulationMessage,
  MockSimulationSession,
} from '../../data';

export interface MockSimulationReadRepository {
  listSessions(): Promise<MockSimulationSession[]>;
  getSession(sessionId: string): Promise<MockSimulationSession | undefined>;
  listFrames(sessionId: string): Promise<MockSimulationFrame[]>;
  listMessages(sessionId: string): Promise<MockSimulationMessage[]>;
  listEvents(sessionId: string): Promise<MockSimulationEvent[]>;
}
