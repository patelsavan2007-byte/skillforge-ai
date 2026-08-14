import { createFileRoute } from "@tanstack/react-router";
import { LoginPageContent } from "@/components/auth/login-page-content";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign In — SkillForge AI" },
      {
        name: "description",
        content:
          "Sign in to SkillForge AI and continue your personalized journey toward becoming job-ready.",
      },
      { property: "og:title", content: "Sign In — SkillForge AI" },
      {
        property: "og:description",
        content: "Continue your journey toward becoming job-ready with SkillForge AI.",
      },
    ],
  }),
  component: LoginPageContent,
});
