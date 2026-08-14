/**
 * Normalized API Base URL for SkillForge AI frontend.
 * Supports VITE_API_BASE_URL and VITE_API_URL environment variables.
 * Ensures trailing slashes are safely stripped to prevent '//api/...' double-slash routing issues.
 */
export const API_BASE_URL = (
  (typeof import.meta !== "undefined" &&
    (import.meta.env?.["VITE_API_BASE_URL"] || import.meta.env?.["VITE_API_URL"])) ||
  "http://localhost:8000"
).replace(/\/+$/, "");

export function buildApiUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
}
