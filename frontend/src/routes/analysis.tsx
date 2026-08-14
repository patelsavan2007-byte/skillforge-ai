import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Edit3,
  FileText,
  FolderGit2,
  GraduationCap,
  Briefcase,
  Award,
  Globe,
  Plus,
  Save,
  Sparkles,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  useProfile,
  saveProfile,
} from "@/lib/profile-store";

import { RequireAuth } from "@/components/auth/require-auth";

const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "Your Career Analysis & Unified Profile — SkillForge AI" },
      {
        name: "description",
        content:
          "AI profile analysis: Unified Resume + Portfolio skills, target role readiness score, skill gaps, and career roadmap.",
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
  const role = profile?.careerProfile?.targetRole || profile?.role || "AI/ML Engineer";

  // Use only real API data — no mock fallbacks
  const readiness = profile?.careerProfile?.careerReadiness ?? 0;
  const summary = profile?.careerProfile?.profileSummary || null;

  const unified = profile?.unifiedProfile;
  const career = profile?.careerProfile;

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Editable local state
  const [editSkills, setEditSkills] = useState<string[]>([]);
  const [editProjects, setEditProjects] = useState<any[]>([]);

  useEffect(() => {
    if (unified) {
      setEditSkills(unified.skills || []);
      setEditProjects(unified.projects || []);
    }
  }, [unified]);

  if (!profile) {
    return (
      <main className="hero-glow min-h-[calc(100vh-72px)] px-5 py-16">
        <section className="panel mx-auto max-w-2xl p-8 text-center sm:p-12">
          <span className="inline-flex size-14 items-center justify-center rounded-2xl bg-primary/15 text-primary"><FileText className="size-7" /></span>
          <h1 className="mt-6 text-3xl font-bold">Start with your career profile</h1>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">Upload a resume or add a public portfolio link first. Once we have your information, your personalized analysis will appear here.</p>
          <Button asChild size="lg" className="glow mt-8 bg-gradient-accent text-primary-foreground"><Link to="/upload">Upload &amp; start analysis <ArrowRight className="size-4" /></Link></Button>
        </section>
      </main>
    );
  }

  function openEditModal() {
    if (unified) {
      setEditSkills(unified.skills ? [...unified.skills] : []);
      setEditProjects(unified.projects ? JSON.parse(JSON.stringify(unified.projects)) : []);
    }
    setIsEditing(true);
  }

  async function handleSaveProfile() {
    setSaving(true);
    setSaveSuccessMsg(null);
    try {
      if (profile && profile.unifiedProfile) {
        const updatedUnified = {
          ...profile.unifiedProfile,
          skills: editSkills,
          projects: editProjects,
        };
        saveProfile({
          ...profile,
          unifiedProfile: updatedUnified,
        });
      }

      setSaveSuccessMsg("Profile saved successfully!");
      setTimeout(() => {
        setIsEditing(false);
        setSaveSuccessMsg(null);
      }, 800);
    } catch (err: any) {
      alert(err.message || "Error saving profile.");
    } finally {
      setSaving(false);
    }
  }

  // Display skills strictly from real unified profile — empty state if none
  const displaySkills = unified?.skills && unified.skills.length > 0 ? unified.skills : [];

  // Prefer deterministic user_strengths; then Gemini strongSkills; never mock data
  const strongSkills =
    career?.user_strengths && career.user_strengths.length > 0
      ? career.user_strengths
      : career?.strongSkills && career.strongSkills.length > 0
        ? career.strongSkills
        : [];

  // Real developing skills from API only
  const developingSkills = career?.developingSkills && career.developingSkills.length > 0
    ? career.developingSkills
    : [];

  // Prefer deterministic true_skill_gaps; then Gemini skillGaps; never mock data
  const criticalGaps =
    career?.true_skill_gaps && career.true_skill_gaps.length > 0
      ? career.true_skill_gaps
      : career?.skillGaps && career.skillGaps.length > 0
        ? career.skillGaps.map((g) => g.skill)
        : [];


  return (
    <main className="hero-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <Link to="/upload" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to resume & portfolio input
        </Link>

        <div className="mt-6 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-bold sm:text-5xl">Your Career Analysis</h1>
              <Button
                variant="outline"
                size="sm"
                onClick={openEditModal}
                className="gap-2 border-primary/40 text-primary hover:bg-primary/10"
              >
                <Edit3 className="size-4" /> Edit Profile
              </Button>
            </div>
            <div className="mt-3 flex items-center gap-3 text-sm text-muted-foreground">
              <span>Target Role: <strong className="text-foreground font-semibold">{role}</strong></span>
              <span className="font-medium text-foreground">Analysis Sources:</span>
              {unified?.source && (
                <div className="flex items-center gap-2">
                  {unified.source.resume && (
                    <Badge variant="secondary" className="bg-primary/15 text-primary border-primary/30">
                      Resume Source
                    </Badge>
                  )}
                  {unified.source.portfolio && (
                    <Badge variant="secondary" className="bg-accent/15 text-accent border-accent/30">
                      Portfolio Source
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </div>
          <ReadinessRing value={readiness} role={role} />
        </div>

        {/* Candidate Bio Header */}
        {unified && (
          <div className="panel mt-8 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold tracking-widest text-muted-foreground uppercase flex items-center gap-2">
                <FileText className="size-4 text-primary" /> Unified Candidate Profile
              </h2>
              <Button size="sm" variant="ghost" onClick={openEditModal} className="text-xs text-primary">
                <Edit3 className="size-3.5 mr-1" /> Edit
              </Button>
            </div>
            <div className="mt-4">
              <p className="font-semibold text-lg text-foreground">{unified.name || "Student Candidate"}</p>
              {unified.bio && <p className="mt-1 text-sm text-muted-foreground">{unified.bio}</p>}
            </div>
          </div>
        )}

        {/* Profile Summary */}
        <Panel className="mt-6" title="Profile Evaluation & Summary" icon={<Sparkles className="size-4" />}>
          {summary ? (
            <p className="text-lg leading-relaxed text-foreground/90">{summary}</p>
          ) : (
            <p className="text-sm text-muted-foreground italic">No profile summary available. Run a career analysis to generate your evaluation.</p>
          )}
        </Panel>

        {/* Unified Skills & Projects */}
        <div className="mt-6 grid gap-6 lg:grid-cols-5">
          <Panel className="lg:col-span-3" title="Unified Extracted Skills">
            {displaySkills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {displaySkills.map((skill, idx) => (
                  <Badge
                    key={idx}
                    variant="outline"
                    className="rounded-lg border-primary/30 bg-primary/10 px-3 py-1.5 text-sm font-medium text-foreground hover:border-primary"
                  >
                    <span className="grid size-4 place-items-center rounded bg-primary/20 text-[9px] font-bold text-primary">{skill.slice(0, 1)}</span>
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">No skills detected. Add a resume or portfolio to extract your skills.</p>
            )}

            <div className="mt-6 space-y-4">
              <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                Strong Target Role Skills
              </p>
              {strongSkills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {strongSkills.map((s, i) => (
                    <Badge key={i} className="bg-success/20 text-success border-success/30">
                      ✓ {s}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground italic">No matching role skills detected yet.</p>
              )}
            </div>
          </Panel>

          <Panel className="lg:col-span-2" title="Analyzed Projects & Evidence" icon={<FolderGit2 className="size-4" />}>
            {unified?.projects && unified.projects.length > 0 ? (
              <ul className="space-y-3">
                {unified.projects.map((p, idx) => (
                  <li key={idx} className="rounded-xl border border-border bg-surface-2/60 p-3.5">
                    <div className="flex items-start gap-2.5">
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                      <div>
                        <p className="text-sm font-medium">{p.name}</p>
                        <Badge variant="outline" className="mt-1 text-[10px]">{p.source === "both" ? "Both" : p.source === "resume" ? "Resume" : "Portfolio"}</Badge>
                        {p.description && <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{p.description}</p>}
                        {p.technologies && p.technologies.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {p.technologies.map((t, ti) => (
                              <span key={ti} className="rounded bg-surface-3 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground italic">No projects detected. Add a GitHub or portfolio URL to analyze your projects.</p>
            )}
          </Panel>
        </div>

        {/* Skill Gap Section */}
        <Panel className="mt-6" title="Skill Gap & Requirement Analysis" icon={<AlertTriangle className="size-4" />}>
          <div className="grid gap-4 sm:grid-cols-3">
            <GapCard tone="success" title="Strong Skills" items={strongSkills} mark="✓" />
            <GapCard tone="warning" title="Developing Skills" items={developingSkills} mark="⚠" />
            <GapCard tone="danger" title="Critical Skill Gaps" items={criticalGaps} mark="●" />
          </div>
        </Panel>

        <div className="mt-10 flex justify-center">
          <Button
            asChild
            size="lg"
            className="glow h-13 bg-gradient-accent px-8 text-base font-semibold text-primary-foreground hover:opacity-90"
          >
            <Link to="/plan">
              Generate My Personalized Roadmap
              <ArrowRight className="size-5" />
            </Link>
          </Button>
        </div>
      </div>

      {/* Edit Profile Modal */}
      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent className="max-h-[85vh] overflow-y-auto max-w-3xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <Edit3 className="size-5 text-primary" /> Edit Extracted Profile Skills
            </DialogTitle>
          </DialogHeader>

          {saveSuccessMsg && (
            <div className="rounded-lg bg-success/15 p-3 text-sm text-success font-medium">
              {saveSuccessMsg}
            </div>
          )}

          <div className="space-y-6 py-4">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
                Skills (Comma Separated)
              </h3>
              <Textarea
                rows={4}
                value={editSkills.join(", ")}
                onChange={(e) =>
                  setEditSkills(
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                }
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-border">
              <Button type="button" variant="secondary" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleSaveProfile}
                disabled={saving}
                className="bg-gradient-accent text-primary-foreground font-semibold"
              >
                <Save className="size-4 mr-2" />
                {saving ? "Saving..." : "Save Profile"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
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
        <p className="mt-1 text-xs text-muted-foreground">Target role match</p>
      </div>
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
        {(items || []).slice(0, 6).map((i, idx) => (
          <li key={idx} className="flex items-center gap-2 text-sm text-foreground">
            <span className={styles.split(" ").pop()}>{mark}</span>
            {i}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Panel({
  className = "",
  title,
  icon,
  children,
}: {
  className?: string;
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className={`panel p-6 ${className}`}>
      <h2 className="mb-4 text-xs font-semibold tracking-widest text-muted-foreground uppercase flex items-center gap-2">
        {icon && <span className="text-primary">{icon}</span>}
        {title}
      </h2>
      {children}
    </section>
  );
}
