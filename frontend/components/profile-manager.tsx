"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api-client";

type Item = { id: string; name?: string; substance?: string; reaction_summary?: string | null; severity?: "mild" | "moderate" | "severe" | null; dosage?: string | null; schedule?: string | null; reason?: string | null; summary?: string | null; diagnosed_on?: string | null };
type Contact = { id: string; name: string; relationship: string | null; phone: string; is_primary: boolean };
type Profile = {
  id: string; kind: "personal" | "family"; display_name: string; relationship: string | null;
  date_of_birth: string | null; age: number | null; blood_group: string | null;
  sex_at_birth: string | null; gender_identity: string | null; pronouns: string | null;
  avatar_url: string | null; notes: string | null; allow_doctor_access: boolean;
  share_with_family: boolean; can_edit: boolean; is_owner: boolean;
  emergency_contacts: Contact[]; allergies: Item[]; medicines: Item[];
  chronic_conditions: Item[];
};

const groups = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
const split = (value: FormDataEntryValue | null) => String(value ?? "").split(",").map((item) => item.trim()).filter(Boolean);
const rows = (value: FormDataEntryValue | null) => String(value ?? "").split(/\r?\n/).map((row) => row.split("|").map((part) => part.trim())).filter((row) => row[0]);
const line = (values: Array<string | null | undefined>) => { const parts = values.map((value) => value ?? ""); while (parts.at(-1) === "") parts.pop(); return parts.join(" | "); };
const initials = (name: string) => name.split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
const joined = (items: Item[], key: "name" | "substance") => items.map((item) => item[key]).filter(Boolean).join(", ");

export function ProfileManager() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState<"personal" | "family" | null>(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await apiRequest<Profile[]>("/profiles");
      setProfiles(data);
      setSelectedId((current) => data.some((profile) => profile.id === current) ? current : data[0]?.id ?? null);
    } catch { setError("Your health profiles could not be loaded."); }
    finally { setBusy(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);
  const selected = profiles.find((profile) => profile.id === selectedId) ?? profiles[0] ?? null;

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setNotice("");
    const values = new FormData(event.currentTarget);
    const contactName = String(values.get("contact_name") ?? "").trim();
    const contactPhone = String(values.get("contact_phone") ?? "").trim();
    if ((contactName && !contactPhone) || (!contactName && contactPhone)) { setError("Provide both an emergency contact name and phone number."); return; }
    const payload = {
      ...(creating ? { kind: creating } : {}),
      display_name: String(values.get("display_name") ?? "").trim(),
      relationship: (creating ?? selected?.kind) === "family" ? String(values.get("relationship") ?? "").trim() : null,
      date_of_birth: String(values.get("date_of_birth") ?? "") || null,
      blood_group: String(values.get("blood_group") ?? "") || null,
      sex_at_birth: String(values.get("sex_at_birth") ?? "").trim() || null,
      gender_identity: String(values.get("gender_identity") ?? "").trim() || null,
      pronouns: String(values.get("pronouns") ?? "").trim() || null,
      avatar_url: String(values.get("avatar_url") ?? "").trim() || null,
      locale: navigator.language || null,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || null,
      notes: String(values.get("notes") ?? "").trim() || null,
      allow_doctor_access: values.get("allow_doctor_access") === "on",
      share_with_family: values.get("share_with_family") === "on",
      emergency_contacts: contactName && contactPhone ? [{ name: contactName, phone: contactPhone, relationship: String(values.get("contact_relationship") ?? "").trim() || null, is_primary: true }, ...(selected?.emergency_contacts.slice(1).map(({ name, phone, relationship }) => ({ name, phone, relationship, is_primary: false })) ?? [])] : [],
      allergies: split(values.get("allergies")).map((substance) => { const existing = selected?.allergies.find((item) => item.substance?.toLowerCase() === substance.toLowerCase()); return { substance, reaction_summary: existing?.reaction_summary ?? null, severity: existing?.severity ?? null }; }),
      medicines: rows(values.get("medicines")).map(([name, dosage, schedule, reason]) => ({ name, dosage: dosage || null, schedule: schedule || null, reason: reason || null })),
      chronic_conditions: rows(values.get("conditions")).map(([name, summary, diagnosed_on]) => ({ name, summary: summary || null, diagnosed_on: diagnosed_on || null })),
    };
    try {
      const saved = await apiRequest<Profile>(creating ? "/profiles" : `/profiles/${selected?.id}`, {
        method: creating ? "POST" : "PATCH", body: JSON.stringify(payload),
      });
      await load(); setSelectedId(saved.id); setCreating(null); setEditing(false);
      setNotice("Profile saved securely.");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "The profile could not be saved.");
    }
  }

  async function remove() {
    if (!selected || !window.confirm(`Delete ${selected.display_name}'s profile and health records?`)) return;
    try {
      await apiRequest(`/profiles/${selected.id}`, { method: "DELETE" });
      setSelectedId(null); await load(); setNotice("Family profile deleted.");
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "The profile could not be deleted."); }
  }

  if (busy) return <p className="profile-status" role="status">Loading health profiles...</p>;
  const personalExists = profiles.some((profile) => profile.kind === "personal" && profile.is_owner);
  return <section className="profiles-shell"><header className="profiles-heading"><div><p className="eyebrow">Health profiles</p><h1>Care information for you and your family.</h1><p>Only a name is required. Add sensitive details only when they are useful to you.</p></div><div className="profile-actions">{!personalExists && <button onClick={() => setCreating("personal")}>Create my profile</button>}<button className="button-secondary" onClick={() => setCreating("family")}>Add family member</button></div></header>{error && <p className="form-error" role="alert">{error}</p>}{notice && <p className="form-success" role="status">{notice}</p>}{profiles.length > 0 && <div className="profile-switcher" role="group" aria-label="Switch health profile">{profiles.map((profile) => <button type="button" className={profile.id === selected?.id && !creating ? "active" : ""} key={profile.id} onClick={() => { setSelectedId(profile.id); setCreating(null); setEditing(false); }}><Avatar name={profile.display_name} /><span><b>{profile.display_name}</b><small>{profile.kind === "personal" ? "My profile" : profile.relationship || "Family"}</small></span></button>)}</div>}{(creating || (selected && editing)) && <ProfileForm profile={creating ? null : selected} kind={creating ?? selected?.kind ?? "personal"} onSubmit={save} onCancel={() => { setCreating(null); setEditing(false); }} />}{selected && !creating && !editing && <ProfileDetails profile={selected} onEdit={() => setEditing(true)} onDelete={remove} />}{profiles.length === 0 && !creating && <div className="empty-profiles"><Avatar name="+" /><h2>Create your private health profile</h2><p>You can leave demographic and health fields blank and add them later.</p></div>}</section>;
}

function Avatar({ name }: { name: string }) { return <span className="profile-avatar" aria-hidden="true">{name === "+" ? "+" : initials(name)}</span>; }

function ProfileDetails({ profile, onEdit, onDelete }: { profile: Profile; onEdit: () => void; onDelete: () => void }) {
  return <div className="profile-detail"><article className="profile-summary-card"><div className="profile-title"><Avatar name={profile.display_name} /><div><span>{profile.kind === "personal" ? "Personal profile" : profile.relationship}</span><h2>{profile.display_name}</h2><p>{profile.age === null ? "Age not provided" : `${profile.age} years`}{profile.blood_group ? ` - ${profile.blood_group}` : ""}</p></div></div><div className="profile-actions">{profile.can_edit && <button onClick={onEdit}>Edit profile</button>}{profile.kind === "family" && profile.is_owner && <button className="danger-button" onClick={onDelete}>Delete family profile</button>}</div><dl className="profile-facts"><div><dt>Pronouns</dt><dd>{profile.pronouns || "Not provided"}</dd></div><div><dt>Emergency contact</dt><dd>{profile.emergency_contacts[0]?.name || "Not provided"}</dd></div><div><dt>Access</dt><dd>{profile.is_owner ? "Owned by you" : profile.can_edit ? "Shared edit access" : "Shared view access"}</dd></div></dl></article><div className="health-record-grid"><RecordCard title="Allergies" values={profile.allergies.map((item) => item.substance || "")} /><RecordCard title="Current medicines" values={profile.medicines.map((item) => `${item.name || ""}${item.dosage ? ` - ${item.dosage}` : ""}${item.schedule ? `, ${item.schedule}` : ""}`)} /><RecordCard title="Chronic conditions" values={profile.chronic_conditions.map((item) => `${item.name || ""}${item.summary ? `: ${item.summary}` : ""}`)} /><article className="record-card"><h3>Privacy controls</h3><p>{profile.allow_doctor_access ? "Doctor sharing is allowed when explicitly granted." : "Doctor sharing is off."}</p><p>{profile.share_with_family ? "Family sharing is allowed when explicitly granted." : "Family sharing is off."}</p><small>Preferences never grant access by themselves. A specific permission is required.</small></article></div></div>;
}

function RecordCard({ title, values }: { title: string; values: string[] }) {
  const present = values.filter(Boolean);
  return <article className="record-card"><h3>{title}</h3>{present.length ? <ul>{present.map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul> : <p>Nothing recorded</p>}</article>;
}

function ProfileForm({ profile, kind, onSubmit, onCancel }: { profile: Profile | null; kind: "personal" | "family"; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onCancel: () => void }) {
  const contact = profile?.emergency_contacts[0];
  return <form className="profile-form" onSubmit={onSubmit}><section><h2>{profile ? "Edit" : "Create"} {kind} profile</h2><p>Fields marked optional may be left blank.</p><div className="form-grid"><label>Display name *<input name="display_name" defaultValue={profile?.display_name} maxLength={120} required /></label>{kind === "family" && <label>Relationship *<input name="relationship" defaultValue={profile?.relationship ?? ""} maxLength={80} required /></label>}<label>Date of birth <span>Optional</span><input name="date_of_birth" type="date" max={new Date().toISOString().slice(0, 10)} defaultValue={profile?.date_of_birth ?? ""} /></label><label>Blood group <span>Optional</span><select name="blood_group" defaultValue={profile?.blood_group ?? ""}>{groups.map((group) => <option value={group} key={group}>{group || "Not provided"}</option>)}</select></label><label>Sex at birth <span>Optional</span><input name="sex_at_birth" defaultValue={profile?.sex_at_birth ?? ""} maxLength={40} /></label><label>Gender identity <span>Optional</span><input name="gender_identity" defaultValue={profile?.gender_identity ?? ""} maxLength={80} /></label><label>Pronouns <span>Optional</span><input name="pronouns" defaultValue={profile?.pronouns ?? ""} maxLength={40} /></label><label>Avatar HTTPS URL <span>Optional</span><input name="avatar_url" type="url" pattern="https://.*" defaultValue={profile?.avatar_url ?? ""} /></label></div></section><section><h2>Health overview</h2><p>Separate multiple items with commas.</p><div className="form-grid"><label>Allergies<input name="allergies" defaultValue={profile ? joined(profile.allergies, "substance") : ""} /></label><label>Current medicines <span>One per line: name | dose | schedule | reason</span><textarea name="medicines" rows={4} defaultValue={profile?.medicines.map((item) => line([item.name, item.dosage, item.schedule, item.reason])).join("\n") ?? ""} /></label><label>Chronic conditions <span>One per line: name | summary | diagnosis date</span><textarea name="conditions" rows={4} defaultValue={profile?.chronic_conditions.map((item) => line([item.name, item.summary, item.diagnosed_on])).join("\n") ?? ""} /></label><label className="full-field">Private notes <span>Optional</span><textarea name="notes" defaultValue={profile?.notes ?? ""} maxLength={4000} rows={3} /></label></div></section><section><h2>Emergency contact</h2><div className="form-grid"><label>Name <span>Optional</span><input name="contact_name" defaultValue={contact?.name ?? ""} maxLength={120} /></label><label>Phone <span>Optional</span><input name="contact_phone" type="tel" defaultValue={contact?.phone ?? ""} pattern="[0-9+() .-]{7,32}" /></label><label>Relationship <span>Optional</span><input name="contact_relationship" defaultValue={contact?.relationship ?? ""} maxLength={80} /></label></div></section><fieldset className="privacy-options"><legend>Privacy preferences</legend><label><input name="allow_doctor_access" type="checkbox" defaultChecked={profile?.allow_doctor_access} /> Permit explicit doctor sharing</label><label><input name="share_with_family" type="checkbox" defaultChecked={profile?.share_with_family} /> Permit explicit family sharing</label><p>These settings never share data automatically.</p></fieldset><div className="form-buttons"><button type="submit">Save profile</button><button type="button" className="button-secondary" onClick={onCancel}>Cancel</button></div></form>;
}
