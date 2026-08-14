import { useState, useEffect } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Brain,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Zap,
  Target,
  FileText,
  FolderGit2,
  Layers,
  Award,
  ChevronRight,
  Moon,
  Sun,
  LogOut,
  User,
  Check,
  Cpu,
  BarChart3,
  BookOpen,
  ArrowUpRight,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth, signOut } from "@/lib/auth-store";

export function LandingPage() {
  const { user, ready } = useAuth();
  const navigate = useNavigate();

  // CTA navigation handler: authenticated -> /analysis, unauthenticated -> /auth
  const handleAuthAction = () => {
    if (user) {
      navigate({ to: "/analysis" });
    } else {
      navigate({ to: "/auth" });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* 1. Header / Navbar */}
      <LandingNavbar user={user} ready={ready} onCtaClick={handleAuthAction} />

      {/* 2. Hero Section */}
      <LandingHero user={user} onCtaClick={handleAuthAction} />

      {/* 3. Product Flow / How It Works */}
      <HowItWorksSection onCtaClick={handleAuthAction} />

      {/* 4. Live Interactive Analysis Preview */}
      <AnalysisPreviewSection onCtaClick={handleAuthAction} />

      {/* 5. Features Grid */}
      <FeaturesGridSection />

      {/* 6. Comparison Section */}
      <ComparisonSection onCtaClick={handleAuthAction} />

      {/* 7. Bottom CTA */}
      <BottomCtaSection onCtaClick={handleAuthAction} />

      {/* 8. Footer */}
      <LandingFooter onCtaClick={handleAuthAction} />
    </div>
  );
}

/* ==========================================================================
   1. NAVBAR COMPONENT
   ========================================================================== */
function LandingNavbar({
  user,
  ready,
  onCtaClick,
}: {
  user: ReturnType<typeof useAuth>["user"];
  ready: boolean;
  onCtaClick: () => void;
}) {
  const navigate = useNavigate();
  const [light, setLight] = useState(
    () => typeof window !== "undefined" && localStorage.getItem("skillforge-theme") === "light",
  );
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const toggleTheme = () => {
    const next = !light;
    setLight(next);
    document.documentElement.classList.toggle("light", next);
    localStorage.setItem("skillforge-theme", next ? "light" : "dark");
  };

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-background/80 backdrop-blur-md border-b border-border shadow-md"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5 font-display text-xl font-bold tracking-tight text-foreground group">
          <div className="grid size-9 place-items-center rounded-xl bg-primary/15 text-primary border border-primary/30 transition-transform group-hover:scale-105 group-hover:bg-primary/25">
            <Brain className="size-5" />
          </div>
          <span>
            Skill<span className="text-primary">Forge</span> AI
          </span>
        </Link>

        {/* Desktop Nav Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <a href="#how-it-works" className="transition-colors hover:text-foreground">
            How It Works
          </a>
          <a href="#preview" className="transition-colors hover:text-foreground">
            Analysis Preview
          </a>
          <a href="#features" className="transition-colors hover:text-foreground">
            Features
          </a>
          <a href="#why-us" className="transition-colors hover:text-foreground">
            Why SkillForge
          </a>
        </nav>

        {/* Right Action buttons */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <button
            type="button"
            aria-label="Toggle light and dark theme"
            onClick={toggleTheme}
            className="grid size-9 place-items-center rounded-xl border border-border bg-surface text-muted-foreground transition-colors hover:text-foreground hover:bg-surface-2"
          >
            {light ? <Moon className="size-4" /> : <Sun className="size-4" />}
          </button>

          {ready && user ? (
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs text-muted-foreground bg-surface border border-border px-3 py-1.5 rounded-full">
                <User className="size-3 text-primary" />
                {user.email}
              </span>
              <Button
                onClick={() => navigate({ to: "/analysis" })}
                size="sm"
                className="bg-gradient-accent glow text-primary-foreground font-semibold text-xs rounded-xl"
              >
                Go to Analysis
                <ArrowRight className="size-3.5 ml-1" />
              </Button>
              <button
                type="button"
                onClick={async () => {
                  await signOut();
                  navigate({ to: "/auth" });
                }}
                className="grid size-9 place-items-center rounded-xl border border-border bg-surface text-muted-foreground transition-colors hover:text-destructive hover:bg-surface-2"
                title="Logout"
              >
                <LogOut className="size-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={onCtaClick}
                className="text-muted-foreground hover:text-foreground text-xs sm:text-sm font-medium"
              >
                Sign In
              </Button>
              <Button
                size="sm"
                onClick={onCtaClick}
                className="bg-gradient-accent glow text-primary-foreground font-semibold text-xs sm:text-sm rounded-xl px-4"
              >
                Get Started
                <ArrowRight className="size-3.5 ml-1" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

/* ==========================================================================
   2. HERO SECTION
   ========================================================================== */
function LandingHero({
  user,
  onCtaClick,
}: {
  user: ReturnType<typeof useAuth>["user"];
  onCtaClick: () => void;
}) {
  return (
    <section className="hero-glow relative pt-12 pb-20 sm:pt-20 sm:pb-28 overflow-hidden">
      <div className="mx-auto max-w-6xl px-5 text-center relative z-10">
        {/* Pill Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-semibold tracking-wide text-primary mb-6 shadow-sm">
          <Sparkles className="size-3.5" />
          <span>AI-Powered Career Intelligence</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight max-w-4xl mx-auto leading-[1.1]">
          Build the career you are{" "}
          <span className="text-gradient">meant for</span>.
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-base sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          SkillForge AI analyzes your resume, GitHub portfolio, and real projects to pinpoint your exact skill gaps and forge your customized week-by-week path to job readiness.
        </p>

        {/* CTAs */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Button
            size="lg"
            onClick={onCtaClick}
            className="bg-gradient-accent glow text-primary-foreground font-semibold text-base h-13 px-8 rounded-xl transition-transform hover:-translate-y-0.5"
          >
            {user ? "Continue to Analysis" : "Build My Career Plan"}
            <ArrowRight className="size-5 ml-2" />
          </Button>

          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center rounded-xl border border-border bg-surface px-6 h-13 text-sm font-semibold text-foreground transition-all hover:bg-surface-2 hover:border-primary/40"
          >
            See How It Works
            <ChevronRight className="size-4 ml-1 text-muted-foreground" />
          </a>
        </div>

        {/* Trust Badges / Stats */}
        <div className="mt-14 pt-8 border-t border-border/60 max-w-3xl mx-auto grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-foreground">100%</p>
            <p className="text-xs text-muted-foreground mt-1">Data-Driven Gap Detection</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-primary">Zero</p>
            <p className="text-xs text-muted-foreground mt-1">Generic Advice</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-foreground">5-Step</p>
            <p className="text-xs text-muted-foreground mt-1">AI Pipeline Execution</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   3. PRODUCT FLOW / HOW IT WORKS
   ========================================================================== */
function HowItWorksSection({ onCtaClick }: { onCtaClick: () => void }) {
  const steps = [
    {
      num: "01",
      title: "Upload Resume & Portfolio",
      desc: "Provide your resume file and public GitHub/portfolio URL. We automatically extract experience and projects.",
      icon: <FileText className="size-5 text-primary" />,
    },
    {
      num: "02",
      title: "AI Skill Extraction",
      desc: "Gemini parses tech stacks, languages, libraries, and real-world project complexity into a unified profile.",
      icon: <Cpu className="size-5 text-primary" />,
    },
    {
      num: "03",
      title: "Target Role Gap Analysis",
      desc: "We benchmark your verified skills against industry requirements to uncover high-impact gaps.",
      icon: <Target className="size-5 text-primary" />,
    },
    {
      num: "04",
      title: "Personalized Roadmap",
      desc: "Receive structured weekly milestones with curated courses, practical projects, and interview questions.",
      icon: <TrendingUp className="size-5 text-primary" />,
    },
  ];

  return (
    <section id="how-it-works" className="py-20 bg-surface/30 border-y border-border">
      <div className="mx-auto max-w-6xl px-5">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <Badge variant="outline" className="border-primary/40 text-primary bg-primary/5 px-3 py-1 mb-3">
            Workflow
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold">
            From your experience to your <span className="text-gradient">next opportunity</span>
          </h2>
          <p className="mt-3 text-muted-foreground text-sm sm:text-base">
            A deterministic, AI-guided system that bridges the distance between where you are and where you want to be.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-4 sm:grid-cols-2">
          {steps.map((s, idx) => (
            <div
              key={s.num}
              className="panel relative p-6 flex flex-col justify-between transition-transform hover:-translate-y-1 hover:border-primary/50 group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-display text-2xl font-bold text-primary/40 group-hover:text-primary transition-colors">
                    {s.num}
                  </span>
                  <div className="grid size-10 place-items-center rounded-xl bg-primary/10 border border-primary/20">
                    {s.icon}
                  </div>
                </div>
                <h3 className="font-display font-semibold text-lg text-foreground mb-2">
                  {s.title}
                </h3>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  {s.desc}
                </p>
              </div>

              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                  <div className="grid size-6 place-items-center rounded-full bg-surface-2 border border-border text-muted-foreground">
                    <ChevronRight className="size-3.5" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Button
            onClick={onCtaClick}
            className="bg-gradient-accent glow text-primary-foreground font-semibold rounded-xl px-6"
          >
            Start Your Free Analysis
            <ArrowRight className="size-4 ml-2" />
          </Button>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   4. LIVE INTERACTIVE ANALYSIS PREVIEW
   ========================================================================== */
function AnalysisPreviewSection({ onCtaClick }: { onCtaClick: () => void }) {
  return (
    <section id="preview" className="py-24">
      <div className="mx-auto max-w-6xl px-5">
        <div className="grid gap-12 lg:grid-cols-12 items-center">
          {/* Left Column: Value Description */}
          <div className="lg:col-span-5 space-y-6">
            <Badge variant="outline" className="border-primary/40 text-primary bg-primary/5 px-3 py-1">
              AI Insight Dashboard
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold leading-tight">
              Know <span className="text-gradient">exactly</span> where you stand before applying.
            </h2>
            <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
              Stop guessing which skills matter for job applications. SkillForge AI compares your real resume text and portfolio code against current hiring requirements.
            </p>

            <ul className="space-y-3 text-sm">
              {[
                "Target Role Career Readiness Score",
                "Automated Skill Gap Identification & Prioritization",
                "Project & Course Recommendations tailored to your gaps",
                "Editable Profile to refine experience & skills anytime",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-foreground/90">
                  <div className="grid size-5 place-items-center rounded-full bg-primary/20 text-primary shrink-0">
                    <Check className="size-3 font-bold" />
                  </div>
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className="pt-2">
              <Button
                onClick={onCtaClick}
                className="bg-gradient-accent glow text-primary-foreground font-semibold rounded-xl"
              >
                Analyze My Resume Now
                <ArrowUpRight className="size-4 ml-1.5" />
              </Button>
            </div>
          </div>

          {/* Right Column: Mock Interactive Dashboard Card */}
          <div className="lg:col-span-7">
            <div className="panel p-6 sm:p-8 bg-surface/90 border border-primary/30 glow relative overflow-hidden">
              {/* Card Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-5">
                <div>
                  <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                    Target Role Profile
                  </span>
                  <h3 className="font-display text-xl font-bold text-foreground">
                    AI/ML Engineer
                  </h3>
                </div>
                <div className="flex items-center gap-2 bg-primary/10 border border-primary/30 rounded-xl px-4 py-2">
                  <Sparkles className="size-4 text-primary" />
                  <span className="text-xs font-semibold text-primary">Readiness: 78%</span>
                </div>
              </div>

              {/* Skills Breakdown Grid */}
              <div className="mt-6 space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1.5">
                    <span className="text-foreground">Python &amp; PyTorch</span>
                    <span className="text-success font-semibold">92% Match</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                    <div className="h-full bg-success rounded-full" style={{ width: "92%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1.5">
                    <span className="text-foreground">LLMs, LangChain &amp; Transformers</span>
                    <span className="text-primary font-semibold">84% Match</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: "84%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1.5">
                    <span className="text-foreground">Vector Databases (ChromaDB / Pinecone)</span>
                    <span className="text-accent font-semibold">62% (Skill Gap)</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                    <div className="h-full bg-accent rounded-full" style={{ width: "62%" }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1.5">
                    <span className="text-foreground">Docker &amp; Cloud Deployment</span>
                    <span className="text-destructive font-semibold">45% (Priority Gap)</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
                    <div className="h-full bg-destructive rounded-full" style={{ width: "45%" }} />
                  </div>
                </div>
              </div>

              {/* Action Plan Preview */}
              <div className="mt-6 pt-5 border-t border-border">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Recommended Immediate Action
                </p>
                <div className="rounded-xl border border-border bg-surface-2 p-3.5 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="grid size-8 place-items-center rounded-lg bg-primary/20 text-primary shrink-0">
                      <BookOpen className="size-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-foreground">
                        Vector Embeddings &amp; Semantic Retrieval Project
                      </p>
                      <p className="text-[11px] text-muted-foreground">Estimated completion: 1 week</p>
                    </div>
                  </div>
                  <Badge className="bg-primary/20 text-primary border-primary/30 text-[10px]">
                    Week 1
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   5. FEATURES GRID SECTION
   ========================================================================== */
function FeaturesGridSection() {
  const features = [
    {
      title: "Unified Student Profile",
      desc: "Merges parsed resume text and portfolio GitHub repository data into one deduplicated candidate profile.",
      icon: <FolderGit2 className="size-6 text-primary" />,
    },
    {
      title: "AI Skill Gap Detection",
      desc: "Deterministic and embedding-based comparison against actual industry job requirements for high accuracy.",
      icon: <Target className="size-6 text-primary" />,
    },
    {
      title: "Dynamic Learning Roadmap",
      desc: "Structured, week-by-week checkpoints that focus solely on closing your identified gaps without wasting time.",
      icon: <Layers className="size-6 text-primary" />,
    },
    {
      title: "Hands-on Project Recommendations",
      desc: "Real-world portfolio-grade project suggestions to provide concrete proof-of-work to recruiters.",
      icon: <Zap className="size-6 text-primary" />,
    },
    {
      title: "Role-Specific Interview Prep",
      desc: "Tailored technical and behavioral question banks designed for the specific gaps you are strengthening.",
      icon: <ShieldCheck className="size-6 text-primary" />,
    },
    {
      title: "Interactive Progress Tracking",
      desc: "Check off milestones, complete courses, and watch your role readiness score climb towards 100%.",
      icon: <BarChart3 className="size-6 text-primary" />,
    },
  ];

  return (
    <section id="features" className="py-20 bg-surface/30 border-y border-border">
      <div className="mx-auto max-w-6xl px-5">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <Badge variant="outline" className="border-primary/40 text-primary bg-primary/5 px-3 py-1 mb-3">
            Key Capabilities
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold">
            Everything you need to <span className="text-gradient">accelerate</span> your career
          </h2>
          <p className="mt-3 text-muted-foreground text-sm sm:text-base">
            Built from the ground up to give candidates clear, personalized, actionable direction.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3 sm:grid-cols-2">
          {features.map((f) => (
            <div
              key={f.title}
              className="panel p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/50 hover:shadow-lg group"
            >
              <div className="grid size-12 place-items-center rounded-2xl bg-primary/10 border border-primary/20 mb-5 group-hover:bg-primary/20 transition-colors">
                {f.icon}
              </div>
              <h3 className="font-display font-semibold text-lg text-foreground mb-2">
                {f.title}
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   6. COMPARISON SECTION
   ========================================================================== */
function ComparisonSection({ onCtaClick }: { onCtaClick: () => void }) {
  return (
    <section id="why-us" className="py-20">
      <div className="mx-auto max-w-6xl px-5">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <Badge variant="outline" className="border-primary/40 text-primary bg-primary/5 px-3 py-1 mb-3">
            Why SkillForge AI
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-bold">
            Stop guessing what to <span className="text-gradient">learn next</span>
          </h2>
          <p className="mt-3 text-muted-foreground text-sm sm:text-base">
            Compare traditional generic approaches with SkillForge AI's targeted career mentor.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* Traditional */}
          <div className="panel p-6 sm:p-8 bg-surface/50 border-border opacity-85">
            <h3 className="font-display text-xl font-bold text-muted-foreground mb-4">
              Traditional Career Planning
            </h3>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li className="flex items-start gap-3">
                <span className="text-destructive font-bold">✕</span>
                <span>Generic 50-hour video tutorials covering things you already know</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-destructive font-bold">✕</span>
                <span>No visibility into which specific skills are blocking job offers</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-destructive font-bold">✕</span>
                <span>Cookie-cutter demo projects that don't stand out to recruiters</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-destructive font-bold">✕</span>
                <span>No structured feedback or readiness measurement</span>
              </li>
            </ul>
          </div>

          {/* SkillForge AI */}
          <div className="panel p-6 sm:p-8 border-primary/40 bg-surface/90 glow relative overflow-hidden">
            <div className="absolute top-3 right-4">
              <Badge className="bg-primary/20 text-primary border-primary/30 text-xs">
                Recommended
              </Badge>
            </div>
            <h3 className="font-display text-xl font-bold text-foreground mb-4">
              SkillForge AI Mentorship
            </h3>
            <ul className="space-y-4 text-sm text-foreground/90">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="size-5 text-primary shrink-0 mt-0.5" />
                <span>Custom curriculum built specifically for your verified gaps</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="size-5 text-primary shrink-0 mt-0.5" />
                <span>Accurate readiness score benchmarked against target roles</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="size-5 text-primary shrink-0 mt-0.5" />
                <span>Portfolio-grade projects with real implementation scope</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="size-5 text-primary shrink-0 mt-0.5" />
                <span>Interactive checkpoints and interview preparation</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   7. BOTTOM CTA
   ========================================================================== */
function BottomCtaSection({ onCtaClick }: { onCtaClick: () => void }) {
  return (
    <section className="py-16 bg-gradient-to-b from-surface/20 to-surface/60 border-t border-border">
      <div className="mx-auto max-w-4xl px-5 text-center">
        <div className="grid size-14 place-items-center rounded-2xl bg-primary/15 text-primary border border-primary/30 mx-auto mb-6">
          <Award className="size-7" />
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold tracking-tight">
          Ready to launch your <span className="text-gradient">dream career</span>?
        </h2>
        <p className="mt-4 text-base sm:text-lg text-muted-foreground max-w-xl mx-auto">
          Start with your resume or portfolio. Get your instant skill gap analysis and step-by-step career roadmap in seconds.
        </p>
        <div className="mt-8 flex justify-center">
          <Button
            size="lg"
            onClick={onCtaClick}
            className="bg-gradient-accent glow text-primary-foreground font-semibold text-base h-13 px-8 rounded-xl"
          >
            Get Started Free
            <ArrowRight className="size-5 ml-2" />
          </Button>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   8. FOOTER
   ========================================================================== */
function LandingFooter({ onCtaClick }: { onCtaClick: () => void }) {
  return (
    <footer className="mt-auto border-t border-border bg-surface/40 py-10">
      <div className="mx-auto max-w-6xl px-5 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Brain className="size-4 text-primary" />
          <span className="font-semibold text-foreground">SkillForge AI</span>
          <span>— Your AI-Powered Career Mentor</span>
        </div>

        <div className="flex items-center gap-6">
          <a href="#how-it-works" className="hover:text-foreground transition-colors">
            How It Works
          </a>
          <a href="#features" className="hover:text-foreground transition-colors">
            Features
          </a>
          <button
            type="button"
            onClick={onCtaClick}
            className="hover:text-foreground transition-colors"
          >
            Sign In
          </button>
        </div>

        <p>© {new Date().getFullYear()} SkillForge AI. All rights reserved.</p>
      </div>
    </footer>
  );
}
