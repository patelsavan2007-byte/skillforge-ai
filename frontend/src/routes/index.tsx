import { createFileRoute } from "@tanstack/react-router";
import { LandingPage } from "@/components/landing/landing-page";

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
  component: LandingPage,
});
