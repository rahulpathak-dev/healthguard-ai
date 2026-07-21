import type { ReactNode } from "react";
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <section className="auth-shell">
      <div className="auth-context">
        <p className="eyebrow">Private by design</p>
        <h2>Your health information deserves careful protection.</h2>
        <p>
          Secure sessions, short-lived access, and clear device controls help
          keep your account in your hands.
        </p>
        <ul>
          <li>Tokens stay in HTTP-only cookies</li>
          <li>Every device session can be reviewed</li>
          <li>Passwords use modern one-way hashing</li>
        </ul>
      </div>
      {children}
    </section>
  );
}
