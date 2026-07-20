import type { Metadata } from "next";
import { HealthChat } from "@/components/health-chat";
export const metadata: Metadata = { title: "Health education chat", description: "Ask general health education questions with safety guidance and source context." };
export default function ChatPage() { return <HealthChat />; }
