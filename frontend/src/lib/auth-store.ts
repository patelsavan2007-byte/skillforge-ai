import { useEffect, useState } from "react";

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  profile_picture?: string;
  provider?: "password" | "google";
  sessionId?: string;
};

const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";
const KEY = "skillforge-auth";

const listeners = new Set<() => void>();

function generateSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function emit() {
  listeners.forEach((l) => l());
}

export function getSession(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function getAuthHeaders(): Record<string, string> {
  const session = getSession();
  if (session?.id) {
    return { "X-User-ID": session.id };
  }
  return {};
}

function setSession(user: AuthUser | null) {
  if (user) {
    localStorage.setItem(KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(KEY);
  }
  emit();
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  try {
    const local = getSession();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (local?.id) {
      headers["X-User-ID"] = local.id;
    }

    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      method: "GET",
      headers,
      credentials: "include",
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        // Keep existing stable sessionId if same user, otherwise generate a new session ID
        const stableSessionId =
          local?.id === data.user.id && local?.sessionId
            ? local.sessionId
            : generateSessionId();

        const user: AuthUser = {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          profile_picture: data.user.profile_picture || "",
          provider: data.user.provider || "google",
          sessionId: stableSessionId,
        };
        setSession(user);
        return user;
      } else {
        // Unauthenticated according to backend
        setSession(null);
        return null;
      }
    }
  } catch (err) {
    console.warn("Backend auth check error:", err);
  }
  return getSession();
}

export async function signIn(email: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.success) {
    throw new Error(data.detail || data.message || "Failed to sign in. Please check your credentials.");
  }

  const user: AuthUser = {
    id: data.user.id,
    name: data.user.name,
    email: data.user.email,
    profile_picture: data.user.profile_picture || "",
    provider: data.user.provider || "password",
    sessionId: generateSessionId(),
  };
  setSession(user);
  return user;
}

export async function signUp(
  name: string,
  email: string,
  password: string,
): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ name, email, password }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.success) {
    throw new Error(data.detail || data.message || "Failed to create account.");
  }

  const user: AuthUser = {
    id: data.user.id,
    name: data.user.name,
    email: data.user.email,
    profile_picture: data.user.profile_picture || "",
    provider: data.user.provider || "password",
    sessionId: generateSessionId(),
  };
  setSession(user);
  return user;
}

export function signInWithGoogle(): void {
  window.location.href = `${API_BASE_URL}/api/auth/google/login`;
}

export async function requestPasswordReset(email: string): Promise<void> {
  // In a full implementation this sends a reset email
  await new Promise((r) => setTimeout(r, 600));
}

export async function signOut(): Promise<void> {
  try {
    const local = getSession();
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      headers: local?.id ? { "X-User-ID": local.id } : {},
      credentials: "include",
    });
  } catch (err) {
    console.warn("Backend logout error:", err);
  }
  // Clear any cached profile data from browser storage and reset session
  if (typeof window !== "undefined") {
    try {
      sessionStorage.clear();
    } catch {
      // ignore
    }
  }
  setSession(null);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("skillforge-profile-update"));
  }
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(() => getSession());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    async function checkAuth() {
      const current = await fetchCurrentUser();
      if (active) {
        setUser(current);
        setReady(true);
      }
    }

    checkAuth();

    const sync = () => {
      if (active) setUser(getSession());
    };

    listeners.add(sync);
    window.addEventListener("storage", sync);

    return () => {
      active = false;
      listeners.delete(sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return { user, ready, refreshUser: fetchCurrentUser };
}

export function validateEmail(email: string) {
  if (!email.trim()) return "Email address is required.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return "Enter a valid email address.";
  return null;
}

export function validatePassword(password: string) {
  if (!password) return "Password is required.";
  if (password.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password))
    return "Use at least one letter and one number.";
  return null;
}


