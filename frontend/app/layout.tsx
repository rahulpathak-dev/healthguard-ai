import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { Navigation } from "@/components/navigation";
import { ToastProvider } from "@/components/toast-provider";
import { MEDICAL_DISCLAIMER } from "@/config/medical";
import "./globals.css";
import "./auth.css";
import "./profiles.css";
import "./dashboard.css";
import "./chat.css";
import "./symptoms.css";
import "./medicines.css";
import "./records.css";
import "./reports.css";
import "./reminders.css";
import "./emergency-guide.css";
import "./misinformation.css";
import "./governance.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://healthguard.ai"),
  title: { default: "HealthGuard AI - Health information, made clearer", template: "%s | HealthGuard AI" },
  description: "A safety-first health companion that helps you understand symptoms, medicines, medical reports, and trusted health information.",
  keywords: ["health education", "medical report explainer", "medicine information", "symptom guidance", "health records"],
  alternates: { canonical: "/" },
  openGraph: {
    title: "HealthGuard AI - Clarity for everyday health questions",
    description: "Understand health information with plain-language, safety-first guidance designed to support, not replace, professional care.",
    url: "/",
    siteName: "HealthGuard AI",
    type: "website",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image", title: "HealthGuard AI", description: "Health information, made clearer and safer." },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#075e73" };

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Navigation />
        <main id="main-content">{children}</main>
        <footer className="site-footer">
          <div className="footer-grid">
            <div className="footer-brand">
              <Link className="brand brand-light" href="/" aria-label="HealthGuard AI home"><span className="brand-mark" aria-hidden="true">+</span><span>HealthGuard <b>AI</b></span></Link>
              <p>Thoughtful technology for clearer health information.</p>
            </div>
            <div><h2>Product</h2><Link href="#features">Features</Link><Link href="#how-it-works">How it works</Link><Link href="#privacy">Privacy</Link></div>
            <div><h2>Company</h2><Link href="#trust">Our approach</Link><Link href="#faq">FAQ</Link><a href="mailto:hello@healthguard.ai">Contact</a></div>
            <div><h2>Important</h2><p className="footer-disclaimer">{MEDICAL_DISCLAIMER}</p></div>
          </div>
          <div className="footer-bottom"><span>(c) {new Date().getFullYear()} HealthGuard AI</span><span>Built with care for people, privacy, and clarity.</span></div>
        </footer>
        </ToastProvider>
      </body>
    </html>
  );
}



