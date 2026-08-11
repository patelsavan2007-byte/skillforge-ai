import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Award,
  BookOpen,
  CheckCircle2,
  Flame,
  Lightbulb,
  MessageSquareCode,
  Rocket,
  Route as RouteIcon,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  careerAdvice,
  certifications,
  courses,
  interviewTopics,
  progress,
  projects,
  roadmap,
} from "@/lib/mock-data";
import { useProfile } from "@/lib/profile-store";

export const Route = createFileRoute("/plan")({
  head: () => ({
    meta: [
      { title: "Your Personalized Career Plan — SkillForge AI" },
      {
        name: "description",
        content:
          "A personalized learning roadmap with courses, projects, certifications and interview prep.",
      },
      {
        property: "og:title",
        content: "Your Personalized Career Plan — SkillForge AI",
      },
      {
        property: "og:description",
        content: "Roadmap, courses, projects, certifications and interview prep.",
      },
    ],
  }),
  component: PlanPage,
});

function PlanPage() {
  const profile = useProfile();
  const role = profile?.role ?? "AI/ML Engineer";

  return (
    <main className="hero-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <Link to="/analysis" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to analysis
        </Link>

        <header className="mt-6">
          <h1 className="text-4xl font-bold sm:text-5xl">
            Your <span className="text-gradient">Personalized Career Plan</span>
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-muted-foreground">
            Target role:
            <Badge className="bg-primary/15 text-primary hover:bg-primary/20">{role}</Badge>
          </div>
        </header>

        <section className="panel mt-8 grid gap-6 p-6 sm:grid-cols-2 lg:grid-cols-4">
          {progress.map((p) => (
            <div key={p.label}>
              <p className="text-xs tracking-widest text-muted-foreground uppercase">
                {p.label}
              </p>
              <p className="mt-2 font-display text-2xl font-bold">{p.detail}</p>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-gradient-accent"
                  style={{ width: `${p.value}%` }}
                />
              </div>
            </div>
          ))}
        </section>

        <Tabs defaultValue="roadmap" className="mt-10">
          <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 bg-surface p-1.5">
            <Tab value="roadmap" icon={<RouteIcon className="size-4" />} label="Roadmap" />
            <Tab value="courses" icon={<BookOpen className="size-4" />} label="Courses" />
            <Tab value="projects" icon={<Rocket className="size-4" />} label="Projects" />
            <Tab value="certs" icon={<Award className="size-4" />} label="Certifications" />
            <Tab
              value="interview"
              icon={<MessageSquareCode className="size-4" />}
              label="Interview Prep"
            />
          </TabsList>

          <TabsContent value="roadmap" className="mt-6">
            <ol className="relative space-y-4 border-l border-border pl-6">
              {roadmap.map((step) => (
                <li key={step.title} className="relative">
                  <span
                    className={`absolute -left-[31px] top-5 grid size-5 place-items-center rounded-full border-2 ${
                      step.status === "done"
                        ? "border-success bg-success text-success-foreground"
                        : step.status === "current"
                          ? "border-accent bg-accent text-accent-foreground"
                          : "border-border bg-surface-2"
                    }`}
                  >
                    {step.status === "done" && <CheckCircle2 className="size-3" />}
                    {step.status === "current" && <Flame className="size-3" />}
                  </span>
                  <div
                    className={`rounded-2xl border p-5 ${
                      step.status === "current"
                        ? "glow border-accent/40 bg-surface-2"
                        : "border-border bg-surface/70"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="flex items-center gap-2 font-display text-lg font-semibold">
                        {step.status === "current" && (
                          <Flame className="size-4 text-accent" />
                        )}
                        {step.title}
                      </h3>
                      <Badge variant="secondary">{step.difficulty}</Badge>
                      {step.status === "done" ? (
                        <Badge className="bg-success/15 text-success hover:bg-success/20">
                          Completed
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          {step.duration}
                        </Badge>
                      )}

                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">
                      <span className="text-foreground/80">Why: </span>
                      {step.why}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {step.skills.map((s) => (
                        <span
                          key={s}
                          className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted-foreground"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </TabsContent>

          <TabsContent value="courses" className="mt-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {courses.map((c) => (
                <Card key={c.title}>
                  <h3 className="font-display text-base font-semibold">{c.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{c.platform}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge className="bg-primary/15 text-primary hover:bg-primary/20">
                      {c.skill}
                    </Badge>
                    <Badge variant="secondary">{c.difficulty}</Badge>
                    <Badge variant="outline" className="text-muted-foreground">
                      {c.duration}
                    </Badge>
                  </div>
                  <p className="mt-3 text-sm text-muted-foreground">
                    <span className="text-foreground/80">Why recommended: </span>
                    {c.why}
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-4 w-full"
                    onClick={() => toast("Course link will open once the backend is connected.")}
                  >
                    View Course
                  </Button>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="projects" className="mt-6">
            <div className="grid gap-4 md:grid-cols-3">
              {projects.map((p) => (
                <Card key={p.title}>
                  <h3 className="font-display text-base font-semibold">{p.title}</h3>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge variant="secondary">{p.difficulty}</Badge>
                    <Badge variant="outline" className="text-muted-foreground">
                      {p.time}
                    </Badge>
                  </div>
                  <p className="mt-3 text-xs tracking-widest text-muted-foreground uppercase">
                    Skills gained
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {p.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <p className="mt-3 text-sm text-muted-foreground">
                    <span className="text-foreground/80">Why: </span>
                    {p.why}
                  </p>
                  <p className="mt-3 inline-flex rounded-lg bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent">
                    {p.impact}
                  </p>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="certs" className="mt-6">
            <div className="grid gap-4 md:grid-cols-3">
              {certifications.map((c) => (
                <Card key={c.name}>
                  <Award className="size-6 text-accent" />
                  <h3 className="mt-3 font-display text-base font-semibold">{c.name}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{c.provider}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge className="bg-primary/15 text-primary hover:bg-primary/20">
                      {c.skill}
                    </Badge>
                    <Badge variant="secondary">{c.difficulty}</Badge>
                  </div>
                  <p className="mt-3 text-sm text-muted-foreground">
                    <span className="text-foreground/80">Why recommended: </span>
                    {c.why}
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-4 w-full"
                    onClick={() => toast("Certification details coming with the live backend.")}
                  >
                    View
                  </Button>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="interview" className="mt-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <p className="text-xs tracking-widest text-muted-foreground uppercase">
                  High priority topics
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {interviewTopics.high.map((t) => (
                    <Badge key={t} className="bg-danger/15 text-danger hover:bg-danger/20">
                      {t}
                    </Badge>
                  ))}
                </div>
                <p className="mt-5 text-xs tracking-widest text-muted-foreground uppercase">
                  Also review
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {interviewTopics.medium.map((t) => (
                    <Badge key={t} variant="secondary">
                      {t}
                    </Badge>
                  ))}
                </div>
              </Card>
              <Card>
                <p className="font-display text-2xl font-bold">
                  50 personalized interview questions
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Generated from your detected skill gaps.
                </p>
                <div className="mt-4 space-y-2">
                  {interviewTopics.categories.map((c) => (
                    <div
                      key={c.name}
                      className="flex items-center justify-between rounded-lg border border-border bg-surface-2/60 px-3 py-2 text-sm"
                    >
                      <span>{c.name}</span>
                      <span className="text-muted-foreground tabular-nums">
                        {c.count} questions
                      </span>
                    </div>
                  ))}
                </div>
                <Button
                  className="glow mt-5 w-full bg-gradient-accent font-semibold text-primary-foreground hover:opacity-90"
                  onClick={() => toast("Interview prep unlocks with your AI backend.")}
                >
                  Start Interview Prep
                </Button>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        <section className="panel glow mt-10 p-7">
          <p className="flex items-center gap-2 text-xs font-semibold tracking-widest text-accent uppercase">
            <Lightbulb className="size-4" />
            Your next best step
          </p>
          <p className="mt-3 text-lg leading-relaxed text-foreground/90">{careerAdvice}</p>
        </section>
      </div>
    </main>
  );
}

function Tab({ value, icon, label }: { value: string; icon: React.ReactNode; label: string }) {
  return (
    <TabsTrigger
      value={value}
      className="gap-2 rounded-lg px-4 py-2 data-[state=active]:bg-surface-2 data-[state=active]:text-primary"
    >
      {icon}
      {label}
    </TabsTrigger>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-primary/40">
      {children}
    </div>
  );
}
