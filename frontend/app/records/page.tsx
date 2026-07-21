import type { Metadata } from "next";
import { MedicalRecordOrganizer } from "@/components/medical-record-organizer";

export const metadata: Metadata = {
  title: "Medical records",
  description:
    "Securely organize private medical records by profile, category, timeline, and tags.",
};

export default function RecordsPage() {
  return <MedicalRecordOrganizer />;
}
