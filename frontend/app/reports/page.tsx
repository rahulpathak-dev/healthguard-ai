import type { Metadata } from "next";
import { ReportExplanationCenter } from "@/components/report-explanation-center";

export const metadata: Metadata = {
  title: "Report explanations",
  description: "OCR-powered medical report explanations with uncertainty and source report links.",
};

export default function ReportsPage() {
  return <ReportExplanationCenter />;
}
