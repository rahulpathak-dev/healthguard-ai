import React from "react";
import Link from "next/link";
import { LocaleSwitcher } from "@/components/locale-switcher";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/symptoms", label: "Symptoms" },
  { href: "/medicines", label: "Medicines" },
  { href: "/records", label: "Records" },
  { href: "/sharing", label: "Sharing" },
  { href: "/doctor", label: "Doctor" },
  { href: "/admin", label: "Admin" },
  { href: "/reports", label: "Reports" },
  { href: "/reminders", label: "Reminders" },
  { href: "/misinformation", label: "Claim check" },
  { href: "/emergency", label: "Emergency" },
  { href: "/profiles", label: "Profiles" },
  { href: "/privacy", label: "Privacy" },
  { href: "/onboarding", label: "Start" },
  { href: "/#features", label: "Features" },
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#privacy", label: "Privacy" },
  { href: "/#faq", label: "FAQ" },
];

export function Navigation() {
  return (
    <header className="site-header">
      <div className="nav-shell">
        <Link className="brand" href="/" aria-label="HealthGuard AI home">
          <span className="brand-mark" aria-hidden="true">+</span>
          <span>HealthGuard <b>AI</b></span>
        </Link>
        <nav aria-label="Primary navigation">
          {links.map((link) => <Link key={link.href} href={link.href}>{link.label}</Link>)}
        </nav>
        <LocaleSwitcher />
        <Link className="button button-small" href="/auth/login">Sign in</Link>
      </div>
    </header>
  );
}



