import type { Metadata } from "next";
import { ProfileManager } from "@/components/profile-manager";
export const metadata: Metadata = { title: "Health profiles", description: "Manage private personal and family health profiles." };
export default function ProfilesPage() { return <ProfileManager />; }
