"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api-client";

type Profile = { id: string; display_name: string };
type Reminder = {
  id: string;
  title: string;
  category: string;
  due_at: string;
  timezone: string;
  recurrence_rule: string;
  status: string;
  snoozed_until: string | null;
};

export function ReminderCenter() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState("");
  const [items, setItems] = useState<Reminder[]>([]);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("doctor_appointment");
  const [dueAt, setDueAt] = useState("");
  const [timezone, setTimezone] = useState("Asia/Calcutta");
  const [recurrence, setRecurrence] = useState("none");
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<{ profiles: Profile[] }>("/chat/bootstrap").then((data) => {
      setProfiles(data.profiles);
      setProfileId(data.profiles[0]?.id ?? "");
    });
    load();
  }, []);

  async function load() {
    setItems(await apiRequest<Reminder[]>("/reminders"));
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await apiRequest("/reminders", {
        method: "POST",
        body: JSON.stringify({
          profile_id: profileId,
          title,
          category,
          due_at: new Date(dueAt).toISOString(),
          timezone,
          recurrence,
        }),
      });
      setTitle("");
      await load();
    } catch {
      setError(
        "Reminder could not be saved. Check wording, date, timezone, and profile access.",
      );
    }
  }

  async function action(path: string) {
    await apiRequest(path, { method: "POST" });
    await load();
  }

  return (
    <section className="reminders-shell">
      <div className="reminders-intro">
        <p className="eyebrow">Reminders and notifications</p>
        <h1>Keep care tasks on time.</h1>
        <p>
          Supports appointments, medicines as prescribed, vaccinations, tests,
          and follow-ups.
        </p>
      </div>
      {error && <p className="form-error">{error}</p>}
      <div className="reminders-grid">
        <form className="reminder-panel" onSubmit={create}>
          <h2>Create reminder</h2>
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
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Reminder title"
          />
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="doctor_appointment">Doctor appointment</option>
            <option value="medicine_schedule">Medicine schedule</option>
            <option value="vaccination">Vaccination</option>
            <option value="health_check">Health check</option>
            <option value="test">Test</option>
            <option value="follow_up">Follow-up</option>
          </select>
          <input
            type="datetime-local"
            value={dueAt}
            onChange={(event) => setDueAt(event.target.value)}
          />
          <input
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
          />
          <select
            value={recurrence}
            onChange={(event) => setRecurrence(event.target.value)}
          >
            <option value="none">One time</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button className="button">Save reminder</button>
        </form>
        <section className="reminder-list">
          <h2>Upcoming</h2>
          {items.map((item) => (
            <article key={item.id}>
              <span>{item.category.replaceAll("_", " ")}</span>
              <h3>{item.title}</h3>
              <p>
                {new Date(item.due_at).toLocaleString()} · {item.timezone} ·{" "}
                {item.recurrence_rule}
              </p>
              <button
                onClick={() =>
                  action(`/reminders/${item.id}/snooze?minutes=30`)
                }
              >
                Snooze
              </button>
              <button onClick={() => action(`/reminders/${item.id}/complete`)}>
                Complete
              </button>
            </article>
          ))}
        </section>
      </div>
    </section>
  );
}
