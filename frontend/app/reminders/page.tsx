import type { Metadata } from "next";
import { ReminderCenter } from "@/components/reminder-center";

export const metadata: Metadata = {
  title: "Reminders",
  description: "Timezone-aware health reminders and notification center.",
};

export default function RemindersPage() {
  return <ReminderCenter />;
}
