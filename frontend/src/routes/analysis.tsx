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
  X,
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
  DialogTrigger,
} from "@/components/ui/dialog";

import {
  extractedSkills,
  portfolioFeedback,
  portfolioProjects,
  profileSummary,
  readiness,
  skillGap,
} from "@/lib/mock-data";
import {
  useProfile,
  saveProfile,
  ExtractedResumeProfile,
  ExtractedEducation,
  ExtractedExperience,
  ExtractedProject,
} from "@/lib/profile-store";

import { RequireAuth } from "@/components/auth/require-auth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "Your Career Analysis & Extracted Profile — SkillForge AI" },
      {
        name: "description",
        content:
          "AI profile analysis: Hugging Face NER extracted skills, education, experience, SGPA/CGPA, projects and editable career profile.",
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
  const [extractedData, setExtractedData] = useState<ExtractedResumeProfile | null>(
    profile?.extractedProfile ?? null
  );

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Editable local state
  const [editForm, setEditForm] = useState<ExtractedResumeProfile>({
    personal: { name: "", email: "", phone: "", location: "" },
    education: [],
    experience: [],
    skills: [],
    certifications: [],
    languages: [],
    projects: [],
  });

  useEffect(() => {
    if (profile?.extractedProfile) {
      setExtractedData(profile.extractedProfile);
      setEditForm(profile.extractedProfile);
    }
  }, [profile]);

  function openEditModal() {
    if (extractedData) {
      setEditForm(JSON.parse(JSON.stringify(extractedData)));
    }
    setIsEditing(true);
  }

  async function handleSaveProfile() {
    setSaving(true);
    setSaveSuccessMsg(null);
    try {
      const resumeId = profile?.resumeId || "active";
      const res = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          profile: editForm,
          resumeCategory: "Information-Technology",
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to save updated profile to backend.");
      }

      const resData = await res.json();
      const updatedProfile = resData.data?.profile || editForm;

      setExtractedData(updatedProfile);
      if (profile) {
        saveProfile({
          ...profile,
          extractedProfile: updatedProfile,
        });
      }

      setSaveSuccessMsg("Profile saved successfully to MongoDB!");
      setTimeout(() => {
        setIsEditing(false);
        setSaveSuccessMsg(null);
      }, 1000);
    } catch (err: any) {
      alert(err.message || "Error saving profile.");
    } finally {
      setSaving(false);
    }
  }

  // Display skills fallback
  const displaySkills =
    extractedData?.skills && extractedData.skills.length > 0
      ? extractedData.skills
      : extractedSkills.map((s) => s.name);

  return (
    <main className="hero-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <Link to="/" className="text-sm text-muted-foreground hover:text-primary">
          ← Back to resume upload
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
            <p className="mt-2 text-muted-foreground">
              Based on {profile?.resumeName ?? "Resume.pdf"} · Parsed with Hugging Face{" "}
              <span className="font-semibold text-primary">oksomu/resume-ner</span>
            </p>
          </div>
          <ReadinessRing value={readiness} role={role} />
        </div>

        {/* Extracted Personal Info Card */}
        {extractedData?.personal && (
          <div className="panel mt-8 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold tracking-widest text-muted-foreground uppercase flex items-center gap-2">
                <FileText className="size-4 text-primary" /> Extracted Candidate Profile
              </h2>
              <Button size="xs" variant="ghost" onClick={openEditModal} className="text-xs text-primary">
                <Edit3 className="size-3.5 mr-1" /> Edit
              </Button>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <span className="text-xs text-muted-foreground">Full Name</span>
                <p className="font-medium text-foreground">{extractedData.personal.name || "N/A"}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Email</span>
                <p className="font-medium text-foreground">{extractedData.personal.email || "N/A"}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Phone</span>
                <p className="font-medium text-foreground">{extractedData.personal.phone || "N/A"}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Location</span>
                <p className="font-medium text-foreground">{extractedData.personal.location || "N/A"}</p>
              </div>
            </div>
          </div>
        )}

        {/* Profile Summary */}
        <Panel className="mt-6" title="Profile Summary" icon={<Sparkles className="size-4" />}>
          <p className="text-lg leading-relaxed text-foreground/90">{profileSummary}</p>
        </Panel>

        {/* Extracted Education & Experience Grid */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Education */}
          <Panel title="Education & Academic Scores" icon={<GraduationCap className="size-4" />}>
            {extractedData?.education && extractedData.education.length > 0 ? (
              <div className="space-y-4">
                {extractedData.education.map((edu, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-surface-2/60 p-4">
                    <p className="font-semibold text-base">{edu.degree} {edu.field ? `in ${edu.field}` : ""}</p>
                    <p className="text-sm text-muted-foreground">{edu.institution || "University"}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                      {(edu.startDate || edu.endDate) && (
                        <span>{edu.startDate || ""} - {edu.endDate || ""}</span>
                      )}
                      {edu.cgpa != null && (
                        <Badge variant="secondary" className="bg-primary/15 text-primary border-primary/30">
                          CGPA: {edu.cgpa}
                        </Badge>
                      )}
                      {edu.sgpa != null && (
                        <Badge variant="secondary" className="bg-accent/15 text-accent border-accent/30">
                          SGPA: {edu.sgpa}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No specific education details extracted.</p>
            )}
          </Panel>

          {/* Experience */}
          <Panel title="Work Experience" icon={<Briefcase className="size-4" />}>
            {extractedData?.experience && extractedData.experience.length > 0 ? (
              <div className="space-y-4">
                {extractedData.experience.map((exp, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-surface-2/60 p-4">
                    <p className="font-semibold text-base">{exp.title || "Position"}</p>
                    <p className="text-sm text-primary">{exp.company || "Company"}</p>
                    {exp.duration && <p className="mt-1 text-xs text-muted-foreground">{exp.duration}</p>}
                    {exp.description && <p className="mt-2 text-xs leading-relaxed text-foreground/90">{exp.description}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No work experience entries detected.</p>
            )}
          </Panel>
        </div>

        {/* Skills & Projects */}
        <div className="mt-6 grid gap-6 lg:grid-cols-5">
          <Panel className="lg:col-span-3" title="Extracted Skills (Hugging Face NER)">
            <div className="flex flex-wrap gap-2">
              {displaySkills.map((skill, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="rounded-lg border-primary/30 bg-primary/10 px-3 py-1.5 text-sm font-medium text-foreground hover:border-primary"
                >
                  {skill}
                </Badge>
              ))}
            </div>

            <div className="mt-6 space-y-4">
              <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
                Role Proficiency Estimation
              </p>
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

          <Panel className="lg:col-span-2" title="Extracted Projects & Portfolio" icon={<FolderGit2 className="size-4" />}>
            {extractedData?.projects && extractedData.projects.length > 0 ? (
              <ul className="space-y-3">
                {extractedData.projects.map((p, idx) => (
                  <li key={idx} className="rounded-xl border border-border bg-surface-2/60 p-3.5">
                    <div className="flex items-start gap-2.5">
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                      <div>
                        <p className="text-sm font-medium">{p.name}</p>
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
              <ul className="space-y-3">
                {portfolioProjects.map((p) => (
                  <li key={p.title} className="flex items-start gap-3 rounded-xl border border-border bg-surface-2/60 p-3">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                    <div>
                      <p className="text-sm font-medium">{p.title}</p>
                      <p className="text-xs text-muted-foreground">{p.stack}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-4 rounded-xl border border-accent/30 bg-accent/10 p-4">
              <p className="text-xs font-semibold tracking-widest text-accent uppercase">
                AI feedback
              </p>
              <p className="mt-2 text-sm text-foreground/90">{portfolioFeedback}</p>
            </div>
          </Panel>
        </div>

        {/* Certifications & Languages */}
        {((extractedData?.certifications && extractedData.certifications.length > 0) ||
          (extractedData?.languages && extractedData.languages.length > 0)) && (
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            {extractedData?.certifications && extractedData.certifications.length > 0 && (
              <Panel title="Certifications" icon={<Award className="size-4" />}>
                <div className="flex flex-wrap gap-2">
                  {extractedData.certifications.map((cert, idx) => (
                    <Badge key={idx} variant="secondary" className="bg-surface-2 text-foreground border-border">
                      {cert}
                    </Badge>
                  ))}
                </div>
              </Panel>
            )}
            {extractedData?.languages && extractedData.languages.length > 0 && (
              <Panel title="Languages" icon={<Globe className="size-4" />}>
                <div className="flex flex-wrap gap-2">
                  {extractedData.languages.map((lang, idx) => (
                    <Badge key={idx} variant="outline" className="border-primary/40 text-primary">
                      {lang}
                    </Badge>
                  ))}
                </div>
              </Panel>
            )}
          </div>
        )}

        {/* Skill Gap */}
        <Panel className="mt-6" title="Skill Gap" icon={<AlertTriangle className="size-4" />}>
          <div className="grid gap-4 sm:grid-cols-3">
            <GapCard tone="success" title="Strong Skills" items={skillGap.strong} mark="✓" />
            <GapCard tone="warning" title="Needs Improvement" items={skillGap.improve} mark="⚠" />
            <GapCard tone="danger" title="Critical Gaps" items={skillGap.critical} mark="●" />
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

      {/* Edit Profile Modal */}
      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent className="max-h-[85vh] overflow-y-auto max-w-3xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <Edit3 className="size-5 text-primary" /> Edit Extracted Profile
            </DialogTitle>
          </DialogHeader>

          {saveSuccessMsg && (
            <div className="rounded-lg bg-success/15 p-3 text-sm text-success font-medium">
              {saveSuccessMsg}
            </div>
          )}

          <div className="space-y-6 py-4">
            {/* Personal Details */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
                Personal Information
              </h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="edit-name">Full Name</Label>
                  <Input
                    id="edit-name"
                    value={editForm.personal?.name || ""}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        personal: { ...prev.personal, name: e.target.value },
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="edit-email">Email</Label>
                  <Input
                    id="edit-email"
                    value={editForm.personal?.email || ""}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        personal: { ...prev.personal, email: e.target.value },
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="edit-phone">Phone</Label>
                  <Input
                    id="edit-phone"
                    value={editForm.personal?.phone || ""}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        personal: { ...prev.personal, phone: e.target.value },
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="edit-location">Location</Label>
                  <Input
                    id="edit-location"
                    value={editForm.personal?.location || ""}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        personal: { ...prev.personal, location: e.target.value },
                      }))
                    }
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
                Skills (Comma Separated)
              </h3>
              <Textarea
                rows={2}
                value={(editForm.skills || []).join(", ")}
                onChange={(e) =>
                  setEditForm((prev) => ({
                    ...prev,
                    skills: e.target.value
                      .split(",")
                      .map((s) => s.strip ? s.trim() : s)
                      .filter(Boolean),
                  }))
                }
              />
            </div>

            {/* Education */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
                  Education Entries
                </h3>
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() =>
                    setEditForm((prev) => ({
                      ...prev,
                      education: [
                        ...(prev.education || []),
                        { degree: "", field: "", institution: "", cgpa: null, sgpa: null },
                      ],
                    }))
                  }
                  className="text-xs text-primary"
                >
                  <Plus className="size-3.5 mr-1" /> Add Education
                </Button>
              </div>

              {(editForm.education || []).map((edu, idx) => (
                <div key={idx} className="relative rounded-xl border border-border bg-surface-2/40 p-4 space-y-3">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      setEditForm((prev) => ({
                        ...prev,
                        education: prev.education?.filter((_, i) => i !== idx),
                      }))
                    }
                    className="absolute top-2 right-2 text-muted-foreground hover:text-destructive size-7"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <Label>Degree</Label>
                      <Input
                        value={edu.degree || ""}
                        onChange={(e) => {
                          const updated = [...(editForm.education || [])];
                          updated[idx].degree = e.target.value;
                          setEditForm({ ...editForm, education: updated });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Field of Study</Label>
                      <Input
                        value={edu.field || ""}
                        onChange={(e) => {
                          const updated = [...(editForm.education || [])];
                          updated[idx].field = e.target.value;
                          setEditForm({ ...editForm, education: updated });
                        }}
                      />
                    </div>
                    <div>
                      <Label>Institution</Label>
                      <Input
                        value={edu.institution || ""}
                        onChange={(e) => {
                          const updated = [...(editForm.education || [])];
                          updated[idx].institution = e.target.value;
                          setEditForm({ ...editForm, education: updated });
                        }}
                      />
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <Label>CGPA</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={edu.cgpa ?? ""}
                        onChange={(e) => {
                          const updated = [...(editForm.education || [])];
                          updated[idx].cgpa = e.target.value ? parseFloat(e.target.value) : null;
                          setEditForm({ ...editForm, education: updated });
                        }}
                      />
                    </div>
                    <div>
                      <Label>SGPA</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={edu.sgpa ?? ""}
                        onChange={(e) => {
                          const updated = [...(editForm.education || [])];
                          updated[idx].sgpa = e.target.value ? parseFloat(e.target.value) : null;
                          setEditForm({ ...editForm, education: updated });
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Projects */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
                  Projects
                </h3>
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() =>
                    setEditForm((prev) => ({
                      ...prev,
                      projects: [
                        ...(prev.projects || []),
                        { name: "", description: "", technologies: [] },
                      ],
                    }))
                  }
                  className="text-xs text-primary"
                >
                  <Plus className="size-3.5 mr-1" /> Add Project
                </Button>
              </div>

              {(editForm.projects || []).map((proj, idx) => (
                <div key={idx} className="relative rounded-xl border border-border bg-surface-2/40 p-4 space-y-3">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      setEditForm((prev) => ({
                        ...prev,
                        projects: prev.projects?.filter((_, i) => i !== idx),
                      }))
                    }
                    className="absolute top-2 right-2 text-muted-foreground hover:text-destructive size-7"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                  <div>
                    <Label>Project Name</Label>
                    <Input
                      value={proj.name || ""}
                      onChange={(e) => {
                        const updated = [...(editForm.projects || [])];
                        updated[idx].name = e.target.value;
                        setEditForm({ ...editForm, projects: updated });
                      }}
                    />
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Textarea
                      rows={2}
                      value={proj.description || ""}
                      onChange={(e) => {
                        const updated = [...(editForm.projects || [])];
                        updated[idx].description = e.target.value;
                        setEditForm({ ...editForm, projects: updated });
                      }}
                    />
                  </div>
                  <div>
                    <Label>Technologies (Comma Separated)</Label>
                    <Input
                      value={(proj.technologies || []).join(", ")}
                      onChange={(e) => {
                        const updated = [...(editForm.projects || [])];
                        updated[idx].technologies = e.target.value
                          .split(",")
                          .map((t) => t.trim())
                          .filter(Boolean);
                        setEditForm({ ...editForm, projects: updated });
                      }}
                    />
                  </div>
                </div>
              ))}
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
                {saving ? "Saving to MongoDB..." : "Save Profile to MongoDB"}
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
