"use client";

import React from "react";

import { useState } from "react";
import { apiRequest } from "@/lib/api-client";

type Grant = {
  id: string;
  doctor_user_id: string;
  profile_id: string;
  record_ids: string[];
  scope: "read";
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
};

type Note = { id: string; note: string; record_id: string; doctor_user_id: string; created_at: string };
type Audit = { id: string; action: string; record_id: string | null; created_at: string };

export function SharingConsentCenter() {
  const [profileId, setProfileId] = useState("");
  const [doctorUserId, setDoctorUserId] = useState("");
  const [recordIds, setRecordIds] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [grants, setGrants] = useState<Grant[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [audits, setAudits] = useState<Audit[]>([]);
  const [message, setMessage] = useState("Only selected records are shared. Access is read-only and can be revoked anytime.");

  async function load() {
    const [grantRows, noteRows, auditRows] = await Promise.all([
      apiRequest<Grant[]>("/sharing/grants"),
      apiRequest<Note[]>("/sharing/review-notes"),
      apiRequest<Audit[]>("/sharing/audit-logs"),
    ]);
    setGrants(grantRows);
    setNotes(noteRows);
    setAudits(auditRows);
  }

  async function createGrant() {
    const ids = recordIds.split(",").map((item) => item.trim()).filter(Boolean);
    await apiRequest<Grant>("/sharing/grants", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, doctor_user_id: doctorUserId, record_ids: ids, expires_at: expiresAt, scope: "read" }),
    });
    setMessage("Sharing grant created. The doctor can only read the selected records until expiry.");
    await load();
  }

  async function revoke(id: string) {
    if (!window.confirm("Revoke this doctor's access now? They will lose access immediately.")) return;
    await apiRequest<Grant>(`/sharing/grants/${id}/revoke`, { method: "POST" });
    setMessage("Access revoked and audit logged.");
    await load();
  }

  return (
    <section className="sharing-shell" aria-labelledby="sharing-title">
      <div className="sharing-hero">
        <p className="eyebrow">Consent-based sharing</p>
        <h1 id="sharing-title">Share selected records with a verified doctor</h1>
        <p>{message}</p>
      </div>
      <div className="sharing-grid">
        <form className="sharing-card" action={createGrant}>
          <h2>Create read-only grant</h2>
          <label>Profile ID<input value={profileId} onChange={(event) => setProfileId(event.target.value)} required /></label>
          <label>Doctor user ID<input value={doctorUserId} onChange={(event) => setDoctorUserId(event.target.value)} required /></label>
          <label>Selected record IDs, comma separated<textarea value={recordIds} onChange={(event) => setRecordIds(event.target.value)} required /></label>
          <label>Expiry date/time<input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} required /></label>
          <button className="button" type="submit">Confirm and share</button>
        </form>
        <div className="sharing-card">
          <h2>Sharing history</h2>
          <button className="button button-secondary" type="button" onClick={load}>Refresh</button>
          {grants.length === 0 ? <p>No active or past grants loaded.</p> : grants.map((grant) => (
            <article key={grant.id} className="share-row">
              <strong>{grant.record_ids.length} record(s)</strong>
              <span>Doctor: {grant.doctor_user_id}</span>
              <span>Expires: {new Date(grant.expires_at).toLocaleString()}</span>
              <span>Status: {grant.revoked_at ? "Revoked" : "Active until expiry"}</span>
              {!grant.revoked_at && <button type="button" onClick={() => revoke(grant.id)}>Revoke</button>}
            </article>
          ))}
        </div>
      </div>
      <div className="sharing-grid">
        <div className="sharing-card"><h2>Doctor review notes visible to you</h2>{notes.map((note) => <p key={note.id}><b>Record {note.record_id}</b>: {note.note}</p>)}</div>
        <div className="sharing-card"><h2>Access audit logs</h2>{audits.map((audit) => <p key={audit.id}>{audit.action} {audit.record_id ? `- ${audit.record_id}` : ""}</p>)}</div>
      </div>
    </section>
  );
}
