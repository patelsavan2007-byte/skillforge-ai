import { useEffect, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2, LogOut } from "lucide-react";

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

  if (!user) return null;

  return (
    <div className="mx-auto flex max-w-5xl items-center justify-end gap-3 px-5 pt-5">
      <span className="hidden text-xs text-muted-foreground sm:inline">{user.email}</span>
      <button
        type="button"
        onClick={() => {
          signOut();
          navigate({ to: "/login", replace: true });
        }}
        className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        <LogOut className="size-3.5" />
        Logout
      </button>
    </div>
  );
}
