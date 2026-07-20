import type { Metadata } from "next";
import { HealthDashboard } from "@/components/health-dashboard";
export const metadata: Metadata = { title: "Health dashboard", description: "A private overview of reminders, records, reports, conversations, and family health profiles." };
export default function DashboardPage() { return <HealthDashboard />; }
