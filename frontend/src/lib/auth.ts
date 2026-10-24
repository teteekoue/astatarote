/**
 * Session storage with a safe in-memory fallback.
 *
 * Some embedded/preview contexts (cross-origin iframes, strict browser
 * settings) block localStorage access entirely. During the open-access
 * testing phase the app must keep working: we fall back to per-page-load
 * memory storage, and the server maps tokenless requests to the shared
 * demo admin anyway (settings.OPEN_ACCESS).
 */
const TOKEN_KEY = "astarote_token";
const USER_KEY = "astarote_user";

const memory = new Map<string, string>();

function storageGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return memory.get(key) ?? null;
  }
}

function storageSet(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    memory.set(key, value);
  }
}

function storageRemove(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    memory.delete(key);
  }
}

export interface UserStats {
  total_time: number;
  levels_completed: number;
  points: number;
  rank: string;
  badges: string[];
  commands_run?: number;
  success_rate?: number;
}

export interface UserPreferences {
  provider_ia: string;
  api_key: string;
  theme: string;
  font_size: number;
}

export interface UserType {
  id: number;
  username: string;
  email: string;
  created_at: string;
  preferences: UserPreferences;
  stats: UserStats;
}

export function getToken(): string | null {
  return storageGet(TOKEN_KEY);
}

export function setToken(token: string): void {
  storageSet(TOKEN_KEY, token);
}

export function setStoredUser(user: UserType): void {
  storageSet(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): UserType | null {
  const raw = storageGet(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserType;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  storageRemove(TOKEN_KEY);
  storageRemove(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}
