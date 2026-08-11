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
  signInWithGoogle,
  signUp,
  useAuth,
  validateEmail,
  validatePassword,
} from "@/lib/auth-store";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Create Your Account — SkillForge AI" },
      {
        name: "description",
        content:
          "Create a free SkillForge AI account and start building the skills you need for your dream career.",
      },
      { property: "og:title", content: "Create Your Account — SkillForge AI" },
      {
        property: "og:description",
        content: "Start building the skills you need for your dream career.",
      },
    ],
  }),
  component: SignupPage,
});

type Errors = Partial<Record<"name" | "email" | "password" | "confirm", string>>;

function SignupPage() {
  const navigate = useNavigate();
  const { user, ready } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (ready && user) navigate({ to: "/", replace: true });
  }, [ready, user, navigate]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next: Errors = {
      name: name.trim().length < 2 ? "Please enter your full name." : undefined,
      email: validateEmail(email) ?? undefined,
      password: validatePassword(password) ?? undefined,
      confirm: confirm !== password ? "Passwords do not match." : undefined,
    };
    setErrors(next);
    if (Object.values(next).some(Boolean)) return;

    setSubmitting(true);
    try {
      await signUp(name.trim(), email, password);
      toast.success("Account created — welcome to SkillForge AI!");
      navigate({ to: "/", replace: true });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onGoogle() {
    setGoogleLoading(true);
    try {
      await signInWithGoogle();
      toast.success("Signed in with Google.");
      navigate({ to: "/", replace: true });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Google sign-in failed.");
    } finally {
      setGoogleLoading(false);
    }
  }

  const busy = submitting || googleLoading;

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start building the skills you need for your dream career."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="space-y-5">
        <AuthField id="name" label="Full name" error={errors.name}>
          <Input
            id="name"
            autoComplete="name"
            placeholder="Your full name"
            value={name}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? "name-error" : undefined}
            onChange={(e) => setName(e.target.value)}
            className="h-11"
          />
        </AuthField>

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
            autoComplete="new-password"
            placeholder="Create a password"
            value={password}
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? "password-error" : undefined}
            onChange={(e) => setPassword(e.target.value)}
          />
        </AuthField>

        <AuthField id="confirm" label="Confirm password" error={errors.confirm}>
          <PasswordInput
            id="confirm"
            autoComplete="new-password"
            placeholder="Confirm your password"
            value={confirm}
            aria-invalid={!!errors.confirm}
            aria-describedby={errors.confirm ? "confirm-error" : undefined}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </AuthField>

        <button
          type="submit"
          disabled={busy}
          className="bg-gradient-accent glow inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:translate-y-0 disabled:opacity-60"
        >
          {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {submitting ? "Creating account…" : "Create Account"}
        </button>
      </form>

      <AuthDivider />
      <GoogleButton onClick={onGoogle} disabled={busy} loading={googleLoading} />
    </AuthLayout>
  );
}
