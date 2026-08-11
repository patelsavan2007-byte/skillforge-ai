import type { ReactNode } from "react";
import { Sparkles } from "lucide-react";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <main className="hero-glow flex min-h-screen items-center justify-center px-5 py-12">
      <div className="w-full max-w-[460px]">
        <header className="text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            <Sparkles className="size-3.5 text-primary" />
            AI Career Mentor
          </span>
          <h1 className="mt-6 text-3xl font-bold sm:text-4xl">
            <span className="text-gradient">SkillForge AI</span>
          </h1>
          <h2 className="mt-6 font-display text-2xl text-foreground sm:text-3xl">{title}</h2>
          <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">{subtitle}</p>
        </header>

        <section className="panel mt-8 p-6 sm:p-8">{children}</section>

        <p className="mt-6 text-center text-sm text-muted-foreground">{footer}</p>
      </div>
    </main>
  );
}

export function AuthField({
  id,
  label,
  error,
  children,
}: {
  id: string;
  label: string;
  error?: string | null | undefined;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label
        htmlFor={id}
        className="text-xs font-medium tracking-wide text-muted-foreground uppercase"
      >
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-xs text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function AuthDivider() {
  return (
    <div className="my-6 flex items-center gap-4">
      <span className="h-px flex-1 bg-border" />
      <span className="text-xs font-medium tracking-widest text-muted-foreground">OR</span>
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

export function GoogleButton({
  onClick,
  disabled,
  loading,
}: {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex w-full items-center justify-center gap-3 rounded-xl border border-border bg-surface-2 px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-surface-2/70 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:opacity-60"
    >
      <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
        <path
          fill="#EA4335"
          d="M12 10.2v3.9h5.5a4.7 4.7 0 0 1-2 3.1l3.2 2.5c1.9-1.7 3-4.3 3-7.4 0-.7-.1-1.4-.2-2H12z"
        />
        <path
          fill="#34A853"
          d="M6.6 14.3 5.9 14l-2.3 1.8A9 9 0 0 0 12 21c2.4 0 4.5-.8 6-2.2l-3.2-2.5c-.8.6-1.9.9-2.8.9a5 5 0 0 1-4.4-2.9z"
        />
        <path
          fill="#FBBC05"
          d="M3.6 8.2A9 9 0 0 0 3.6 15.8L6.6 13.5a5.4 5.4 0 0 1 0-3z"
        />
        <path
          fill="#4285F4"
          d="M12 6.6c1.3 0 2.5.5 3.5 1.4l2.6-2.6A9 9 0 0 0 3.6 8.2l3 2.3A5 5 0 0 1 12 6.6z"
        />
      </svg>
      {loading ? "Connecting…" : "Continue with Google"}
    </button>
  );
}
