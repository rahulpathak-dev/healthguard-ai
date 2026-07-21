"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";
import { env } from "@/lib/env";

type Profile = { id: string; display_name: string; kind: string };
type Bootstrap = { profiles: Profile[] };
type RecordItem = {
  id: string;
  profile_id: string;
  title: string;
  record_type: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: string;
  scan_status: string;
  tags_json: string[];
  metadata_json: Record<string, unknown>;
  occurred_at: string | null;
  created_at: string;
  archived_at: string | null;
  deleted_at: string | null;
};

export function MedicalRecordOrganizer() {
  const [setup, setSetup] = useState<Bootstrap | null>(null);
  const [profileId, setProfileId] = useState("");
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [recordType, setRecordType] = useState("");
  const [tag, setTag] = useState("");
  const [title, setTitle] = useState("");
  const [uploadType, setUploadType] = useState("lab_report");
  const [tags, setTags] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<Bootstrap>("/chat/bootstrap")
      .then((data) => {
        setSetup(data);
        setProfileId(data.profiles[0]?.id ?? "");
      })
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Records could not load.",
        ),
      );
  }, []);

  useEffect(() => {
    if (!profileId) return;
    loadRecords();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId, query, recordType, tag]);

  async function loadRecords() {
    const params = new URLSearchParams({ profile_id: profileId });
    if (query) params.set("q", query);
    if (recordType) params.set("record_type", recordType);
    if (tag) params.set("tag", tag);
    const data = await apiRequest<RecordItem[]>(`/records?${params}`);
    setRecords(data);
    setSelected((current) =>
      current && data.some((item) => item.id === current.id)
        ? current
        : (data[0] ?? null),
    );
  }

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file || !profileId) {
      setError("Choose a profile and file.");
      return;
    }
    setUploading(true);
    setProgress(15);
    setError("");
    try {
      const body = new FormData();
      body.set("profile_id", profileId);
      body.set("title", title || file.name);
      body.set("record_type", uploadType);
      body.set("tags", tags);
      body.set("file", file);
      setProgress(45);
      const response = await fetch(`${env.NEXT_PUBLIC_API_URL}/records`, {
        method: "POST",
        credentials: "include",
        body,
      });
      setProgress(80);
      if (!response.ok) throw new Error("Upload failed");
      setTitle("");
      setTags("");
      setFile(null);
      setProgress(100);
      await loadRecords();
    } catch {
      setError("Upload failed validation or could not be stored.");
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 700);
    }
  }

  async function download(record: RecordItem) {
    try {
      const access = await apiRequest<{ url: string }>(
        `/records/${record.id}/download-url`,
        {
          method: "POST",
        },
      );
      window.open(
        `${env.NEXT_PUBLIC_API_URL}${access.url}`,
        "_blank",
        "noopener,noreferrer",
      );
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "File is not available yet.",
      );
    }
  }

  async function archive(record: RecordItem) {
    await apiRequest(`/records/${record.id}/archive`, { method: "POST" });
    await loadRecords();
  }

  async function remove(record: RecordItem) {
    if (
      !window.confirm(
        `Securely delete ${record.title}? This removes the stored file.`,
      )
    )
      return;
    await apiRequest(`/records/${record.id}`, { method: "DELETE" });
    await loadRecords();
  }

  const timeline = useMemo(() => groupByMonth(records), [records]);

  return (
    <section className="records-shell">
      <div className="records-intro">
        <p className="eyebrow">Private medical record organizer</p>
        <h1>Keep health files organized and private.</h1>
        <p>
          Uploads are validated and quarantined for malware scanning before
          files become available.
        </p>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="records-grid">
        <aside className="records-panel">
          <label>
            Profile
            <select
              value={profileId}
              onChange={(event) => setProfileId(event.target.value)}
            >
              {setup?.profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.display_name}
                </option>
              ))}
            </select>
          </label>
          <form className="record-upload" onSubmit={upload}>
            <h2>Upload record</h2>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Record title"
            />
            <select
              value={uploadType}
              onChange={(event) => setUploadType(event.target.value)}
            >
              <option value="lab_report">Lab report</option>
              <option value="imaging">Imaging</option>
              <option value="prescription">Prescription</option>
              <option value="discharge_summary">Discharge summary</option>
              <option value="vaccination">Vaccination</option>
              <option value="insurance">Insurance</option>
              <option value="other">Other</option>
            </select>
            <input
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              placeholder="tags: cardiology, 2026"
            />
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.txt"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            {progress > 0 && <progress max={100} value={progress} />}
            <button className="button" disabled={uploading || !file}>
              {uploading ? "Uploading..." : "Upload securely"}
            </button>
            <small>
              Allowed: PDF, PNG, JPG, JPEG, TXT. Files remain private and
              quarantined until scanned.
            </small>
          </form>
          <div className="record-filters">
            <h2>Search and filters</h2>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search title"
            />
            <input
              value={tag}
              onChange={(event) => setTag(event.target.value)}
              placeholder="Filter tag"
            />
            <select
              value={recordType}
              onChange={(event) => setRecordType(event.target.value)}
            >
              <option value="">All categories</option>
              <option value="lab_report">Lab report</option>
              <option value="imaging">Imaging</option>
              <option value="prescription">Prescription</option>
              <option value="other">Other</option>
            </select>
          </div>
        </aside>
        <section className="record-timeline">
          <h2>Timeline</h2>
          {timeline.map(([month, items]) => (
            <div key={month}>
              <h3>{month}</h3>
              {items.map((item) => (
                <button
                  className={selected?.id === item.id ? "active" : ""}
                  key={item.id}
                  onClick={() => setSelected(item)}
                >
                  <span>{item.title}</span>
                  <small>
                    {item.record_type.replaceAll("_", " ")} - {item.status}
                  </small>
                </button>
              ))}
            </div>
          ))}
          {!records.length && <p>No records yet.</p>}
        </section>
        <aside className="record-detail">
          {selected ? (
            <>
              <span className="record-status">
                {selected.status} / {selected.scan_status}
              </span>
              <h2>{selected.title}</h2>
              <p>{selected.original_filename}</p>
              <dl>
                <dt>Category</dt>
                <dd>{selected.record_type.replaceAll("_", " ")}</dd>
                <dt>Size</dt>
                <dd>{Math.round(selected.file_size_bytes / 1024)} KB</dd>
                <dt>Created</dt>
                <dd>{new Date(selected.created_at).toLocaleString()}</dd>
                <dt>Tags</dt>
                <dd>{selected.tags_json.join(", ") || "None"}</dd>
              </dl>
              <div className="record-actions">
                <button onClick={() => download(selected)}>Download</button>
                <button onClick={() => archive(selected)}>Archive</button>
                <button onClick={() => remove(selected)}>Secure delete</button>
              </div>
              {selected.scan_status !== "clean" && (
                <p className="record-warning">
                  File preview and download stay locked until malware scanning
                  marks this record clean.
                </p>
              )}
            </>
          ) : (
            <p>Select a record to view details.</p>
          )}
        </aside>
      </div>
    </section>
  );
}

function groupByMonth(records: RecordItem[]): Array<[string, RecordItem[]]> {
  const groups = new Map<string, RecordItem[]>();
  for (const record of records) {
    const month = new Date(
      record.occurred_at ?? record.created_at,
    ).toLocaleDateString(undefined, { month: "long", year: "numeric" });
    groups.set(month, [...(groups.get(month) ?? []), record]);
  }
  return [...groups.entries()];
}
