"use client";

import React from "react";

import { useState } from "react";
import { apiRequest } from "@/lib/api-client";
import { formatDateTime } from "@/lib/i18n";
import { useToast } from "@/components/toast-provider";

type Center = { active_sessions: number; active_sharing_grants: number; consent_events: number; pending_exports: number; deletion_status: string | null; retention_documentation: string[]; legal_compliance_note: string };
type ExportRequest = { id: string; status: string; download_expires_at: string | null; requested_at: string; completed_at: string | null };
type ConsentEvent = { id: string; event_type: string; action: string; subject_type: string; created_at: string };

export function PrivacyCenter() {
  const toast = useToast();
  const [center, setCenter] = useState<Center | null>(null);
  const [exports, setExports] = useState<ExportRequest[]>([]);
  const [events, setEvents] = useState<ConsentEvent[]>([]);
  const [phrase, setPhrase] = useState("");

  async function load() {
    const [summary, exportRows, eventRows] = await Promise.all([
      apiRequest<Center>("/privacy/center"),
      apiRequest<ExportRequest[]>("/privacy/exports"),
      apiRequest<ConsentEvent[]>("/privacy/consent-history"),
    ]);
    setCenter(summary); setExports(exportRows); setEvents(eventRows);
  }
  async function requestExport() {
    await apiRequest<ExportRequest>("/privacy/exports", { method: "POST", body: JSON.stringify({ include_ai_conversations: true, include_health_records_metadata: true, include_profiles: true }) });
    toast("Export prepared with a short-lived private download link.");
    await load();
  }
  async function downloadExport(id: string) {
    const result = await apiRequest<{ url: string; expires_at: string }>(`/privacy/exports/${id}/download`, { method: "POST" });
    window.location.href = result.url;
  }
  async function requestDeletion() {
    if (!window.confirm("Request account deletion? Active sessions will be revoked.")) return;
    await apiRequest("/privacy/deletion", { method: "POST", body: JSON.stringify({ confirmation_phrase: phrase }) });
    toast("Deletion request created. Follow the status instructions before final confirmation.");
  }
  return (
    <section className="privacy-center-shell">
      <div className="privacy-center-hero"><p className="eyebrow">Privacy by design</p><h1>Privacy and data control center</h1><p>Manage sessions, sharing, exports, deletion, cookies, and notification preferences. This product does not claim automatic legal compliance.</p><button className="button" onClick={load}>Load my privacy center</button></div>
      {center && <div className="privacy-stats"><div><span>Active sessions</span><b>{center.active_sessions}</b></div><div><span>Sharing grants</span><b>{center.active_sharing_grants}</b></div><div><span>Consent events</span><b>{center.consent_events}</b></div><div><span>Exports</span><b>{center.pending_exports}</b></div></div>}
      <div className="privacy-control-grid">
        <section className="privacy-control-card"><h2>Secure export</h2><p>Exports include selected metadata and conversation summaries; download links expire quickly.</p><button className="button" onClick={requestExport}>Request export</button>{exports.map((item) => <p key={item.id}>{item.status} - {formatDateTime(item.requested_at)} {item.status === "ready" && <button onClick={() => downloadExport(item.id)}>Download</button>}</p>)}</section>
        <section className="privacy-control-card"><h2>Account deletion</h2><p>Type: <b>delete my healthguard account</b>. A configured grace period helps prevent accidental deletion.</p><input aria-label="Deletion confirmation phrase" value={phrase} onChange={(event) => setPhrase(event.target.value)} /><button className="button danger-button" onClick={requestDeletion}>Request deletion</button></section>
        <section className="privacy-control-card"><h2>Retention documentation</h2>{center?.retention_documentation.map((item) => <p key={item}>{item}</p>)}</section>
        <section className="privacy-control-card"><h2>Consent history</h2>{events.map((event) => <p key={event.id}>{event.event_type}: {event.action} on {event.subject_type}</p>)}</section>
      </div>
    </section>
  );
}
