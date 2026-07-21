import type { Metadata } from "next";
import { AdminGovernanceConsole } from "@/components/admin-governance-console";

export const metadata: Metadata = {
  title: "Admin governance",
  description:
    "Govern HealthGuard AI users, verified doctors, safety events, sources, and platform health with privacy controls.",
};

export default function AdminPage() {
  return <AdminGovernanceConsole />;
}
