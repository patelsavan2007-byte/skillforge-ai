import { useEffect, useState } from "react";

/**
 * Frontend-only auth session layer.
 *
 * There is no backend in this project yet. Every function below is the single
 * place to swap in real API calls (FastAPI) later — the UI never talks to
 * storage directly.
 */

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  provider: "password" | "google";
};

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

function setSession(user: AuthUser) {
  localStorage.setItem(KEY, JSON.stringify(user));
  emit();
}

function delay(ms = 700) {
  return new Promise((r) => setTimeout(r, ms));
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

export async function signInWithGoogle(): Promise<AuthUser> {
  await delay(900);
  const email = "student@gmail.com";
  const users = readUsers();
  let user = users.find((u) => u.email === email);
  if (!user) {
    user = {
      id: crypto.randomUUID(),
      name: "Google Student",
      email,
      provider: "google",
    };
    writeUsers([...users, user]);
  }
  const { password: _pw, ...safe } = user;
  setSession(safe);
  return safe;
}

export async function requestPasswordReset(email: string): Promise<void> {
  await delay();
  if (!readUsers().some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    throw new Error("No account found with that email address.");
  }
}

export function signOut() {
  localStorage.removeItem(KEY);
  emit();
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const sync = () => setUser(getSession());
    sync();
    setReady(true);
    listeners.add(sync);
    window.addEventListener("storage", sync);
    return () => {
      listeners.delete(sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return { user, ready };
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
