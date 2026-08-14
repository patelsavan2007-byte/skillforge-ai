import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";
import {
  AuthDivider,
  AuthField,
  AuthLayout,
  GoogleButton,
} from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";
import {
  requestPasswordReset,
  signIn,
  signInWithGoogle,
  useAuth,
  validateEmail,
} from "@/lib/auth-store";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign In — SkillForge AI" },
      {
        name: "description",
        content:
          "Sign in to SkillForge AI and continue your personalized journey toward becoming job-ready.",
      },
      { property: "og:title", content: "Sign In — SkillForge AI" },
      {
        property: "og:description",
        content: "Continue your journey toward becoming job-ready with SkillForge AI.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { user, ready } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string | undefined; password?: string | undefined }>({});
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (ready && user) navigate({ to: "/", replace: true });

    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const error = params.get("error");
      if (error) {
        if (error === "invalid_state") {
          toast.error("Google login session expired or state mismatch. Please try again.");
        } else if (error === "auth_failed") {
          toast.error("Google authentication failed. Please check your credentials or try again.");
        } else if (error === "access_denied") {
          toast.error("Google sign-in was cancelled.");
        } else {
          toast.error(`Google authentication error: ${error}`);
        }
        // Clean URL params
        window.history.replaceState({}, "", "/login");
      }
    }
  }, [ready, user, navigate]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next = {
      email: validateEmail(email) ?? undefined,
      password: password ? undefined : "Password is required.",
    };
    setErrors(next);
    if (next.email || next.password) return;

    setSubmitting(true);
    try {
      const u = await signIn(email, password);
      toast.success(`Welcome back, ${u.name.split(" ")[0]}!`);
      navigate({ to: "/", replace: true });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not sign you in.");
    } finally {
      setSubmitting(false);
    }
  }

  function onGoogle() {
    setGoogleLoading(true);
    signInWithGoogle();
  }

  async function onForgot() {
    const emailError = validateEmail(email);
    if (emailError) {
      setErrors((p) => ({ ...p, email: "Enter your email first, then tap reset." }));
      return;
    }
    try {
      await requestPasswordReset(email);
      toast.success("Password reset link sent to your inbox.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not send reset link.");
    }
  }

  const busy = submitting || googleLoading;

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Continue your journey toward becoming job-ready."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="space-y-5">
        <AuthField id="email" label="Email address" error={errors.email}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? "email-error" : undefined}
            onChange={(e) => setEmail(e.target.value)}
            className="h-11"
          />
        </AuthField>

        <AuthField id="password" label="Password" error={errors.password}>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? "password-error" : undefined}
            onChange={(e) => setPassword(e.target.value)}
          />
        </AuthField>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={onForgot}
            className="text-xs font-medium text-primary transition-opacity hover:opacity-80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          disabled={busy}
          className="bg-gradient-accent glow inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:translate-y-0 disabled:opacity-60"
        >
          {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {submitting ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <AuthDivider />
      <GoogleButton onClick={onGoogle} disabled={busy} loading={googleLoading} />
    </AuthLayout>
  );
}
