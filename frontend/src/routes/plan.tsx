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
  careerAdvice as mockAdvice,
  certifications as mockCerts,
  courses as mockCourses,
  projects as mockProjects,
  roadmap as mockRoadmap,
} from "@/lib/mock-data";
import {
  useProfile,
  type LearningPathData,
  type RoadmapWeek,
} from "@/lib/profile-store";

import { RequireAuth } from "@/components/auth/require-auth";

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
  const role = profile?.careerProfile?.targetRole || profile?.role || "AI/ML Engineer";
  const learning = profile?.learningPath;

  type CourseItem = NonNullable<LearningPathData["courses"]>[number];
  type ProjectItem = NonNullable<LearningPathData["recommendedProjects"]>[number];
  type CertItem = NonNullable<LearningPathData["certifications"]>[number];
  type InterviewItem = NonNullable<LearningPathData["interviewPrep"]>[number];

  const roadmapItems: RoadmapWeek[] =
    learning?.roadmap && learning.roadmap.length > 0 ? learning.roadmap : (mockRoadmap as unknown as RoadmapWeek[]);
  const courseItems: CourseItem[] =
    learning?.courses && learning.courses.length > 0 ? learning.courses : (mockCourses as unknown as CourseItem[]);
  const projectItems: ProjectItem[] =
    learning?.recommendedProjects && learning.recommendedProjects.length > 0
      ? learning.recommendedProjects
      : (mockProjects as unknown as ProjectItem[]);
  const certItems: CertItem[] =
    learning?.certifications && learning.certifications.length > 0
      ? learning.certifications
      : (mockCerts as unknown as CertItem[]);
  const interviewItems: InterviewItem[] = learning?.interviewPrep || [];
  const adviceList = learning?.careerAdvice && learning.careerAdvice.length > 0 ? learning.careerAdvice : [mockAdvice];

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
          </TabsContent>

          <TabsContent value="courses" className="mt-6">
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
          </TabsContent>

          <TabsContent value="projects" className="mt-6">
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
          </TabsContent>

          <TabsContent value="certs" className="mt-6">
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
          <ul className="mt-3 space-y-2">
            {adviceList.map((adv: string, idx: number) => (
              <li key={idx} className="text-base leading-relaxed text-foreground/90 flex items-start gap-2">
                <span className="text-accent font-bold">•</span>
                {adv}
              </li>
            ))}
          </ul>
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
