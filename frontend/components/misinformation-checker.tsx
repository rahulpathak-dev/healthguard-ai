"use client";

import React from "react";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";

type Check = {
  id: string;
  claim_summary: string;
  verdict: string;
  evidence_json: {
    evidence_analysis?: string;
    trusted_sources?: Array<{
      title: string;
      source: string;
      url: string;
      excerpt: string;
    }>;
    missing_context?: string[];
    harm_warning?: string;
    uncertainty?: string;
    safe_next_steps?: string[];
  };
  created_at: string;
};

export function MisinformationChecker() {
  const [claim, setClaim] = useState("");
  const [active, setActive] = useState<Check | null>(null);
  const [history, setHistory] = useState<Check[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    apiRequest<Check[]>("/misinformation/checks")
      .then(setHistory)
      .catch(() => undefined);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await apiRequest<Check>("/misinformation/checks", {
        method: "POST",
        body: JSON.stringify({ claim }),
      });
      setActive(result);
      await loadHistory();
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Claim could not be checked.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function feedback(rating: "helpful" | "not_helpful" | "unsafe") {
    if (!active) return;
    await apiRequest(`/misinformation/checks/${active.id}/feedback`, {
      method: "PUT",
      body: JSON.stringify({ rating }),
    });
  }

  return (
    <section className="misinfo-shell">
      <div className="misinfo-intro">
        <p className="eyebrow">Evidence-based claim check</p>
        <h1>Paste a health claim.</h1>
        <p>
          Verdicts use retrieval from approved sources, not the model&apos;s own
          belief.
        </p>
      </div>
      <div className="misinfo-grid">
        <form className="misinfo-panel" onSubmit={submit}>
          {error && <p className="form-error">{error}</p>}
          <textarea
            value={claim}
            onChange={(event) => setClaim(event.target.value)}
            maxLength={4000}
            rows={8}
            placeholder="Paste a claim, caption, message, or article excerpt..."
          />
          <button
            className="button"
            disabled={loading || claim.trim().length < 10}
          >
            {loading ? "Checking..." : "Check claim"}
          </button>
        </form>
        <section className="misinfo-result">
          {active ? (
            <>
              <span>{active.verdict.replaceAll("_", " ")}</span>
              <h2>{active.claim_summary}</h2>
              <p>{active.evidence_json.evidence_analysis}</p>
              <h3>Trusted sources</h3>
              {active.evidence_json.trusted_sources?.map((source) => (
                <a
                  key={source.url}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {source.source}: {source.title}
                </a>
              ))}
              <h3>Missing context</h3>
              <ul>
                {active.evidence_json.missing_context?.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p className="record-warning">
                {active.evidence_json.harm_warning}
              </p>
              <p>{active.evidence_json.uncertainty}</p>
              <button onClick={() => feedback("helpful")}>Helpful</button>
              <button onClick={() => feedback("not_helpful")}>
                Not helpful
              </button>
              <button onClick={() => feedback("unsafe")}>Report unsafe</button>
            </>
          ) : (
            <p>Results will appear here.</p>
          )}
        </section>
        <aside className="misinfo-panel">
          <h2>History</h2>
          {history.map((item) => (
            <button key={item.id} onClick={() => setActive(item)}>
              {item.verdict.replaceAll("_", " ")}
              <small>{item.claim_summary}</small>
            </button>
          ))}
        </aside>
      </div>
    </section>
  );
}
