import { useEffect, useState } from "react";
import { getAuthHeaders, getSession } from "./auth-store";

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
  prioritized_gaps?: {
    critical?: string[];
    medium?: string[];
    optional?: string[];
  };
};

export type RoadmapSubTask = {
  title: string;
  duration?: string;
  description?: string;
};

export type RoadmapWeek = {
  week: number;
  title: string;
  skill?: string;
  skills?: string[];
  current_level?: string;
  target_level?: string;
  gap_level?: string;
  estimated_hours?: number | string;
  estimated_days?: number | string;
  difficulty?: string;
  objective?: string;
  why_this_matters?: string;
  why_this_week?: string;
  tasks?: RoadmapSubTask[];
  checkpoint?: string;
  courses?: { title: string; provider?: string; url?: string; duration?: string; difficulty?: string; why_recommended?: string }[];
  project?: { title: string; description?: string; skills?: string[]; url?: string };
  status?: "not_started" | "in_progress" | "completed";
  completed?: boolean;
  completed_at?: string;
  actual_hours?: number;
};

export type LearningPathData = {
  id?: string | undefined;
  targetRole: string;
  durationWeeks?: number | undefined;
  estimatedCompletionHours?: number | undefined;
  estimatedCompletionDays?: number | undefined;
  initialReadiness?: number | undefined;
  careerReadiness?: number | undefined;
  improvedScore?: number | undefined;
  roadmap?: RoadmapWeek[] | undefined;
  courses?: { title: string; provider?: string; url?: string; duration?: string; difficulty?: string; skillAddressed?: string; similarity_score?: number; why_recommended?: string }[] | undefined;
  recommendedProjects?: {
    title: string;
    description?: string;
    technologies?: string[];
    difficulty?: string;
    skills_gained?: string[];
    skills_targeted?: string[];
    why_recommended?: string;
    expected_resume_impact?: string;
    suggested_stack?: string[];
    url?: string;
  }[] | undefined;
  certifications?: { name: string; provider?: string; priority?: string; skill?: string; why_recommended?: string; url?: string }[] | undefined;
  interviewPrep?: { topic: string; question: string; keyConcept?: string; url?: string; resourceTitle?: string }[] | undefined;
  careerAdvice?: string[] | undefined;
  user_strengths?: string[] | undefined;
  true_skill_gaps?: string[] | undefined;
  prioritized_gaps?: {
    critical?: string[];
    medium?: string[];
    optional?: string[];
  } | undefined;
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
  initialReadiness?: number;
  careerReadiness?: number;
  improvedScore?: number;
  completedGaps?: string[];
  remainingGaps?: string[];
  skillGapItems?: string[];
  skillProgress?: SkillProgressItem[];
};

export type AnalysisPipelineResult = {
  userId?: string | undefined;
  sessionId?: string | undefined;
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

const API_BASE_URL = import.meta.env["VITE_API_URL"] || "http://localhost:8000";
let hydrationRequest: Promise<AnalysisPipelineResult | null> | null = null;

function getProfileStorageKey(userId?: string, sessionId?: string): string {
  if (!userId || !sessionId) return "skillforge-profile-unauthenticated";
  return `skillforge_profile_${userId}_${sessionId}`;
}

export function saveProfile(profile: AnalysisPipelineResult) {
  if (typeof window === "undefined") return;
  try {
    const user = getSession();
    const userId = profile.userId || user?.id;
    const sessionId = profile.sessionId || user?.sessionId;
    const fullProfile: AnalysisPipelineResult = {
      ...profile,
      userId,
      sessionId,
    };
    const key = getProfileStorageKey(userId, sessionId);
    sessionStorage.setItem(key, JSON.stringify(fullProfile));
    sessionStorage.removeItem("skillforge-profile");
    window.dispatchEvent(new Event("skillforge-profile-update"));
  } catch (err) {
    console.warn("Error saving profile to sessionStorage:", err);
  }
}

export function clearProfile() {
  if (typeof window === "undefined") return;
  try {
    const user = getSession();
    if (user?.id && user?.sessionId) {
      sessionStorage.removeItem(getProfileStorageKey(user.id, user.sessionId));
    }
    sessionStorage.removeItem("skillforge-profile");
    window.dispatchEvent(new Event("skillforge-profile-update"));
  } catch (err) {
    console.warn("Error clearing profile from sessionStorage:", err);
  }
}

export function readStoredProfile(): AnalysisPipelineResult | null {
  if (typeof window === "undefined") return null;
  try {
    const user = getSession();
    if (!user?.id || !user?.sessionId) return null;
    const key = getProfileStorageKey(user.id, user.sessionId);
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AnalysisPipelineResult;
    if (parsed && parsed.userId === user.id && parsed.sessionId === user.sessionId) {
      return parsed;
    }
    return null;
  } catch (err) {
    console.warn("Error reading stored profile from sessionStorage:", err);
    return null;
  }
}

/** Restore the latest persisted analysis when the browser session has no cached copy. */
export async function hydrateProfileFromBackend(): Promise<AnalysisPipelineResult | null> {
  if (typeof window === "undefined") return null;
  try {
    const user = getSession();
    if (!user?.id || !user?.sessionId) return null;
    const stored = readStoredProfile();
    if (stored) return stored;
    if (hydrationRequest) return hydrationRequest;

    hydrationRequest = fetch(`${API_BASE_URL}/api/career-profiles/latest-analysis`, {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then(async (response) => {
        if (response.status === 401 || !response.ok) return null;
        const payload = await response.json();
        if (!payload.success || !payload.data) return null;
        const result = payload.data as AnalysisPipelineResult;
        result.userId = user.id;
        result.sessionId = user.sessionId;
        saveProfile(result);
        return result;
      })
      .catch(() => null)
      .finally(() => {
        hydrationRequest = null;
      });
    return hydrationRequest;
  } catch {
    return null;
  }
}

/** Optimistically synchronize a roadmap checkbox with session state. */
export function updateRoadmapCheckpoint(week: number, completed: boolean) {
  try {
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
  } catch (err) {
    console.warn("Error updating roadmap checkpoint:", err);
  }
}

/** Apply the server's authoritative checkpoint and deterministic progress state. */
export function updateProgressState(progress: ProgressData, roadmap?: RoadmapWeek[]) {
  try {
    const profile = readStoredProfile();
    if (!profile) return;
    saveProfile({
      ...profile,
      progress,
      learningPath: profile.learningPath
        ? { ...profile.learningPath, roadmap: roadmap ?? profile.learningPath.roadmap }
        : profile.learningPath,
    });
  } catch (err) {
    console.warn("Error updating progress state:", err);
  }
}

export function useProfile(): AnalysisPipelineResult | null {
  const [profile, setProfile] = useState<AnalysisPipelineResult | null>(() => {
    try {
      return readStoredProfile();
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const sync = () => {
      try {
        setProfile(readStoredProfile());
      } catch {
        setProfile(null);
      }
    };

    window.addEventListener("skillforge-profile-update", sync);
    window.addEventListener("storage", sync);

    try {
      const initial = readStoredProfile();
      setProfile(initial);
    } catch {
      setProfile(null);
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
