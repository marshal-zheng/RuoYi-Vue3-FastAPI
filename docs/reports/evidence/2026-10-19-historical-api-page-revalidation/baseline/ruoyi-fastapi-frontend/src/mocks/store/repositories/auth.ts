import type { MockAccount } from '../../data';

export interface MockAuthSession {
  token: string;
  username: string;
  expiresAt: string;
}

export interface MockAuthRepository {
  findAccountByUsername(username: string): Promise<MockAccount | undefined>;
  findSessionByToken(token: string): Promise<MockAuthSession | undefined>;
  createSession(username: string): Promise<MockAuthSession>;
  deleteSession(token: string): Promise<void>;
}
