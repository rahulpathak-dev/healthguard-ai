"use client";

import { useState } from "react";
import { apiRequest } from "@/lib/api-client";

type SharedRecord = { id: string; grant_id: string; title: string; record_type: string; owner_user_id: string; created_at: string };

export function DoctorReviewWorkspace() {
  const [records, setRecords] = useState<SharedRecord[]>([]);
  const [noteByRecord, setNoteByRecord] = useState<Record<string, string>>({});
  const [status, setStatus] = useState("Load consented records to begin. Doctor role alone does not provide access.");

  async function load() {
    setRecords(await apiRequest<SharedRecord[]>("/sharing/doctor/records"));
    setStatus("Showing only unexpired, non-revoked records explicitly shared with this doctor account.");
  }

  async function saveNote(record: SharedRecord) {
    await apiRequest(`/sharing/doctor/grants/${record.grant_id}/records/${record.id}/notes`, {
      method: "POST",
      body: JSON.stringify({ note: noteByRecord[record.id] ?? "" }),
    });
    setStatus("Review note saved and made visible to the user.");
  }

  return (
    <section className="sharing-shell">
      <div className="sharing-hero"><p className="eyebrow">Doctor workspace</p><h1>Consented record review</h1><p>{status}</p><button className="button" onClick={load}>Load shared records</button></div>
      <div className="sharing-grid">
        {records.length === 0 ? <div className="sharing-card"><h2>No consented records loaded</h2><p>Ask the user to create a selected-record grant with an expiry date.</p></div> : records.map((record) => (
          <article className="sharing-card" key={`${record.grant_id}-${record.id}`}>
            <h2>{record.title}</h2>
            <p>{record.record_type} - shared by user {record.owner_user_id}</p>
            <label>Review note visible to user<textarea value={noteByRecord[record.id] ?? ""} onChange={(event) => setNoteByRecord({ ...noteByRecord, [record.id]: event.target.value })} /></label>
            <button className="button" onClick={() => saveNote(record)}>Save note</button>
          </article>
        ))}
      </div>
    </section>
  );
}
