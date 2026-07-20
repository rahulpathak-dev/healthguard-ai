import type { Metadata } from "next";
import { SharingConsentCenter } from "@/components/sharing-consent-center";

export const metadata: Metadata = {
  title: "Doctor record sharing",
  description: "Create read-only, expiring doctor access grants for selected HealthGuard AI records.",
};

export default function SharingPage() {
  return <SharingConsentCenter />;
}
