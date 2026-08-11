import { useEffect, useState } from "react";

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  profile_picture?: string;
  provider?: "password" | "google";
};

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const KEY = "skillforge-auth";
const USERS_KEY = "skillforge-auth-users";

type StoredUser = AuthUser & { password?: string };

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function readUsers(): StoredUser[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) ?? "[]") as StoredUser[];
  } catch {
    return [];
  }
}

function writeUsers(users: StoredUser[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
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

function setSession(user: AuthUser | null) {
  if (user) {
    localStorage.setItem(KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(KEY);
  }
  emit();
}

function delay(ms = 700) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        const user: AuthUser = {
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          profile_picture: data.user.profile_picture || "",
          provider: "google",
        };
        setSession(user);
        return user;
      }
    }
  } catch (err) {
    console.warn("Backend auth check error:", err);
  }
  return getSession();
}

export async function signIn(email: string, password: string): Promise<AuthUser> {
  await delay();
  const user = readUsers().find((u) => u.email.toLowerCase() === email.toLowerCase());
  if (!user) throw new Error("No account found with that email address.");
  if (user.provider === "google" && !user.password) {
    throw new Error("This account was created with Google. Continue with Google instead.");
  }
  if (user.password !== password) throw new Error("Incorrect password. Please try again.");
  const { password: _pw, ...safe } = user;
  setSession(safe);
  return safe;
}

export async function signUp(
  name: string,
  email: string,
  password: string,
): Promise<AuthUser> {
  await delay();
  const users = readUsers();
  if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    throw new Error("An account with that email already exists.");
  }
  const user: StoredUser = {
    id: crypto.randomUUID(),
    name,
    email,
    provider: "password",
    password,
  };
  writeUsers([...users, user]);
  const { password: _pw, ...safe } = user;
  setSession(safe);
  return safe;
}

export function signInWithGoogle(): void {
  window.location.href = `${API_BASE_URL}/api/auth/google/login`;
}

export async function requestPasswordReset(email: string): Promise<void> {
  await delay();
  if (!readUsers().some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    throw new Error("No account found with that email address.");
  }
}

export async function signOut(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (err) {
    console.warn("Backend logout error:", err);
  }
  setSession(null);
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

