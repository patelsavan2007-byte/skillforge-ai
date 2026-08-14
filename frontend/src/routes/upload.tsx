import { createFileRoute } from "@tanstack/react-router";
import { RequireAuth } from "@/components/auth/require-auth";
import { AppWorkflow } from "@/components/workflow/app-workflow";

export const Route = createFileRoute("/upload")({
  head: () => ({
    meta: [
      { title: "Upload Resume & Portfolio — SkillForge AI" },
      {
        name: "description",
        content: "Upload your resume or enter your portfolio URL to run a personalized career gap analysis.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <AppWorkflow />
    </RequireAuth>
  ),
});
