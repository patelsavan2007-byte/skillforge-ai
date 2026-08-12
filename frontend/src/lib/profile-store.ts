import { useEffect, useState } from "react";

export type ExtractedPersonal = {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
};

export type ExtractedEducation = {
  degree?: string;
  field?: string;
  institution?: string;
  startDate?: string;
  endDate?: string;
  sgpa?: number | null;
  cgpa?: number | null;
};

export type ExtractedExperience = {
  company?: string;
  title?: string;
  startDate?: string;
  endDate?: string;
  duration?: string;
  description?: string;
};

export type ExtractedProject = {
  name?: string;
  description?: string;
  technologies?: string[];
  url?: string;
};

export type ExtractedResumeProfile = {
  personal?: ExtractedPersonal;
  education?: ExtractedEducation[];
  experience?: ExtractedExperience[];
  skills?: string[];
  certifications?: string[];
  languages?: string[];
  projects?: ExtractedProject[];
};

export type StudentProfile = {
  resumeId?: string;
  resumeName: string;
  resumeSize: number;
  portfolio: string;
  linkedin: string;
  role: string;
  extractedProfile?: ExtractedResumeProfile;
};

const KEY = "skillforge-profile";

export function saveProfile(profile: StudentProfile) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(profile));
  // Dispatch custom event to sync active listeners
  window.dispatchEvent(new Event("skillforge-profile-update"));
}

export function useProfile(): StudentProfile | null {
  const [profile, setProfile] = useState<StudentProfile | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as StudentProfile;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const sync = () => {
      const raw = sessionStorage.getItem(KEY);
      if (raw) {
        try {
          setProfile(JSON.parse(raw) as StudentProfile);
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
