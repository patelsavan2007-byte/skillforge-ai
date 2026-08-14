import { createFileRoute } from "@tanstack/react-router";
import { RequireAuth } from "@/components/auth/require-auth";
import { AppWorkflow } from "@/components/workflow/app-workflow";

export const Route = createFileRoute("/app")({
  head: () => ({ meta: [{ title: "Create Career Analysis — SkillForge AI" }] }),
  component: () => (
    <RequireAuth>
      <AppWorkflow />
    </RequireAuth>
  ),
});
