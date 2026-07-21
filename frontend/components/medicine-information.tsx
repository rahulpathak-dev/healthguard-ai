"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";

type Reference = {
  title: string;
  source: string;
  url: string;
  excerpt: string;
};
type MedicineInfo = {
  query: string;
  generic_name: string | null;
  brand_names: string[];
  common_uses: string[];
  common_side_effects: string[];
  serious_warnings: string[];
  precautions: string[];
  interactions: string[];
  storage_information: string[];
  pregnancy_child_elderly_cautions: string[];
  spelling_suggestions: string[];
  source_references: Reference[];
  disclaimer: string;
  unsupported_notice: string | null;
};
type HistoryItem = {
  id: string;
  query: string;
  matched_generic_name: string | null;
  source_count: number;
  created_at: string;
};

export function MedicineInformationPlatform() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<MedicineInfo | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    apiRequest<HistoryItem[]>("/medicines/history")
      .then(setHistory)
      .catch(() => undefined);
  }

  async function search(event?: FormEvent, override?: string) {
    event?.preventDefault();
    const value = (override ?? query).trim();
    if (value.length < 2) {
      setError("Enter at least two characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest<MedicineInfo>(
        `/medicines/search?q=${encodeURIComponent(value)}`,
      );
      setResult(data);
      setQuery(value);
      await loadHistory();
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Medicine information could not load.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="medicine-shell">
      <div className="medicine-intro">
        <p className="eyebrow">Verified medicine education</p>
        <h1>Search medicine information safely.</h1>
        <p>
          Look up general uses, warnings, precautions, interactions, storage,
          and special population cautions from verified references. This tool
          does not give dosing or treatment instructions.
        </p>
      </div>
      <div className="medicine-grid">
        <aside className="medicine-search-panel">
          <form onSubmit={search}>
            <label htmlFor="medicine-search">Medicine name</label>
            <div className="medicine-search-row">
              <input
                id="medicine-search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="acetaminophen, ibuprofen, Tylenol"
              />
              <button className="button" disabled={loading}>
                {loading ? "Searching..." : "Search"}
              </button>
            </div>
          </form>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {result?.spelling_suggestions.length ? (
            <div className="medicine-suggestions">
              <h2>Did you mean?</h2>
              {result.spelling_suggestions.map((item) => (
                <button key={item} onClick={() => search(undefined, item)}>
                  {item}
                </button>
              ))}
            </div>
          ) : null}
          <div className="medicine-history">
            <h2>Search history</h2>
            {history.length ? (
              history.map((item) => (
                <button
                  key={item.id}
                  onClick={() => search(undefined, item.query)}
                >
                  <span>{item.query}</span>
                  <small>
                    {item.matched_generic_name ?? "No verified match"} -{" "}
                    {item.source_count} sources
                  </small>
                </button>
              ))
            ) : (
              <p>No searches yet.</p>
            )}
          </div>
        </aside>
        <MedicineResult result={result} />
      </div>
    </section>
  );
}

function MedicineResult({ result }: { result: MedicineInfo | null }) {
  if (!result) {
    return (
      <section className="medicine-result empty">
        <h2>Medicine details will appear here</h2>
        <p>Search by generic or common brand name.</p>
      </section>
    );
  }
  return (
    <section className="medicine-result">
      {result.unsupported_notice && (
        <p className="medicine-warning">{result.unsupported_notice}</p>
      )}
      <span className="medicine-label">Generic name</span>
      <h2>{result.generic_name ?? "No verified match"}</h2>
      {result.brand_names.length > 0 && (
        <p>
          <b>Brand examples:</b> {result.brand_names.join(", ")}. Availability
          and naming vary by country.
        </p>
      )}
      <InfoList title="Common uses" items={result.common_uses} />
      <InfoList
        title="Common side effects"
        items={result.common_side_effects}
      />
      <InfoList
        title="Serious warnings"
        items={result.serious_warnings}
        important
      />
      <InfoList title="Precautions" items={result.precautions} />
      <InfoList title="Interactions" items={result.interactions} />
      <InfoList
        title="Storage information"
        items={result.storage_information}
      />
      <InfoList
        title="Pregnancy, child, and elderly cautions"
        items={result.pregnancy_child_elderly_cautions}
      />
      <h3>Source references</h3>
      {result.source_references.length ? (
        result.source_references.map((source) => (
          <a
            className="medicine-source"
            key={source.url}
            href={source.url}
            target="_blank"
            rel="noreferrer"
          >
            <span>{source.source}</span>
            <b>{source.title}</b>
            <small>{source.excerpt}</small>
          </a>
        ))
      ) : (
        <p>No approved source reference is available for this query.</p>
      )}
      <p className="medicine-disclaimer">{result.disclaimer}</p>
    </section>
  );
}

function InfoList({
  title,
  items,
  important = false,
}: {
  title: string;
  items: string[];
  important?: boolean;
}) {
  return (
    <section
      className={important ? "medicine-section important" : "medicine-section"}
    >
      <h3>{title}</h3>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>Not available from verified local sources for this search.</p>
      )}
    </section>
  );
}
