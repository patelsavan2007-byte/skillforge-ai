import { useEffect, useState } from "react";

export type StudentProfile = {
  resumeName: string;
  resumeSize: number;
  portfolio: string;
  linkedin: string;
  role: string;
};

const KEY = "skillforge-profile";

export function saveProfile(profile: StudentProfile) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(profile));
}

export function useProfile(): StudentProfile | null {
  const [profile, setProfile] = useState<StudentProfile | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(KEY);
    if (raw) {
      try {
        setProfile(JSON.parse(raw) as StudentProfile);
      } catch {
        setProfile(null);
      }
    }
  }, []);

  return profile;
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
