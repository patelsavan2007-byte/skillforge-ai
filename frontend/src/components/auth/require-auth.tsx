import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2, LogOut, Moon, Sun } from "lucide-react";
import { Link } from "@tanstack/react-router";

import { signOut, useAuth } from "@/lib/auth-store";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (ready && !user) navigate({ to: "/login", replace: true });
  }, [ready, user, navigate]);

  if (!ready || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <>
      <AuthBar />
      {children}
    </>
  );
}

function AuthBar() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [light, setLight] = useState(() => typeof window !== "undefined" && localStorage.getItem("skillforge-theme") === "light");

  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
  }, [light]);

  function toggleTheme() {
    const next = !light;
    setLight(next);
    document.documentElement.classList.toggle("light", next);
    localStorage.setItem("skillforge-theme", next ? "light" : "dark");
  }

  if (!user) return null;

  return (
    <header className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-5 pt-5">
      <Link to="/" className="font-display text-lg font-bold tracking-tight text-foreground">
        Skill<span className="text-primary">Forge</span> AI
      </Link>
      <nav className="flex items-center gap-2 sm:gap-3">
        <Link to="/" className="hidden rounded-full px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface hover:text-foreground sm:inline">New analysis</Link>
        <Link to="/analysis" className="hidden rounded-full px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface hover:text-foreground sm:inline">Analysis</Link>
        <button type="button" aria-label="Toggle light and dark theme" onClick={toggleTheme} className="grid size-8 place-items-center rounded-full border border-border bg-surface text-muted-foreground transition-colors hover:text-foreground">
          {light ? <Moon className="size-3.5" /> : <Sun className="size-3.5" />}
        </button>
      <span className="hidden text-xs text-muted-foreground sm:inline">{user.email}</span>
      <button
        type="button"
        onClick={async () => {
          await signOut();
          navigate({ to: "/login", replace: true });
        }}
        className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        <LogOut className="size-3.5" />
        Logout
      </button>
      </nav>
    </header>
  );
}
