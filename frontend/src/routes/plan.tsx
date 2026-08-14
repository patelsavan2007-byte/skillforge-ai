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
  Sparkles,
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
import { getAuthHeaders } from "@/lib/auth-store";

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

  const initialReadiness = profile.progress?.initialReadiness
    ?? profile.learningPath?.initialReadiness
    ?? profile.careerProfile?.careerReadiness
    ?? 50;

  const currentReadiness = profile.progress?.careerReadiness
    ?? profile.learningPath?.careerReadiness
    ?? profile.careerProfile?.careerReadiness
    ?? 50;

  const improvedScore = profile.progress?.improvedScore
    ?? profile.learningPath?.improvedScore
    ?? Math.max(0, currentReadiness - initialReadiness);

  const completedGaps = profile.progress?.completedGaps ?? [];
  const remainingGaps = profile.progress?.remainingGaps ?? profile.careerProfile?.true_skill_gaps ?? [];

  const topPriorities = profile.careerProfile?.prioritized_gaps?.critical?.length
    ? profile.careerProfile.prioritized_gaps.critical
    : (profile.careerProfile?.true_skill_gaps?.slice(0, 3) ?? []);

  const strengths = profile.careerProfile?.user_strengths?.slice(0, 5) ?? [];

  const totalEstimatedHours = learning.estimatedCompletionHours
    ?? roadmapItems.reduce((acc, curr) => acc + (typeof curr.estimated_hours === 'number' ? curr.estimated_hours : 8), 0);
  const totalEstimatedDays = learning.estimatedCompletionDays
    ?? roadmapItems.reduce((acc, curr) => acc + (typeof curr.estimated_days === 'number' ? curr.estimated_days : 2), 0);

  async function toggleCheckpoint(step: RoadmapWeek) {
    const previous = Boolean(step.completed);
    const completed = !previous;
    updateRoadmapCheckpoint(step.week, completed);
    setUpdatingWeek(step.week);

    try {
      const response = await fetch(`${API_BASE_URL}/api/progress/checkpoint`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        credentials: "include",
        body: JSON.stringify({ week: step.week, completed, learningPathId: learning?.id }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !body.success) {
        throw new Error(body.detail || "Unable to save this checkpoint.");
      }
      updateProgressState(body.data, body.roadmap);
      toast.success(completed ? `Completed Phase ${step.week}! Readiness updated.` : `Phase ${step.week} marked incomplete.`);
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
            <Badge variant="outline" className="text-muted-foreground">
              Personalized Roadmap • {totalEstimatedDays || 6} Days ({totalEstimatedHours || 24} hours)
            </Badge>
          </div>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            {/* Career Readiness Gauge Card */}
            <section className="rounded-2xl border border-primary/20 bg-surface/70 p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Career Readiness Estimate
                  </span>
                  {improvedScore > 0 && (
                    <Badge className="bg-success/15 text-success border border-success/30 text-xs font-semibold">
                      +{improvedScore}% improvement
                    </Badge>
                  )}
                </div>
                <div className="mt-3 flex items-baseline gap-3">
                  <span className="font-display text-4xl font-bold text-gradient">
                    {currentReadiness}%
                  </span>
                  {improvedScore > 0 && (
                    <span className="text-xs text-muted-foreground">
                      (Baseline: {initialReadiness}%)
                    </span>
                  )}
                </div>
                <Progress value={currentReadiness} className="mt-3 h-2.5" aria-label={`${currentReadiness}% career readiness`} />
              </div>
              <p className="mt-4 text-xs text-muted-foreground italic leading-relaxed">
                Based on verified skills from your profile and completed milestones. This score increases dynamically as you verify skills.
              </p>
            </section>

            {/* Live Progress & Gaps Tracker */}
            <section className="rounded-2xl border border-primary/20 bg-surface/70 p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="font-medium">Milestones Progress</span>
                  <span className="text-muted-foreground text-xs font-semibold">
                    {completedMilestones} / {totalMilestones} completed · {roadmapProgress}%
                  </span>
                </div>
                <Progress value={roadmapProgress} className="mt-2.5 h-2" aria-label={`${roadmapProgress}% roadmap complete`} />

                <div className="mt-4 space-y-2.5">
                  {completedGaps.length > 0 && (
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-success">
                        Skills Verified / Completed
                      </span>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {completedGaps.map((skill, i) => (
                          <Badge key={i} className="bg-success/15 text-success text-[11px] py-0 px-2">
                            ✓ {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-accent">
                      Remaining Priority Gaps
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {remainingGaps.length > 0 ? (
                        remainingGaps.slice(0, 4).map((gap, i) => (
                          <Badge key={i} variant="outline" className="text-[11px] py-0 px-2 text-foreground/80">
                            • {gap}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-success font-medium">All targeted gaps completed!</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* Why this plan section */}
          <section className="mt-4 rounded-2xl border border-border bg-surface/50 p-5">
            <h2 className="flex items-center gap-2 font-display text-sm font-semibold text-foreground">
              <Sparkles className="size-4 text-primary" />
              Why this plan is personalized for you
            </h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-accent">Core Focus Areas</span>
                <p className="mt-1 text-xs text-muted-foreground">
                  {topPriorities.join(", ") || "Targeted production architectures and testing"}
                </p>
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">Your Verified Strengths</span>
                <p className="mt-1 text-xs text-muted-foreground">
                  {strengths.join(", ") || "Full-stack foundations and project implementations"}
                </p>
              </div>
            </div>
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
              <ol className="relative space-y-6 border-l border-border pl-6">
                {roadmapItems.map((step, idx) => (
                  <li key={idx} className="relative">
                    <span
                      className={`absolute -left-[31px] top-6 grid size-5 place-items-center rounded-full border-2 ${
                        step.completed
                          ? "border-success bg-success text-success-foreground"
                          : idx === 0
                            ? "border-accent bg-accent text-accent-foreground"
                            : "border-border bg-surface-2"
                      }`}
                    >
                      {step.completed && <CheckCircle2 className="size-3" />}
                      {idx === 0 && !step.completed && <Flame className="size-3" />}
                    </span>

                    <div
                      className={`rounded-2xl border p-6 ${
                        step.completed
                          ? "border-success/30 bg-surface/50"
                          : idx === 0
                            ? "glow border-accent/40 bg-surface-2"
                            : "border-border bg-surface/70"
                      }`}
                    >
                      {/* Phase Header */}
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2.5">
                          <h3 className="font-display text-lg font-bold text-foreground">
                            Phase {step.week}: {step.title}
                          </h3>
                          {step.skill && (
                            <Badge className="bg-primary/15 text-primary text-xs font-semibold">
                              {step.skill}
                            </Badge>
                          )}
                          {step.current_level && step.target_level && (
                            <Badge variant="outline" className="text-xs text-muted-foreground">
                              {step.current_level} → {step.target_level}
                            </Badge>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {step.estimated_hours && (
                            <Badge variant="secondary" className="text-xs">
                              ⏱ {step.estimated_hours}h {step.estimated_days ? `• 📅 ${step.estimated_days}d` : ''}
                            </Badge>
                          )}
                          {step.difficulty && (
                            <Badge variant="outline" className="text-xs">
                              {step.difficulty}
                            </Badge>
                          )}
                          {step.completed ? (
                            <Badge className="bg-success/15 text-success hover:bg-success/20">
                              ✓ Completed
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-accent border-accent/30">
                              {idx === 0 ? "In Progress" : "Upcoming"}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Objective & Why this matters */}
                      {step.objective && (
                        <p className="mt-3 text-sm text-foreground/90 leading-relaxed">
                          <strong className="text-primary font-semibold">Objective: </strong>
                          {step.objective}
                        </p>
                      )}

                      {step.why_this_matters && (
                        <p className="mt-1 text-xs text-muted-foreground italic">
                          <strong className="text-accent font-medium">Why this matters: </strong>
                          {step.why_this_matters}
                        </p>
                      )}

                      {/* Subtasks breakdown */}
                      {step.tasks && step.tasks.length > 0 && (
                        <div className="mt-4 rounded-xl border border-border/70 bg-surface/50 p-3.5">
                          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Daily Task Breakdown
                          </span>
                          <ul className="mt-2 space-y-2">
                            {step.tasks.map((t, ti) => (
                              <li key={ti} className="flex items-start justify-between gap-3 text-xs">
                                <div className="flex items-start gap-2">
                                  <span className="text-primary font-bold">•</span>
                                  <div>
                                    <span className="font-semibold text-foreground">{t.title}</span>
                                    {t.description && (
                                      <p className="text-muted-foreground mt-0.5">{t.description}</p>
                                    )}
                                  </div>
                                </div>
                                {t.duration && (
                                  <span className="shrink-0 rounded bg-surface-2 px-1.5 py-0.5 text-[11px] font-mono text-muted-foreground">
                                    {t.duration}
                                  </span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Checkpoint & Project */}
                      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5">
                        <div className="max-w-xl">
                          <span className="text-xs font-bold uppercase tracking-wider text-primary">
                            Verification Checkpoint
                          </span>
                          <p className="mt-0.5 text-xs text-foreground/90">
                            {step.checkpoint || `Build and verify a functional ${step.skill || 'module'} with unit and integration tests.`}
                          </p>
                        </div>

                        <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-primary/30 bg-surface px-3 py-1.5 text-xs font-semibold text-foreground shadow-sm hover:bg-surface-2">
                          <Checkbox
                            checked={Boolean(step.completed)}
                            disabled={updatingWeek === step.week}
                            onCheckedChange={() => toggleCheckpoint(step)}
                            aria-label={`Mark Phase ${step.week} as ${step.completed ? "incomplete" : "complete"}`}
                          />
                          {updatingWeek === step.week ? "Recalculating…" : step.completed ? "Completed" : "Mark Complete"}
                        </label>
                      </div>

                      {step.project && (
                        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-surface-2/50 px-3 py-2 text-xs">
                          <p className="text-muted-foreground flex-1">
                            <span className="text-foreground/80 font-medium">Recommended Mini-Project: </span>
                            {step.project.title} — {step.project.description}
                          </p>
                          {step.project.url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-primary hover:bg-primary/10 shrink-0"
                              onClick={() => window.open(step.project?.url, "_blank")}
                            >
                              Starter Repo ↗
                            </Button>
                          )}
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
                    <p className="mt-1 text-xs text-muted-foreground">{c.provider || "Verified Provider"}</p>
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
                    {c.why_recommended && (
                      <p className="mt-3 text-xs text-muted-foreground italic">
                        <span className="text-accent font-medium">Why: </span>
                        {c.why_recommended}
                      </p>
                    )}
                    {c.url ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        className="mt-4 w-full"
                        onClick={() => window.open(c.url, "_blank")}
                      >
                        View Course
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full text-muted-foreground"
                        disabled
                      >
                        Search Course
                      </Button>
                    )}
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
                    {p.why_recommended && (
                      <p className="mt-2 text-xs text-accent italic">
                        <span className="font-medium">Why recommended: </span>
                        {p.why_recommended}
                      </p>
                    )}
                    {p.expected_resume_impact && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        <strong className="text-foreground/80">Resume Impact: </strong>
                        {p.expected_resume_impact}
                      </p>
                    )}
                    {p.suggested_stack && p.suggested_stack.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {p.suggested_stack.map((s: string, si: number) => (
                          <span
                            key={si}
                            className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-primary"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    {(!p.suggested_stack || p.suggested_stack.length === 0) && p.technologies && p.technologies.length > 0 && (
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
                    {p.url ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        className="mt-4 w-full"
                        onClick={() => window.open(p.url, "_blank")}
                      >
                        View Reference Architecture ↗
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full text-muted-foreground"
                        onClick={() => window.open(`https://github.com/search?q=${encodeURIComponent(p.title + ' ' + (p.technologies?.join(' ') || ''))}`, "_blank")}
                      >
                        Explore GitHub Templates ↗
                      </Button>
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
                    <div className="flex items-center justify-between">
                      <Award className="size-6 text-accent" />
                      {c.priority && (
                        <Badge className="bg-primary/15 text-primary text-xs">Priority: {c.priority}</Badge>
                      )}
                    </div>
                    <h3 className="mt-3 font-display text-base font-semibold text-foreground">{c.name}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">{c.provider || "Industry Credential"}</p>
                    {c.why_recommended && (
                      <p className="mt-2 text-xs text-muted-foreground italic leading-relaxed">
                        {c.why_recommended}
                      </p>
                    )}
                    {c.url ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        className="mt-4 w-full"
                        onClick={() => window.open(c.url, "_blank")}
                      >
                        Official Website ↗
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full text-muted-foreground"
                        onClick={() => window.open(`https://www.google.com/search?q=${encodeURIComponent(c.name + ' ' + (c.provider || ''))}`, "_blank")}
                      >
                        Explore Certification ↗
                      </Button>
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
                    <div className="flex items-center justify-between gap-2">
                      <Badge className="bg-accent/15 text-accent">{item.topic || "Interview Prep"}</Badge>
                      {item.resourceTitle && (
                        <span className="text-[11px] font-mono text-muted-foreground">{item.resourceTitle}</span>
                      )}
                    </div>
                    <p className="mt-3 font-semibold text-base text-foreground leading-snug">{item.question}</p>
                    {item.keyConcept && (
                      <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                        <strong className="text-foreground/80">Key Concept: </strong>
                        {item.keyConcept}
                      </p>
                    )}
                    {item.url ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full border-primary/30 text-primary hover:bg-primary/10"
                        onClick={() => window.open(item.url, "_blank")}
                      >
                        Open Practice Website ↗
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-4 w-full text-muted-foreground"
                        onClick={() => window.open(`https://www.google.com/search?q=${encodeURIComponent(item.topic + ' interview questions practice')}`, "_blank")}
                      >
                        Search Practice Questions ↗
                      </Button>
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
