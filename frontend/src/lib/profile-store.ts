import { useEffect, useState } from "react";

export type UnifiedProfile = {
  name?: string;
  bio?: string;
  education?: any[];
  experience?: any[];
  skills?: string[];
  projects?: { name?: string; description?: string; technologies?: string[]; url?: string; source?: string }[];
  certifications?: string[];
  technologies?: string[];
  achievements?: string[];
  source?: {
    resume: boolean;
    portfolio: boolean;
  };
};

export type SkillGapItem = {
  skill: string;
  importance?: string;
  currentLevel?: number;
  requiredLevel?: number;
};

export type CareerProfileData = {
  id?: string;
  targetRole: string;
  careerMatches?: { role: string; score: number }[];
  profileSummary?: string;
  strongSkills?: string[];
  developingSkills?: string[];
  skillGaps?: SkillGapItem[];
  careerReadiness: number;
  missingTechnologies?: string[];
  missingProjectExperience?: string[];
  recommendedNextSkills?: string[];
  /** Deterministic intersection: student skills ∩ required skills */
  user_strengths?: string[];
  /** Deterministic difference: required skills − student skills */
  true_skill_gaps?: string[];
};

export type RoadmapWeek = {
  week: number;
  title: string;
  skills?: string[];
  courses?: { title: string; provider?: string; url?: string; duration?: string; difficulty?: string }[];
  project?: { title: string; description?: string; skills?: string[] };
  completed?: boolean;
};

export type LearningPathData = {
  id?: string | undefined;
  targetRole: string;
  durationWeeks?: number | undefined;
  roadmap?: RoadmapWeek[] | undefined;
  courses?: { title: string; provider?: string; url?: string; duration?: string; difficulty?: string; skillAddressed?: string; similarity_score?: number }[] | undefined;
  recommendedProjects?: { title: string; description?: string; technologies?: string[]; difficulty?: string }[] | undefined;
  certifications?: { name: string; provider?: string; priority?: string }[] | undefined;
  interviewPrep?: { topic: string; question: string; keyConcept?: string }[] | undefined;
  careerAdvice?: string[] | undefined;
};

export type SkillProgressItem = {
  skill: string;
  status: "not_started" | "in_progress" | "completed";
  progress: number;
  completed: boolean;
};

export type ProgressData = {
  id?: string;
  roadmapProgress: number;
  totalRoadmapItems: number;
  completedRoadmapItems: number;
  skillGapItems?: string[];
  skillProgress?: SkillProgressItem[];
};

export type AnalysisPipelineResult = {
  resumeId?: string | undefined;
  portfolioId?: string | undefined;
  resumeName?: string | undefined;
  resumeSize?: number | undefined;
  portfolio?: string | undefined;
  linkedin?: string | undefined;
  role: string;
  unifiedProfile?: UnifiedProfile | undefined;
  careerProfile?: CareerProfileData | undefined;
  learningPath?: LearningPathData | undefined;
  progress?: ProgressData | undefined;
};


const KEY = "skillforge-profile";
const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";
let hydrationRequest: Promise<AnalysisPipelineResult | null> | null = null;

export function saveProfile(profile: AnalysisPipelineResult) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(profile));
  window.dispatchEvent(new Event("skillforge-profile-update"));
}

export function clearProfile() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(KEY);
  window.dispatchEvent(new Event("skillforge-profile-update"));
}

function readStoredProfile(): AnalysisPipelineResult | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AnalysisPipelineResult) : null;
  } catch {
    return null;
  }
}

/** Restore the latest persisted analysis when the browser session has no cached copy. */
export async function hydrateProfileFromBackend(): Promise<AnalysisPipelineResult | null> {
  if (typeof window === "undefined") return null;
  const stored = readStoredProfile();
  if (stored) return stored;
  if (hydrationRequest) return hydrationRequest;

  hydrationRequest = fetch(`${API_BASE_URL}/api/career-profiles/latest-analysis`, {
    credentials: "include",
  })
    .then(async (response) => {
      if (response.status === 401 || !response.ok) return null;
      const payload = await response.json();
      if (!payload.success || !payload.data) return null;
      const result = payload.data as AnalysisPipelineResult;
      saveProfile(result);
      return result;
    })
    .catch(() => null)
    .finally(() => {
      hydrationRequest = null;
    });
  return hydrationRequest;
}

/** Optimistically synchronize a roadmap checkbox with session state. */
export function updateRoadmapCheckpoint(week: number, completed: boolean) {
  const profile = readStoredProfile();
  if (!profile?.learningPath?.roadmap) return;
  saveProfile({
    ...profile,
    learningPath: {
      ...profile.learningPath,
      roadmap: profile.learningPath.roadmap.map((item) =>
        item.week === week ? { ...item, completed } : item,
      ),
    },
  });
}

/** Apply the server's authoritative checkpoint and deterministic progress state. */
export function updateProgressState(progress: ProgressData, roadmap?: RoadmapWeek[]) {
  const profile = readStoredProfile();
  if (!profile) return;
  saveProfile({
    ...profile,
    progress,
    learningPath: profile.learningPath
      ? { ...profile.learningPath, roadmap: roadmap ?? profile.learningPath.roadmap }
      : profile.learningPath,
  });
}

export function useProfile(): AnalysisPipelineResult | null {
  const [profile, setProfile] = useState<AnalysisPipelineResult | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AnalysisPipelineResult;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const sync = () => {
      const raw = sessionStorage.getItem(KEY);
      if (raw) {
        try {
          setProfile(JSON.parse(raw) as AnalysisPipelineResult);
        } catch {
          setProfile(null);
        }
      } else setProfile(null);
    };

    window.addEventListener("skillforge-profile-update", sync);
    window.addEventListener("storage", sync);
    if (!readStoredProfile()) {
      void hydrateProfileFromBackend().then((hydrated) => {
        if (hydrated) setProfile(hydrated);
      });
    }
    return () => {
      window.removeEventListener("skillforge-profile-update", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return profile;
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
