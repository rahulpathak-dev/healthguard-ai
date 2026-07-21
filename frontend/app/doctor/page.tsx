import type { Metadata } from "next";
import { DoctorReviewWorkspace } from "@/components/doctor-review-workspace";

export const metadata: Metadata = {
  title: "Doctor review workspace",
  description:
    "Review only medical records explicitly shared by users with active consent.",
};

export default function DoctorPage() {
  return <DoctorReviewWorkspace />;
}
