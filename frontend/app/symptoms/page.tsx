import type { Metadata } from "next";
import { SymptomAssistant } from "@/components/symptom-assistant";

export const metadata: Metadata = {
  title: "Symptom guidance",
  description:
    "Organize symptoms and receive non-diagnostic safety-first guidance.",
};

export default function SymptomsPage() {
  return <SymptomAssistant />;
}
