import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import {
  BrainCircuit,
  FileText,
  Github,
  Linkedin,
  Loader2,
  Sparkles,
  Target,
  Trash2,
  UploadCloud,
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
import { TARGET_ROLES } from "@/lib/mock-data";
import { formatBytes, saveProfile } from "@/lib/profile-store";

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
  component: Index,
});

const LOADING_STEPS = [
  "Parsing your resume…",
  "Scanning your portfolio repositories…",
  "Extracting skills & proficiency…",
  "Comparing against role requirements…",
  "Building your personalized plan…",
];

function Index() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<{ name: string; size: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [portfolio, setPortfolio] = useState("https://github.com/student");
  const [linkedin, setLinkedin] = useState("");
  const [role, setRole] = useState<string>("AI/ML Engineer");
  const [loadingStep, setLoadingStep] = useState(-1);

  const analyzing = loadingStep >= 0;

  function pick(f: File | undefined | null) {
    if (!f) return;
    setFile({ name: f.name, size: f.size });
  }

  function analyze() {
    saveProfile({
      resumeName: file?.name ?? "Resume.pdf",
      resumeSize: file?.size ?? 184320,
      portfolio,
      linkedin,
      role,
    });
    setLoadingStep(0);
    LOADING_STEPS.forEach((_, i) => {
      setTimeout(() => setLoadingStep(i), i * 650);
    });
    setTimeout(() => navigate({ to: "/analysis" }), LOADING_STEPS.length * 650);
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
            Upload your resume, share your portfolio, and discover exactly what you should
            learn next to become job-ready.
          </p>
        </header>

        <section className="panel mt-12 p-6 sm:p-9">
          <div className="grid gap-8 md:grid-cols-2">
            <div className="md:col-span-2">
              <SectionLabel icon={<FileText className="size-4" />} text="Resume" />
              {file ? (
                <div className="mt-3 flex items-center justify-between gap-4 rounded-xl border border-primary/40 bg-surface-2 p-4">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-primary/15 text-primary">
                      <FileText className="size-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatBytes(file.size)} · PDF
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFile(null)}
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
                  <p className="mt-3 text-sm font-medium">Drag & drop your PDF here</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    PDF only · max 5 MB
                  </p>
                  <Button type="button" variant="secondary" size="sm" className="mt-4">
                    Upload Resume
                  </Button>
                  <input
                    ref={inputRef}
                    type="file"
                    accept="application/pdf"
                    className="hidden"
                    onChange={(e) => pick(e.target.files?.[0])}
                  />
                </div>
              )}
            </div>

            <div>
              <SectionLabel icon={<Github className="size-4" />} text="Portfolio" />
              <Label htmlFor="portfolio" className="mt-3 mb-2 block text-xs text-muted-foreground">
                GitHub / Portfolio URL
              </Label>
              <Input
                id="portfolio"
                value={portfolio}
                onChange={(e) => setPortfolio(e.target.value)}
                placeholder="https://github.com/username"
                className="bg-surface-2"
              />
              <Label htmlFor="linkedin" className="mt-4 mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                <Linkedin className="size-3.5" /> LinkedIn URL (optional)
              </Label>
              <Input
                id="linkedin"
                value={linkedin}
                onChange={(e) => setLinkedin(e.target.value)}
                placeholder="https://linkedin.com/in/username"
                className="bg-surface-2"
              />
            </div>

            <div>
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
              <p className="mt-4 rounded-lg border border-border bg-surface-2/60 p-3 text-xs leading-relaxed text-muted-foreground">
                We compare your extracted skills against the market requirements for{" "}
                <span className="text-primary">{role}</span> to detect your gaps.
              </p>
            </div>
          </div>

          <Button
            size="lg"
            onClick={analyze}
            disabled={analyzing}
            className="glow mt-9 h-13 w-full bg-gradient-accent text-base font-semibold text-primary-foreground hover:opacity-90"
          >
            {analyzing ? (
              <>
                <Loader2 className="size-5 animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                <BrainCircuit className="size-5" />
                Analyze My Career
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
              t: "Profile Analysis",
              d: "Resume + portfolio parsed into a real skill profile with proficiency scores.",
            },
            {
              t: "Skill Gap Detection",
              d: "Your level compared against what the role actually requires today.",
            },
            {
              t: "Personalized Plan",
              d: "Roadmap, courses, projects, certifications and interview prep.",
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
