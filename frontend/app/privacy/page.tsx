import type { Metadata } from "next";
import { PrivacyCenter } from "@/components/privacy-center";

export const metadata: Metadata = { title: "Privacy center", description: "Manage HealthGuard AI privacy preferences, exports, consent history, and deletion requests." };
export default function PrivacyPage() { return <PrivacyCenter />; }
