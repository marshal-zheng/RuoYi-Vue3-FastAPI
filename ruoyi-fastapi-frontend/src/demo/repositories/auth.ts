import type { DemoOfflineDb, DemoAuthSession, DemoCsrfToken, DemoWsTicket } from '@/demo/db';
import type { DemoAccount, DemoRole } from '@/demo/scenarios';

export class AuthRepository {
  constructor(private readonly db: DemoOfflineDb) {}

  getAccount(username: string): Promise<DemoAccount | undefined> {
    return this.db.accounts.get(username);
  }

  listAccounts(): Promise<DemoAccount[]> {
    return this.db.accounts.toArray();
  }

  listRoles(): Promise<DemoRole[]> {
    return this.db.roles.toArray();
  }

  saveSession(session: DemoAuthSession): Promise<string> {
    return this.db.authSessions.put(session);
  }

  getSession(token: string): Promise<DemoAuthSession | undefined> {
    return this.db.authSessions.get(token);
  }

  listSessions(): Promise<DemoAuthSession[]> {
    return this.db.authSessions.toArray();
  }

  removeSession(token: string): Promise<void> {
    return this.db.authSessions.delete(token);
  }

  clearSessions(): Promise<void> {
    return this.db.authSessions.clear();
  }

  saveCsrfToken(token: DemoCsrfToken): Promise<string> {
    return this.db.csrfTokens.put(token);
  }

  getCsrfToken(token: string): Promise<DemoCsrfToken | undefined> {
    return this.db.csrfTokens.get(token);
  }

  getCsrfTokenBySession(sessionToken: string): Promise<DemoCsrfToken | undefined> {
    return this.db.csrfTokens.where('sessionToken').equals(sessionToken).first();
  }

  async removeCsrfTokensBySession(sessionToken: string): Promise<void> {
    await this.db.csrfTokens.where('sessionToken').equals(sessionToken).delete();
  }

  clearCsrfTokens(): Promise<void> {
    return this.db.csrfTokens.clear();
  }

  saveWsTicket(ticket: DemoWsTicket): Promise<string> {
    return this.db.wsTickets.put(ticket);
  }

  getWsTicket(ticket: string): Promise<DemoWsTicket | undefined> {
    return this.db.wsTickets.get(ticket);
  }

  async markWsTicketUsed(ticket: string): Promise<void> {
    await this.db.wsTickets.update(ticket, {
      used: true,
    });
  }
}
