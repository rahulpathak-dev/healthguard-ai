import type { Metadata } from "next";
import { EmergencyGuide } from "@/components/emergency-guide";

export const metadata: Metadata = {
  title: "Emergency guidance",
  description: "Rapid first-aid guidance with immediate action first.",
};

export default function EmergencyPage() {
  return <EmergencyGuide />;
}
