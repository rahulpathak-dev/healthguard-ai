"use client";

import { useState } from "react";
import { apiRequest } from "@/lib/api-client";

type Overview = { users: number; active_users: number; doctors_pending: number; safety_events_open: number; misinformation_checks: number; approved_sources: number; notification_failures: number; system_health: string; job_health: string };
type UserRow = { id: string; email_domain: string; role: string; is_active: boolean; created_at: string };
type DoctorRow = { id: string; display_name: string; specialty: string | null; verification_status: string };
type SafetyRow = { id: string; severity: string; stage: string; action: string; created_at: string };
type SourceRow = { id: string; name: string; publisher: string; approval_status: string; base_url: string };
type AuditRow = { id: string; action: string; target_type: string; reason: string | null; created_at: string };

export function AdminGovernanceConsole() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [doctors, setDoctors] = useState<DoctorRow[]>([]);
  const [safety, setSafety] = useState<SafetyRow[]>([]);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [audits, setAudits] = useState<AuditRow[]>([]);
  const [message, setMessage] = useState("Admin views are intentionally redacted to avoid unnecessary patient data exposure.");

  async function load() {
    const [nextOverview, nextUsers, nextDoctors, nextSafety, nextSources, nextAudits] = await Promise.all([
      apiRequest<Overview>("/admin/overview"),
      apiRequest<UserRow[]>("/admin/users"),
      apiRequest<DoctorRow[]>("/admin/doctors"),
      apiRequest<SafetyRow[]>("/admin/safety-events"),
      apiRequest<SourceRow[]>("/admin/knowledge-sources"),
      apiRequest<AuditRow[]>("/admin/audit-logs"),
    ]);
    setOverview(nextOverview); setUsers(nextUsers); setDoctors(nextDoctors); setSafety(nextSafety); setSources(nextSources); setAudits(nextAudits);
  }

  async function verifyDoctor(id: string, verification_status: "verified" | "rejected" | "suspended") {
    const reason = window.prompt(`Reason for doctor status: ${verification_status}`);
    if (!reason) return;
    await apiRequest(`/admin/doctors/${id}/verification`, { method: "PUT", body: JSON.stringify({ confirm: true, reason, verification_status }) });
    setMessage("Doctor verification decision saved and audited.");
    await load();
  }

  async function sourceStatus(id: string, approval_status: "approved" | "rejected" | "retired") {
    const reason = window.prompt(`Reason for source status: ${approval_status}`);
    if (!reason) return;
    await apiRequest(`/admin/knowledge-sources/${id}/status`, { method: "PUT", body: JSON.stringify({ confirm: true, reason, approval_status }) });
    setMessage("Knowledge source status saved and audited.");
    await load();
  }

  return (
    <section className="admin-shell">
      <div className="admin-hero"><p className="eyebrow">Governance</p><h1>Admin dashboard</h1><p>{message}</p><button className="button" onClick={load}>Load governance data</button></div>
      {overview && <div className="admin-metrics">{Object.entries(overview).map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><strong>{value}</strong></div>)}</div>}
      <div className="admin-grid">
        <section className="admin-card"><h2>User status</h2>{users.map((user) => <p key={user.id}>{user.role} at {user.email_domain}: {user.is_active ? "active" : "disabled"}</p>)}</section>
        <section className="admin-card"><h2>Doctor verification</h2>{doctors.map((doctor) => <article key={doctor.id}><b>{doctor.display_name}</b><p>{doctor.specialty ?? "Specialty not provided"} - {doctor.verification_status}</p><button onClick={() => verifyDoctor(doctor.id, "verified")}>Verify</button><button onClick={() => verifyDoctor(doctor.id, "rejected")}>Reject</button><button onClick={() => verifyDoctor(doctor.id, "suspended")}>Suspend</button></article>)}</section>
        <section className="admin-card"><h2>Safety events</h2>{safety.map((event) => <p key={event.id}>{event.severity} - {event.stage} - {event.action}</p>)}</section>
        <section className="admin-card"><h2>Medical source management</h2>{sources.map((source) => <article key={source.id}><b>{source.name}</b><p>{source.publisher} - {source.approval_status}</p><button onClick={() => sourceStatus(source.id, "approved")}>Approve</button><button onClick={() => sourceStatus(source.id, "rejected")}>Reject</button><button onClick={() => sourceStatus(source.id, "retired")}>Retire</button></article>)}</section>
        <section className="admin-card"><h2>Audit logs</h2>{audits.map((audit) => <p key={audit.id}>{audit.action} on {audit.target_type}: {audit.reason}</p>)}</section>
      </div>
    </section>
  );
}
