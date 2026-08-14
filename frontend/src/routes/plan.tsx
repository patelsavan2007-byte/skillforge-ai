import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  Award,
  BookOpen,
  CheckCircle2,
  FileText,
  Flame,
  Lightbulb,
  MessageSquareCode,
  Rocket,
  Route as RouteIcon,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useProfile,
  type LearningPathData,
  type RoadmapWeek,
  updateProgressState,
  updateRoadmapCheckpoint,
} from "@/lib/profile-store";

import { RequireAuth } from "@/components/auth/require-auth";

const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";

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
  component: () => (
    <RequireAuth>
      <PlanPage />
    </RequireAuth>
  ),
});

function PlanPage() {
  const profile = useProfile();
  const [updatingWeek, setUpdatingWeek] = useState<number | null>(null);

  // No analysis yet — show explicit empty state
  if (!profile) {
    return (
      <main className="hero-glow min-h-[calc(100vh-72px)] px-5 py-16">
        <section className="panel mx-auto max-w-2xl p-8 text-center sm:p-12">
          <span className="inline-flex size-14 items-center justify-center rounded-2xl bg-primary/15 text-primary">
            <FileText className="size-7" />
          </span>
          <h1 className="mt-6 text-3xl font-bold">No career analysis yet</h1>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
            Your personalized career plan will appear here once you upload a resume or portfolio and run your career analysis.
          </p>
          <Button asChild size="lg" className="glow mt-8 bg-gradient-accent text-primary-foreground">
            <Link to="/">Start your career analysis <span aria-hidden>→</span></Link>
          </Button>
        </section>
      </main>
    );
  }

  const role = profile?.careerProfile?.targetRole || profile?.role || "AI/ML Engineer";
  const learning = profile?.learningPath;

  // No learning path generated — show explicit empty state
  if (!learning) {
    return (
      <main className="hero-glow min-h-[calc(100vh-72px)] px-5 py-16">
        <section className="panel mx-auto max-w-2xl p-8 text-center sm:p-12">
          <span className="inline-flex size-14 items-center justify-center rounded-2xl bg-primary/15 text-primary">
            <RouteIcon className="size-7" />
          </span>
          <h1 className="mt-6 text-3xl font-bold">Learning path not generated</h1>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
            Your career analysis completed but no learning path was returned. Please re-run the analysis.
          </p>
          <Button asChild size="lg" className="glow mt-8 bg-gradient-accent text-primary-foreground">
            <Link to="/">Re-run analysis <span aria-hidden>→</span></Link>
          </Button>
        </section>
      </main>
    );
  }

  type CourseItem = NonNullable<LearningPathData["courses"]>[number];
  type ProjectItem = NonNullable<LearningPathData["recommendedProjects"]>[number];
  type CertItem = NonNullable<LearningPathData["certifications"]>[number];
  type InterviewItem = NonNullable<LearningPathData["interviewPrep"]>[number];

  // Use real API data only — never fall back to mock arrays
  const roadmapItems: RoadmapWeek[] = learning.roadmap ?? [];
  const courseItems: CourseItem[] = learning.courses ?? [];
  const projectItems: ProjectItem[] = learning.recommendedProjects ?? [];
  const certItems: CertItem[] = learning.certifications ?? [];
  const interviewItems: InterviewItem[] = learning.interviewPrep ?? [];
  const adviceList: string[] = learning.careerAdvice ?? [];
  const completedMilestones = profile.progress?.completedRoadmapItems
    ?? roadmapItems.filter((item) => item.completed).length;
  const totalMilestones = profile.progress?.totalRoadmapItems ?? roadmapItems.length;
  const roadmapProgress = profile.progress?.roadmapProgress
    ?? (totalMilestones ? Math.trunc((completedMilestones / totalMilestones) * 100) : 0);

  async function toggleCheckpoint(step: RoadmapWeek) {
    const previous = Boolean(step.completed);
    const completed = !previous;
    updateRoadmapCheckpoint(step.week, completed);
    setUpdatingWeek(step.week);
    try {
      const response = await fetch(`${API_BASE_URL}/api/progress/checkpoint`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ week: step.week, completed, learningPathId: learning?.id }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !body.success) {
        throw new Error(body.detail || "Unable to save this checkpoint.");
      }
      updateProgressState(body.data, body.roadmap);
    } catch (error) {
      updateRoadmapCheckpoint(step.week, previous);
      toast.error(error instanceof Error ? error.message : "Unable to save this checkpoint.");
    } finally {
      setUpdatingWeek(null);
    }
  }

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
            {learning?.durationWeeks && (
              <Badge variant="outline" className="text-muted-foreground">
                {learning.durationWeeks} Weeks Roadmap
              </Badge>
            )}
          </div>
          <section className="mt-6 max-w-xl rounded-2xl border border-primary/20 bg-surface/70 p-4">
            <div className="flex items-center justify-between gap-4 text-sm">
              <span className="font-medium">Progress overview</span>
              <span className="text-muted-foreground">
                {completedMilestones} / {totalMilestones} milestones completed · {roadmapProgress}%
              </span>
            </div>
            <Progress value={roadmapProgress} className="mt-3" aria-label={`${roadmapProgress}% roadmap complete`} />
          </section>
        </header>

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
            {roadmapItems.length > 0 ? (
              <ol className="relative space-y-4 border-l border-border pl-6">
                {roadmapItems.map((step, idx) => (
                  <li key={idx} className="relative">
                    <span
                      className={`absolute -left-[31px] top-5 grid size-5 place-items-center rounded-full border-2 ${
                        step.completed
                          ? "border-success bg-success text-success-foreground"
                          : idx === 1
                            ? "border-accent bg-accent text-accent-foreground"
                            : "border-border bg-surface-2"
                      }`}
                    >
                      {step.completed && <CheckCircle2 className="size-3" />}
                      {idx === 1 && <Flame className="size-3" />}
                    </span>
                    <div
                      className={`rounded-2xl border p-5 ${
                        idx === 1
                          ? "glow border-accent/40 bg-surface-2"
                          : "border-border bg-surface/70"
                      }`}
                    >
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="flex items-center gap-2 font-display text-lg font-semibold">
                          {idx === 1 && <Flame className="size-4 text-accent" />}
                          Week {step.week}: {step.title}
                        </h3>
                        {step.completed ? (
                          <Badge className="bg-success/15 text-success hover:bg-success/20">
                            Completed
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-muted-foreground">
                            In Progress
                          </Badge>
                        )}
                        <label className="ml-auto flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
                          <Checkbox
                            checked={Boolean(step.completed)}
                            disabled={updatingWeek === step.week}
                            onCheckedChange={() => toggleCheckpoint(step)}
                            aria-label={`Mark Week ${step.week} as ${step.completed ? "incomplete" : "complete"}`}
                          />
                          {updatingWeek === step.week ? "Saving…" : "Checkpoint"}
                        </label>
                      </div>

                      {step.project && (
                        <p className="mt-3 text-sm text-muted-foreground">
                          <span className="text-foreground/80 font-medium">Hands-on Project: </span>
                          {step.project.title} — {step.project.description}
                        </p>
                      )}

                      {step.skills && step.skills.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {step.skills.map((s: string) => (
                            <span
                              key={s}
                              className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted-foreground"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <Card>
                <p className="text-sm text-muted-foreground italic">No roadmap milestones generated yet. Run your career analysis to see your personalized learning roadmap.</p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="courses" className="mt-6">
            {courseItems.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {courseItems.map((c, idx) => (
                  <Card key={idx}>
                    <h3 className="font-display text-base font-semibold">{c.title}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">{c.provider || "Online Provider"}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {c.skillAddressed && (
                        <Badge className="bg-primary/15 text-primary hover:bg-primary/20">
                          {c.skillAddressed}
                        </Badge>
                      )}
                      {c.difficulty && <Badge variant="secondary">{c.difficulty}</Badge>}
                      {c.duration && (
                        <Badge variant="outline" className="text-muted-foreground">
                          {c.duration}
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="mt-4 w-full"
                      onClick={() => {
                        if (c.url) window.open(c.url, "_blank");
                        else toast("Opening course portal...");
                      }}
                    >
                      View Course
                    </Button>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <p className="text-sm text-muted-foreground italic">No courses recommended yet. E5-ranked courses will appear here after career analysis.</p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="projects" className="mt-6">
            {projectItems.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {projectItems.map((p, idx) => (
                  <Card key={idx}>
                    <h3 className="font-display text-base font-semibold">{p.title}</h3>
                    {p.difficulty && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge variant="secondary">{p.difficulty}</Badge>
                      </div>
                    )}
                    {p.description && (
                      <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                        {p.description}
                      </p>
                    )}
                    {p.technologies && p.technologies.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {p.technologies.map((s: string, si: number) => (
                          <span
                            key={si}
                            className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <p className="text-sm text-muted-foreground italic">No projects recommended yet. Hands-on project ideas will appear here after career analysis.</p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="certs" className="mt-6">
            {certItems.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-3">
                {certItems.map((c, idx) => (
                  <Card key={idx}>
                    <Award className="size-6 text-accent" />
                    <h3 className="mt-3 font-display text-base font-semibold">{c.name}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">{c.provider || "Industry Certification"}</p>
                    {c.priority && (
                      <div className="mt-3">
                        <Badge className="bg-primary/15 text-primary">Priority: {c.priority}</Badge>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <p className="text-sm text-muted-foreground italic">No certifications recommended yet. Certification suggestions will appear here after career analysis.</p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="interview" className="mt-6">
            <div className="grid gap-4 md:grid-cols-2">
              {interviewItems.length > 0 ? (
                interviewItems.map((item, idx) => (
                  <Card key={idx}>
                    <Badge className="bg-accent/15 text-accent">{item.topic || "Interview Prep"}</Badge>
                    <p className="mt-3 font-semibold text-base text-foreground">{item.question}</p>
                    {item.keyConcept && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        <strong className="text-foreground/80">Key Concept: </strong>
                        {item.keyConcept}
                      </p>
                    )}
                  </Card>
                ))
              ) : (
                <Card>
                  <p className="font-display text-xl font-bold">Recommended Interview Focus</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Practice technical system design questions, data structure optimization, and role-specific architecture for {role}.
                  </p>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <section className="panel glow mt-10 p-7">
          <p className="flex items-center gap-2 text-xs font-semibold tracking-widest text-accent uppercase">
            <Lightbulb className="size-4" />
            AI Career Mentor Advice
          </p>
          {adviceList.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {adviceList.map((adv: string, idx: number) => (
                <li key={idx} className="text-base leading-relaxed text-foreground/90 flex items-start gap-2">
                  <span className="text-accent font-bold">•</span>
                  {adv}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-muted-foreground italic">Career mentor advice will appear here after your analysis is generated.</p>
          )}
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
