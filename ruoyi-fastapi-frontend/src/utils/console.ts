// Utilities
import { warn } from 'vue';

export function consoleWarn(message: string): void {
  warn(`System: ${message}`);
}

export function consoleError(message: string): void {
  warn(`System error: ${message}`);
}
