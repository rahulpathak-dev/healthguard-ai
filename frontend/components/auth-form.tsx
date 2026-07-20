"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, apiRequest } from "@/lib/api-client";

type Mode = "login" | "register" | "forgot" | "reset" | "verify";

const copy = {
  login: ["Welcome back", "Sign in to securely access your HealthGuard account."],
  register: ["Create your account", "Start with a private, safety-first health workspace."],
  forgot: ["Reset your password", "Enter your email and we will send instructions if an account is eligible."],
  reset: ["Choose a new password", "Use the one-time token from your password reset email."],
  verify: ["Verify your email", "Use the one-time token from your verification email."],
} as const;

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  useEffect(() => { const value = new URLSearchParams(window.location.hash.slice(1)).get("token"); if (value) setToken(value); }, []);
  const needsEmail = ["login", "register", "forgot"].includes(mode);
  const needsPassword = ["login", "register", "reset"].includes(mode);
  const needsToken = ["reset", "verify"].includes(mode);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setMessage(""); setLoading(true);
    const values = new FormData(event.currentTarget);
    const body: Record<string, string> = {};
    if (needsEmail) body.email = String(values.get("email") ?? "");
    if (needsPassword) body[mode === "reset" ? "new_password" : "password"] = String(values.get("password") ?? "");
    if (needsToken) body.token = String(values.get("token") ?? "");
    const endpoint = { login: "login", register: "register", forgot: "forgot-password", reset: "reset-password", verify: "verify-email" }[mode];
    try {
      const result = await apiRequest<{ message?: string } | { email: string }>(`/auth/${endpoint}`, { method: "POST", body: JSON.stringify(body) });
      if (mode === "login") { router.replace("/account"); router.refresh(); return; }
      setMessage("message" in result && result.message ? result.message : "Request completed.");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Something went wrong. Please try again.");
    } finally { setLoading(false); }
  }

  return <div className="auth-card"><div className="auth-heading"><span className="brand-mark" aria-hidden="true">+</span><h1>{copy[mode][0]}</h1><p>{copy[mode][1]}</p></div><form onSubmit={submit} className="auth-form">{needsEmail && <label>Email address<input name="email" type="email" autoComplete="email" required /></label>}{needsToken && <label>One-time token<input name="token" type="text" autoComplete="one-time-code" minLength={32} value={token} onChange={(event) => setToken(event.target.value)} required /></label>}{needsPassword && <label>{mode === "reset" ? "New password" : "Password"}<input name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "login" ? 1 : 12} required /></label>}<button type="submit" disabled={loading}>{loading ? "Please wait..." : copy[mode][0]}</button>{error && <p className="form-error" role="alert">{error}</p>}{message && <p className="form-success" role="status">{message}</p>}</form>{mode === "login" && <div className="auth-links"><Link href="/auth/forgot-password">Forgot password?</Link><Link href="/auth/register">Create an account</Link></div>}{mode === "register" && <div className="auth-links"><Link href="/auth/login">Already have an account?</Link></div>}<p className="auth-note">HealthGuard AI will never ask for your password by email or store it in readable form.</p></div>;
}
