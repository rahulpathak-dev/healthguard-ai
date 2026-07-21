"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";

type Profile = { id: string; display_name: string };
type RecordItem = {
  id: string;
  title: string;
  status: string;
  scan_status: string;
};
type Analysis = {
  id: string;
  title: string;
  status: string;
  ocr_status: string;
  ocr_confidence: number | null;
  extracted_values_json: Array<Record<string, unknown>>;
  explanation_json: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
};

export function ReportExplanationCenter() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState("");
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [recordId, setRecordId] = useState("");
  const [history, setHistory] = useState<Analysis[]>([]);
  const [active, setActive] = useState<Analysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<{ profiles: Profile[] }>("/chat/bootstrap")
      .then((data) => {
        setProfiles(data.profiles);
        setProfileId(data.profiles[0]?.id ?? "");
      })
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Reports could not load.",
        ),
      );
    loadHistory();
  }, []);

  useEffect(() => {
    if (!profileId) return;
    apiRequest<RecordItem[]>(
      `/records?profile_id=${profileId}&record_type=lab_report&include_archived=true`,
    )
      .then((items) => {
        setRecords(items);
        setRecordId(items[0]?.id ?? "");
      })
      .catch(() => undefined);
  }, [profileId]);

  async function loadHistory() {
    apiRequest<Analysis[]>("/reports/analyses")
      .then(setHistory)
      .catch(() => undefined);
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!recordId) return;
    try {
      const created = await apiRequest<Analysis>("/reports/analyses", {
        method: "POST",
        body: JSON.stringify({ record_id: recordId }),
      });
      setActive(created);
      await loadHistory();
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Analysis could not be started.",
      );
    }
  }

  async function retry(item: Analysis) {
    const updated = await apiRequest<Analysis>(
      `/reports/analyses/${item.id}/retry`,
      { method: "POST" },
    );
    setActive(updated);
    await loadHistory();
  }

  return (
    <section className="reports-shell">
      <div className="reports-intro">
        <p className="eyebrow">OCR report explanation</p>
        <h1>Explain report values without diagnosing.</h1>
        <p>
          Uses ranges printed on the report where readable and highlights OCR
          uncertainty.
        </p>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="reports-grid">
        <form className="report-panel" onSubmit={create}>
          <h2>Start from a record</h2>
          <select
            value={profileId}
            onChange={(event) => setProfileId(event.target.value)}
          >
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.display_name}
              </option>
            ))}
          </select>
          <select
            value={recordId}
            onChange={(event) => setRecordId(event.target.value)}
          >
            {records.map((record) => (
              <option key={record.id} value={record.id}>
                {record.title} ({record.status}/{record.scan_status})
              </option>
            ))}
          </select>
          <button className="button" disabled={!recordId}>
            Create explanation
          </button>
          <small>
            Records must be scanned clean before OCR processing runs.
          </small>
        </form>
        <section className="report-result">
          {active ? (
            <ReportResult item={active} onRetry={() => retry(active)} />
          ) : (
            <p>Select an analysis from history or create a new one.</p>
          )}
        </section>
        <aside className="report-panel">
          <h2>History</h2>
          {history.map((item) => (
            <button key={item.id} onClick={() => setActive(item)}>
              {item.title}
              <small>
                {item.status} - {new Date(item.created_at).toLocaleDateString()}
              </small>
            </button>
          ))}
        </aside>
      </div>
    </section>
  );
}

function ReportResult({
  item,
  onRetry,
}: {
  item: Analysis;
  onRetry: () => void;
}) {
  const values = item.extracted_values_json;
  return (
    <>
      <span className="report-status">
        {item.status} / {item.ocr_status}
      </span>
      <h2>{item.title}</h2>
      {item.error_message && (
        <p className="record-warning">{item.error_message}</p>
      )}
      {item.ocr_confidence !== null && (
        <p>
          OCR confidence: {Math.round(item.ocr_confidence * 100)}%. Review the
          original report.
        </p>
      )}
      <ul>
        {values.map((value, index) => (
          <li key={index}>
            {String(value.label)}: {String(value.value)}{" "}
            {String(value.unit ?? "")} range{" "}
            {String(value.reference_range ?? "unreadable")} -{" "}
            {String(value.flag)}
          </li>
        ))}
      </ul>
      <button onClick={onRetry}>Retry OCR</button>
    </>
  );
}
