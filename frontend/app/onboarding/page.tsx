import type { Metadata } from "next";

export const metadata: Metadata = { title: "Onboarding", description: "Start safely with HealthGuard AI." };
export default function OnboardingPage() {
  return <section className="onboarding-shell"><p className="eyebrow">Welcome</p><h1>Start safely with HealthGuard AI</h1><div className="onboarding-steps"><article><h2>1. Add profiles</h2><p>Create only the health profiles you need, with optional sensitive fields.</p></article><article><h2>2. Upload carefully</h2><p>Records stay private and are scanned/quarantined before use.</p></article><article><h2>3. Use AI safely</h2><p>HealthGuard provides education, cites sources, and escalates red flags.</p></article></div></section>;
}
