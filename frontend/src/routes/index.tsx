import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import {
  BrainCircuit,
  FileText,
  Github,
  Loader2,
  Sparkles,
  Target,
  Trash2,
  UploadCloud,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ROLE_DESCRIPTIONS, TARGET_ROLES, type TargetRole } from "@/lib/mock-data";
import { clearProfile, formatBytes, saveProfile } from "@/lib/profile-store";
import { getSession } from "@/lib/auth-store";

import { RequireAuth } from "@/components/auth/require-auth";

const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SkillForge AI — Your AI-Powered Career Mentor" },
      {
        name: "description",
        content:
          "Upload your resume, share your portfolio, and discover exactly what to learn next to become job-ready.",
      },
      { property: "og:title", content: "SkillForge AI — Your AI Career Mentor" },
      {
        property: "og:description",
        content:
          "Resume + portfolio analysis, skill gap detection and a personalized learning roadmap.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <Index />
    </RequireAuth>
  ),
});

const LOADING_STEPS = [
  "Parsing candidate resume (PDF/DOCX/TXT)…",
  "Scraping & analyzing developer portfolio URL…",
  "Unifying Resume + Portfolio into a single student profile…",
  "Comparing profile against target role requirements & skill gaps…",
  "Generating personalized roadmap & AI career recommendations…",
];

function Index() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileMeta, setFileMeta] = useState<{ name: string; size: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [portfolio, setPortfolio] = useState("");
  const [role, setRole] = useState<string>("AI/ML Engineer");
  const [loadingStep, setLoadingStep] = useState(-1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const analyzing = loadingStep >= 0;
  const trimmedPortfolio = portfolio.trim();
  const hasPortfolio = Boolean(trimmedPortfolio);
  const portfolioValid = !hasPortfolio || /^https?:\/\/[^\s]+$/i.test(trimmedPortfolio);
  const buttonText = "Create My Career Analysis";
  const roleDescription = ROLE_DESCRIPTIONS[role as TargetRole];

  function pick(f: File | undefined | null) {
    if (!f) return;
    setErrorMsg(null);
    setFile(f);
    setFileMeta({ name: f.name, size: f.size });
  }

  async function analyze() {
    setErrorMsg(null);

    const hasFile = Boolean(file);
    if (!hasFile && !hasPortfolio) {
      setErrorMsg("Please upload a resume file OR provide a Portfolio/GitHub URL to run career analysis.");
      return;
    }
    if (!portfolioValid) {
      setErrorMsg("Please enter a valid portfolio URL starting with http:// or https://.");
      return;
    }

    clearProfile();
    setLoadingStep(0);

    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => (prev < LOADING_STEPS.length - 1 ? prev + 1 : prev));
    }, 700);

    try {
      const formData = new FormData();
      if (file) {
        formData.append("file", file);
      }
      if (hasPortfolio) {
        formData.append("portfolio_url", portfolio.trim());
      }
      formData.append("target_role", role);

      const headers: Record<string, string> = {};
      const session = getSession();
      if (session?.id) {
        headers["X-User-ID"] = session.id;
      }

      const res = await fetch(`${API_BASE_URL}/api/career-profiles/analyze`, {
        method: "POST",
        headers,
        body: formData,
        credentials: "include",
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to execute career analysis pipeline on backend.");
      }

      const responseJson = await res.json();
      clearInterval(stepInterval);
      setLoadingStep(LOADING_STEPS.length - 1);

      if (responseJson.success && responseJson.data) {
        const pipelineData = responseJson.data;

        // Persist complete backend unified profile & recommendations
        saveProfile({
          resumeId: pipelineData.resumeId,
          portfolioId: pipelineData.portfolioId,
          resumeName: fileMeta?.name,
          resumeSize: fileMeta?.size,
          portfolio: hasPortfolio ? trimmedPortfolio : undefined,
          role: role,
          unifiedProfile: pipelineData.unifiedProfile,
          careerProfile: pipelineData.careerProfile,
          learningPath: pipelineData.learningPath,
          progress: pipelineData.progress,
        });

        setTimeout(() => navigate({ to: "/analysis" }), 400);
      } else {
        throw new Error(responseJson.message || "Failed to parse analysis output.");
      }
    } catch (err: any) {
      clearInterval(stepInterval);
      setLoadingStep(-1);
      setErrorMsg(err.message || "An error occurred while analyzing your career profile.");
    }
  }

  return (
    <main className="hero-glow min-h-screen">
      <div className="mx-auto max-w-5xl px-5 pt-14 pb-20 sm:pt-20">
        <header className="text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            <Sparkles className="size-3.5 text-primary" />
            AI Career Mentor
          </span>
          <h1 className="mt-6 text-5xl font-bold sm:text-7xl">
            <span className="text-gradient">SkillForge AI</span>
          </h1>
          <p className="mt-3 font-display text-xl text-foreground/90 sm:text-2xl">
            Your AI-powered career mentor
          </p>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground">
            Start with your resume and a public portfolio link. We turn your real work into a focused career plan.
          </p>
        </header>

        <section className="panel mt-12 p-6 sm:p-9">
          {errorMsg && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-destructive">
              <AlertCircle className="mt-0.5 size-5 shrink-0" />
              <div className="text-sm">
                <p className="font-semibold">Analysis Pipeline Error</p>
                <p className="mt-1 opacity-90">{errorMsg}</p>
              </div>
            </div>
          )}

          <div className="mb-7 text-center">
            <p className="text-sm font-semibold text-primary">Your career profile starts here</p>
            <p className="mt-1 text-sm text-muted-foreground">Add your resume, portfolio, or both. Each source makes your result stronger.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-border bg-surface/60 p-5">
              <SectionLabel icon={<FileText className="size-4" />} text="Upload Your Resume" />
              <p className="mt-3 text-sm text-muted-foreground">Upload your PDF, DOCX or TXT resume. Optional.</p>
              {fileMeta ? (
                <div className="mt-3 flex items-center justify-between gap-4 rounded-xl border border-primary/40 bg-surface-2 p-4">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-primary/15 text-primary">
                      <FileText className="size-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{fileMeta.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatBytes(fileMeta.size)} · {fileMeta.name.split(".").pop()?.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFile(null);
                      setFileMeta(null);
                    }}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="size-4" />
                    Remove
                  </Button>
                </div>
              ) : (
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragging(false);
                    pick(e.dataTransfer.files?.[0]);
                  }}
                  onClick={() => inputRef.current?.click()}
                  className={`mt-3 cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
                    dragging
                      ? "border-primary bg-primary/10"
                      : "border-border bg-surface-2/60 hover:border-primary/50"
                  }`}
                >
                  <UploadCloud className="mx-auto size-8 text-primary" />
                  <p className="mt-3 text-sm font-medium">Drag & drop your resume file here</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    PDF, DOCX, or TXT · max 10 MB
                  </p>
                  <Button type="button" variant="secondary" size="sm" className="mt-4">
                    Upload Resume
                  </Button>
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    className="hidden"
                    onChange={(e) => pick(e.target.files?.[0])}
                  />
                </div>
              )}
            </div>
            <div className="rounded-xl border border-border bg-surface/60 p-5">
              <SectionLabel icon={<Github className="size-4" />} text="Add Your Portfolio" />
              <p className="mt-3 text-sm text-muted-foreground">GitHub or a personal portfolio link. We read public project pages, descriptions, and listed technologies.</p>
              <Label htmlFor="portfolio" className="mt-4 mb-2 block text-xs text-muted-foreground">
                Portfolio URL
              </Label>
              <Input
                id="portfolio"
                value={portfolio}
                onChange={(e) => setPortfolio(e.target.value)}
                placeholder="https://github.com/username"
                className="bg-surface-2"
              />
              <p className={`mt-2 text-xs ${portfolioValid ? "text-muted-foreground" : "text-destructive"}`}>
                {hasPortfolio ? (portfolioValid ? "Valid URL" : "Enter a valid http:// or https:// URL") : "Example: https://github.com/username"}
              </p>
            </div>

            <div className="md:col-span-2">
              <SectionLabel icon={<Target className="size-4" />} text="Target Career" />
              <Label className="mt-3 mb-2 block text-xs text-muted-foreground">
                Which role are you aiming for?
              </Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger className="w-full bg-surface-2">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  {TARGET_ROLES.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="mt-3 rounded-lg border border-primary/20 bg-primary/8 p-3 text-sm leading-relaxed text-foreground/85">
                <span className="font-semibold text-primary">What this role does: </span>{roleDescription}
              </p>
            </div>
          </div>

          <Button
            size="lg"
            onClick={analyze}
            disabled={analyzing || (!file && !hasPortfolio) || !portfolioValid}
            className="glow mt-9 h-13 w-full bg-gradient-accent text-base font-semibold text-primary-foreground hover:opacity-90"
          >
            {analyzing ? (
              <>
                <Loader2 className="size-5 animate-spin" />
                Analyzing Career Profile with Gemini AI…
              </>
            ) : (
              <>
                <BrainCircuit className="size-5" />
                {buttonText}
              </>
            )}
          </Button>

          {analyzing && (
            <ul className="mt-6 space-y-2">
              {LOADING_STEPS.map((step, i) => (
                <li
                  key={step}
                  className={`flex items-center gap-2 text-sm transition-opacity ${
                    i <= loadingStep ? "text-foreground" : "text-muted-foreground/50"
                  }`}
                >
                  {i < loadingStep ? (
                    <span className="text-success">✓</span>
                  ) : i === loadingStep ? (
                    <Loader2 className="size-3.5 animate-spin text-primary" />
                  ) : (
                    <span className="size-3.5" />
                  )}
                  {step}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mt-14 grid gap-4 sm:grid-cols-3">
          {[
            {
              t: "Unified Student Profile",
              d: "Merges Resume text and Portfolio web scraping into a single deduplicated candidate profile.",
            },
            {
              t: "Deterministic & AI Gap Analysis",
              d: "Compares your skills against actual target role requirements and calculates readiness score.",
            },
            {
              t: "Personalized Action Roadmap",
              d: "Generates custom learning paths, courses, hands-on projects, and interview questions.",
            },
          ].map((f) => (
            <div key={f.t} className="rounded-xl border border-border bg-surface/70 p-5">
              <h3 className="font-display text-base font-semibold">{f.t}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.d}</p>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}

function SectionLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 border-b border-border pb-2 text-xs font-semibold tracking-widest text-muted-foreground uppercase">
      <span className="text-primary">{icon}</span>
      {text}
    </div>
  );
}
