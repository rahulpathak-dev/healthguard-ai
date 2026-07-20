import type { Metadata } from "next";
import { MisinformationChecker } from "@/components/misinformation-checker";

export const metadata: Metadata = {
  title: "Misinformation checker",
  description: "Check health claims against trusted retrieved sources.",
};

export default function MisinformationPage() {
  return <MisinformationChecker />;
}
