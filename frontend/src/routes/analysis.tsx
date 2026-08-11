import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FolderGit2,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  extractedSkills,
  portfolioFeedback,
  portfolioProjects,
  profileSummary,
  readiness,
  skillGap,
} from "@/lib/mock-data";
import { useProfile } from "@/lib/profile-store";

import { RequireAuth } from "@/components/auth/require-auth";

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "Your Career Analysis — SkillForge AI" },
      {
        name: "description",
        content:
          "AI profile analysis: career readiness score, extracted skills, portfolio review and skill gaps.",
      },
      { property: "og:title", content: "Your Career Analysis — SkillForge AI" },
      {
        property: "og:description",
        content: "Career readiness score, extracted skills and detected skill gaps.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <AnalysisPage />
    </RequireAuth>
  ),
});

function AnalysisPage() {
  const profile = useProfile();
  const role = profile?.role ?? "AI/ML Engineer";

  return (
    <main className="hero-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <Link to="/" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to profile input
        </Link>

        <div className="mt-6 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-4xl font-bold sm:text-5xl">Your Career Analysis</h1>
            <p className="mt-2 text-muted-foreground">
              Based on {profile?.resumeName ?? "Resume.pdf"} ·{" "}
              {profile?.portfolio ?? "github.com/student"}
            </p>
          </div>
          <ReadinessRing value={readiness} role={role} />
        </div>

        <Panel className="mt-10" title="Profile Summary" icon={<Sparkles className="size-4" />}>
          <p className="text-lg leading-relaxed text-foreground/90">{profileSummary}</p>
        </Panel>

        <div className="mt-6 grid gap-6 lg:grid-cols-5">
          <Panel className="lg:col-span-3" title="Extracted Skills">
            <div className="space-y-4">
              {extractedSkills.map((s) => (
                <div key={s.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-muted-foreground tabular-nums">{s.level}%</span>
                  </div>
                  <Bar value={s.level} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            className="lg:col-span-2"
            title="Portfolio Analysis"
            icon={<FolderGit2 className="size-4" />}
          >
            <p className="text-xs tracking-widest text-muted-foreground uppercase">
              Projects detected
            </p>
            <ul className="mt-3 space-y-3">
              {portfolioProjects.map((p) => (
                <li
                  key={p.title}
                  className="flex items-start gap-3 rounded-xl border border-border bg-surface-2/60 p-3"
                >
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                  <div>
                    <p className="text-sm font-medium">{p.title}</p>
                    <p className="text-xs text-muted-foreground">{p.stack}</p>
                  </div>
                </li>
              ))}
            </ul>
            <div className="mt-4 rounded-xl border border-accent/30 bg-accent/10 p-4">
              <p className="text-xs font-semibold tracking-widest text-accent uppercase">
                AI feedback
              </p>
              <p className="mt-2 text-sm text-foreground/90">{portfolioFeedback}</p>
            </div>
          </Panel>
        </div>

        <Panel className="mt-6" title="Skill Gap" icon={<AlertTriangle className="size-4" />}>
          <div className="grid gap-4 sm:grid-cols-3">
            <GapCard
              tone="success"
              title="Strong Skills"
              items={skillGap.strong}
              mark="✓"
            />
            <GapCard
              tone="warning"
              title="Needs Improvement"
              items={skillGap.improve}
              mark="⚠"
            />
            <GapCard tone="danger" title="Critical Gaps" items={skillGap.critical} mark="●" />
          </div>

          <div className="mt-8">
            <div className="flex items-center justify-between text-xs tracking-widest text-muted-foreground uppercase">
              <span>Your level</span>
              <span>Required level</span>
            </div>
            <div className="mt-4 space-y-5">
              {extractedSkills.map((s) => (
                <div key={s.name}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="tabular-nums text-muted-foreground">
                      <span
                        className={
                          s.level >= s.required ? "text-success" : "text-danger"
                        }
                      >
                        {s.level}%
                      </span>{" "}
                      / {s.required}%
                    </span>
                  </div>
                  <div className="mt-2 space-y-1.5">
                    <Bar value={s.level} tone={s.level >= s.required ? "success" : "primary"} />
                    <Bar value={s.required} tone="muted" thin />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        <div className="mt-10 flex justify-center">
          <Button
            asChild
            size="lg"
            className="glow h-13 bg-gradient-accent px-8 text-base font-semibold text-primary-foreground hover:opacity-90"
          >
            <Link to="/plan">
              Generate My Personalized Plan
              <ArrowRight className="size-5" />
            </Link>
          </Button>
        </div>
      </div>
    </main>
  );
}

function ReadinessRing({ value, role }: { value: number; role: string }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  return (
    <div className="panel flex items-center gap-5 p-5">
      <div className="relative size-32 shrink-0">
        <svg viewBox="0 0 120 120" className="size-full -rotate-90">
          <circle cx="60" cy="60" r={r} fill="none" stroke="var(--muted)" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            r={r}
            fill="none"
            stroke="var(--primary)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c - (c * value) / 100}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <span className="font-display text-3xl font-bold">{value}%</span>
        </div>
      </div>
      <div>
        <p className="text-xs tracking-widest text-muted-foreground uppercase">
          Career Readiness
        </p>
        <p className="mt-1 font-display text-lg font-semibold">{role}</p>
        <p className="mt-1 text-xs text-muted-foreground">Target role</p>
      </div>
    </div>
  );
}

function Bar({
  value,
  tone = "primary",
  thin,
}: {
  value: number;
  tone?: "primary" | "success" | "muted";
  thin?: boolean;
}) {
  const color =
    tone === "success"
      ? "bg-success"
      : tone === "muted"
        ? "bg-muted-foreground/40"
        : "bg-gradient-accent";
  return (
    <div className={`mt-2 w-full overflow-hidden rounded-full bg-muted ${thin ? "h-1.5" : "h-2.5"}`}>
      <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function GapCard({
  tone,
  title,
  items,
  mark,
}: {
  tone: "success" | "warning" | "danger";
  title: string;
  items: string[];
  mark: string;
}) {
  const styles = {
    success: "border-success/30 bg-success/10 text-success",
    warning: "border-warning/30 bg-warning/10 text-warning",
    danger: "border-danger/30 bg-danger/10 text-danger",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${styles}`}>
      <p className="text-xs font-semibold tracking-widest uppercase">{title}</p>
      <ul className="mt-3 space-y-2">
        {items.map((i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-foreground">
            <span className={styles.split(" ").pop()}>{mark}</span>
            {i}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Panel({
  title,
  icon,
  children,
  className = "",
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel p-6 sm:p-7 ${className}`}>
      <h2 className="mb-5 flex items-center gap-2 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
        {icon && <span className="text-primary">{icon}</span>}
        {title}
      </h2>
      {children}
    </section>
  );
}
