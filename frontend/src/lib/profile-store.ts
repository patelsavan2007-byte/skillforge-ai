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
  id?: string;
  targetRole: string;
  durationWeeks?: number;
  roadmap?: RoadmapWeek[];
  courses?: { title: string; provider?: string; url?: string; duration?: string; difficulty?: string; skillAddressed?: string }[];
  recommendedProjects?: { title: string; description?: string; technologies?: string[]; difficulty?: string }[];
  certifications?: { name: string; provider?: string; priority?: string }[];
  interviewPrep?: { topic: string; question: string; keyConcept?: string }[];
  careerAdvice?: string[];
};

export type AnalysisPipelineResult = {
  resumeId?: string;
  portfolioId?: string;
  resumeName?: string;
  resumeSize?: number;
  portfolio?: string;
  linkedin?: string;
  role: string;
  unifiedProfile?: UnifiedProfile;
  careerProfile?: CareerProfileData;
  learningPath?: LearningPathData;
};

const KEY = "skillforge-profile";

export function saveProfile(profile: AnalysisPipelineResult) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(profile));
  window.dispatchEvent(new Event("skillforge-profile-update"));
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
      }
    };

    window.addEventListener("skillforge-profile-update", sync);
    window.addEventListener("storage", sync);
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
