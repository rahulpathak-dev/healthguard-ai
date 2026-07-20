import type { Metadata } from "next";
import { MedicineInformationPlatform } from "@/components/medicine-information";

export const metadata: Metadata = {
  title: "Medicine information",
  description: "Search verified medicine education with source references and safety cautions.",
};

export default function MedicinesPage() {
  return <MedicineInformationPlatform />;
}
