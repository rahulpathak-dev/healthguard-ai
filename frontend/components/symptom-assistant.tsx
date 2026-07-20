"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";

type Profile = { id: string; display_name: string; kind: string };
type Bootstrap = { profiles: Profile[]; disclaimer: string };
type Guidance = {
  educational_explanation: string;
  possible_cause_categories: string[];
  urgency_level: string;
  red_flags: string[];
  when_to_seek_care: string;
  doctor_questions: string[];
  safe_self_care: string[];
  disclaimer: string;
  citations: Array<{ title: string; source: string; url: string; excerpt: string }>;
};
type Assessment = {
  id: string;
  profile_id: string;
  symptoms_json: string[];
  duration: string;
  severity: number;
  age_group: string;
  urgency_level: string;
  red_flags_json: string[];
  guidance_json: Guidance;
  created_at: string;
};

const warningOptions = [
  "chest pain",
  "cannot breathe",
  "severe bleeding",
  "unconscious",
  "stroke symptoms",
  "blue lips",
  "stiff neck",
];

export function SymptomAssistant() {
  const [setup, setSetup] = useState<Bootstrap | null>(null);
  const [profileId, setProfileId] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [duration, setDuration] = useState("");
  const [severity, setSeverity] = useState(5);
  const [ageGroup, setAgeGroup] = useState("adult");
  const [context, setContext] = useState("");
  const [associated, setAssociated] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [history, setHistory] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<Bootstrap>("/chat/bootstrap")
      .then((data) => {
        setSetup(data);
        setProfileId(data.profiles[0]?.id ?? "");
      })
      .catch((reason) =>
        setError(reason instanceof ApiError ? reason.message : "Symptom guidance could not load."),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!profileId) return;
    apiRequest<Assessment[]>(`/symptoms/assessments?profile_id=${profileId}`)
      .then(setHistory)
      .catch(() => undefined);
  }, [profileId, assessment?.id]);

  const symptomItems = useMemo(() => splitItems(symptoms), [symptoms]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!profileId || !symptomItems.length) {
      setError("Add at least one symptom and choose a profile.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await apiRequest<Assessment>("/symptoms/assessments", {
        method: "POST",
        body: JSON.stringify({
          profile_id: profileId,
          symptoms: symptomItems,
          duration,
          severity,
          age_group: ageGroup,
          relevant_context: context || null,
          associated_symptoms: splitItems(associated),
          emergency_warning_signs: warnings,
        }),
      });
      setAssessment(created);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Guidance could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <section className="symptom-shell" aria-busy="true">Loading symptom guidance...</section>;
  if (!setup) return <section className="symptom-shell" role="alert">{error}</section>;

  return (
    <section className="symptom-shell">
      <div className="symptom-intro">
        <p className="eyebrow">Non-diagnostic symptom guidance</p>
        <h1>Organize symptoms before care decisions.</h1>
        <p>
          This flow highlights urgency, red flags, and questions for a clinician. It does not
          diagnose or confirm conditions.
        </p>
      </div>
      <div className="symptom-grid">
        <form className="symptom-form" onSubmit={submit}>
          {error && <p className="form-error" role="alert">{error}</p>}
          <label>
            Profile
            <select value={profileId} onChange={(event) => setProfileId(event.target.value)}>
              {setup.profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>{profile.display_name}</option>
              ))}
            </select>
          </label>
          <label>
            Symptoms
            <input value={symptoms} onChange={(event) => setSymptoms(event.target.value)} placeholder="fever, cough, headache" />
          </label>
          <label>
            Duration
            <input value={duration} onChange={(event) => setDuration(event.target.value)} placeholder="2 days, since this morning" maxLength={120} />
          </label>
          <label>
            Severity: {severity}/10
            <input type="range" min="1" max="10" value={severity} onChange={(event) => setSeverity(Number(event.target.value))} />
          </label>
          <label>
            Age group
            <select value={ageGroup} onChange={(event) => setAgeGroup(event.target.value)}>
              <option value="adult">Adult</option>
              <option value="older_adult">Older adult</option>
              <option value="teen">Teen</option>
              <option value="child">Child</option>
              <option value="infant">Infant</option>
              <option value="pregnant">Pregnant</option>
            </select>
          </label>
          <label>
            Associated symptoms
            <input value={associated} onChange={(event) => setAssociated(event.target.value)} placeholder="nausea, rash, dizziness" />
          </label>
          <label>
            Relevant context
            <textarea value={context} onChange={(event) => setContext(event.target.value)} rows={4} maxLength={1000} placeholder="Recent travel, medicines, allergies, chronic conditions, or triggers" />
          </label>
          <fieldset>
            <legend>Emergency warning signs</legend>
            {warningOptions.map((option) => (
              <label key={option} className="check-row">
                <input type="checkbox" checked={warnings.includes(option)} onChange={() => toggleWarning(option, setWarnings)} />
                {option}
              </label>
            ))}
          </fieldset>
          <button className="button" disabled={submitting || !profileId} type="submit">
            {submitting ? "Reviewing..." : "Create guidance"}
          </button>
          <p className="symptom-disclaimer">{setup.disclaimer}</p>
        </form>
        <ResultPanel assessment={assessment} />
      </div>
      <section className="symptom-history">
        <h2>Recent symptom guidance</h2>
        {history.length ? history.map((item) => (
          <button key={item.id} onClick={() => setAssessment(item)}>
            <span>{item.symptoms_json.join(", ")}</span>
            <small>{item.urgency_level.replaceAll("_", " ")} - {new Date(item.created_at).toLocaleDateString()}</small>
          </button>
        )) : <p>No saved symptom guidance yet.</p>}
      </section>
    </section>
  );
}

function ResultPanel({ assessment }: { assessment: Assessment | null }) {
  if (!assessment) {
    return <aside className="symptom-result empty"><h2>Guidance will appear here</h2><p>Use this before a care conversation, not instead of one.</p></aside>;
  }
  const guidance = assessment.guidance_json;
  return (
    <aside className={`symptom-result urgency-${guidance.urgency_level}`}>
      <span className="urgency-label">{guidance.urgency_level.replaceAll("_", " ")}</span>
      <h2>Symptom guidance</h2>
      <p>{guidance.educational_explanation}</p>
      <h3>Possible categories of causes</h3>
      <ul>{guidance.possible_cause_categories.map((item) => <li key={item}>{item}</li>)}</ul>
      <h3>Red flags</h3>
      <ul>{guidance.red_flags.length ? guidance.red_flags.map((item) => <li key={item}>{item}</li>) : <li>No emergency red flags were selected or detected.</li>}</ul>
      <h3>When to seek care</h3>
      <p>{guidance.when_to_seek_care}</p>
      <h3>Questions for a doctor</h3>
      <ul>{guidance.doctor_questions.map((item) => <li key={item}>{item}</li>)}</ul>
      <h3>Safe self-care</h3>
      <ul>{guidance.safe_self_care.map((item) => <li key={item}>{item}</li>)}</ul>
      {guidance.citations.length > 0 && <h3>Citations</h3>}
      {guidance.citations.map((item) => <a key={item.url} href={item.url} target="_blank" rel="noreferrer">{item.source}: {item.title}</a>)}
      <p className="symptom-disclaimer">{guidance.disclaimer}</p>
    </aside>
  );
}

function splitItems(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean).slice(0, 8);
}

function toggleWarning(option: string, setWarnings: (updater: (items: string[]) => string[]) => void) {
  setWarnings((items) => items.includes(option) ? items.filter((item) => item !== option) : [...items, option]);
}
