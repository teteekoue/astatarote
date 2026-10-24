const TOKEN_KEY = "astarote_token";
const USER_KEY = "astarote_user";

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
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function setStoredUser(user: UserType): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): UserType | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserType) : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}
