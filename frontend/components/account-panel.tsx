"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiRequest } from "@/lib/api-client";

type User = {
  id: string;
  email: string;
  role: "user" | "doctor" | "admin";
  is_email_verified: boolean;
};
type Session = {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  last_seen_at: string;
  expires_at: string;
  is_current: boolean;
};

export function AccountPanel() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [account, devices] = await Promise.all([
        apiRequest<User>("/auth/me"),
        apiRequest<Session[]>("/auth/sessions"),
      ]);
      setUser(account);
      setSessions(devices);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        router.replace("/auth/login");
        return;
      }
      setError("We could not load your account securely.");
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  async function revoke(id: string) {
    await apiRequest(`/auth/sessions/${id}`, { method: "DELETE" });
    await load();
  }
  async function signOut(all = false) {
    await apiRequest(all ? "/auth/logout-all" : "/auth/logout", {
      method: "POST",
    });
    router.replace("/");
    router.refresh();
  }

  if (error)
    return (
      <p role="alert" className="form-error">
        {error}
      </p>
    );
  if (!user) return <p role="status">Loading your secure account...</p>;
  return (
    <div className="account-grid">
      <section className="account-card">
        <p className="eyebrow">Account</p>
        <h1>Your HealthGuard account</h1>
        <dl>
          <div>
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Role</dt>
            <dd>{user.role}</dd>
          </div>
          <div>
            <dt>Email status</dt>
            <dd>
              {user.is_email_verified ? "Verified" : "Verification required"}
            </dd>
          </div>
        </dl>
        <div className="account-actions">
          <button onClick={() => signOut(false)}>Sign out</button>
          <button className="button-secondary" onClick={() => signOut(true)}>
            Sign out everywhere
          </button>
        </div>
      </section>
      <section className="account-card">
        <p className="eyebrow">Security</p>
        <h2>Devices and sessions</h2>
        <p>
          Review where your account is signed in. Revoke anything you do not
          recognize.
        </p>
        <ul className="session-list">
          {sessions.map((session) => (
            <li key={session.id}>
              <div>
                <b>{session.is_current ? "This device" : "Signed-in device"}</b>
                <span>{session.user_agent || "Unknown browser"}</span>
                <small>
                  Last active {new Date(session.last_seen_at).toLocaleString()}
                </small>
              </div>
              {!session.is_current && (
                <button onClick={() => revoke(session.id)}>Revoke</button>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
