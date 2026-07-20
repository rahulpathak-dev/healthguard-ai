"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { ApiError, apiRequest } from "@/lib/api-client";

type Profile = { id: string; display_name: string; kind: string; relationship: string | null; is_owner: boolean; can_edit: boolean };
type TimedItem = { id: string; title: string; category?: string; due_at?: string; created_at?: string; last_message_at?: string; record_type?: string; status?: string };
type Family = { id: string; display_name: string; relationship: string | null; age: number | null };
type Dashboard = {
  welcome_name: string; profiles: Profile[]; active_profile: Profile | null;
  upcoming_reminders: TimedItem[]; recent_records: TimedItem[]; report_analyses: TimedItem[];
  recent_conversations: TimedItem[]; notifications: TimedItem[]; unread_notification_count: number;
  family: Family[]; privacy: { access_label: string; permission_count: number; doctor_sharing_enabled: boolean; family_sharing_enabled: boolean } | null;
  education: Array<{ slug: string; title: string; description: string; reading_minutes: number }>;
  quick_actions: Array<{ label: string; href: string; available: boolean }>;
  emergency_shortcuts: Array<{ label: string; description: string; action: string }>;
};

const when = (value?: string) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Date not provided";

export function HealthDashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [requestedProfile, setRequestedProfile] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let ignore = false;
    setLoading(true); setError("");
    const query = requestedProfile ? `?profile_id=${encodeURIComponent(requestedProfile)}` : "";
    apiRequest<Dashboard>(`/dashboard${query}`)
      .then((result) => { if (!ignore) setData(result); })
      .catch((reason) => { if (!ignore) setError(reason instanceof ApiError ? reason.message : "The dashboard could not be loaded."); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [requestedProfile, retry]);

  if (loading && !data) return <DashboardLoading />;
  if (error && !data) return <section className="dashboard-shell"><div className="dashboard-error" role="alert"><h1>We could not load your dashboard</h1><p>{error}</p><button onClick={() => setRetry((value) => value + 1)}>Try again</button></div></section>;
  if (!data) return null;

  return <section className="dashboard-shell" aria-busy={loading}><header className="dashboard-header"><div><p className="eyebrow">Your health overview</p><h1>Welcome, {data.welcome_name}.</h1><p>A calm view of what may need your attention today.</p></div><div className="dashboard-controls"><label>Active profile<select value={data.active_profile?.id ?? ""} onChange={(event) => setRequestedProfile(event.target.value)} disabled={!data.profiles.length}>{!data.profiles.length && <option value="">No profile yet</option>}{data.profiles.map((profile) => <option value={profile.id} key={profile.id}>{profile.display_name}{profile.kind === "family" ? ` (${profile.relationship || "family"})` : ""}</option>)}</select></label><div className="notification-count" aria-label={`${data.unread_notification_count} unread notifications`}><span aria-hidden="true">!</span><b>{data.unread_notification_count}</b></div></div></header>{error && <p className="form-error" role="alert">{error}</p>}{loading && <div className="dashboard-refresh" role="status">Switching profile...</div>}{!data.active_profile ? <NoProfile /> : <><div className="quick-actions" aria-label="Quick actions">{data.quick_actions.map((action) => action.available ? <Link href={action.href} key={action.label}>{action.label}<span aria-hidden="true">-&gt;</span></Link> : <button type="button" disabled key={action.label}>{action.label}<small>Coming soon</small></button>)}</div><div className="dashboard-grid"><DashboardCard id="reminders" title="Upcoming reminders" eyebrow="Next up" className="span-two"><ItemList items={data.upcoming_reminders} empty="No upcoming reminders" detail={(item) => `${item.category || "Reminder"} - ${when(item.due_at)}`} /></DashboardCard><DashboardCard id="records" title="Recent medical records" eyebrow="Records"><ItemList items={data.recent_records} empty="No medical records yet" detail={(item) => `${item.record_type || "Record"} - ${when(item.created_at)}`} /></DashboardCard><EmergencyCard items={data.emergency_shortcuts} /><DashboardCard title="Report analysis history" eyebrow="Reports"><ItemList items={data.report_analyses} empty="No reports have been analyzed" detail={(item) => `${item.status || "Pending"} - ${when(item.created_at)}`} /></DashboardCard><DashboardCard id="conversations" title="Recent AI conversations" eyebrow="Conversations"><ItemList items={data.recent_conversations} empty="No conversations yet" detail={(item) => when(item.last_message_at)} /></DashboardCard><DashboardCard title="Unread notifications" eyebrow={`${data.unread_notification_count} unread`}><ItemList items={data.notifications} empty="You are all caught up" detail={(item) => `${item.category || "Update"} - ${when(item.created_at)}`} /></DashboardCard><FamilyCard family={data.family} /><PrivacyCard privacy={data.privacy} /></div></>}
    <section className="wellness-section" aria-labelledby="wellness-heading"><div><p className="eyebrow">Wellness education</p><h2 id="wellness-heading">Small reads for more informed care.</h2></div><div className="education-grid">{data.education.map((card) => <article key={card.slug}><span>{card.reading_minutes} min read</span><h3>{card.title}</h3><p>{card.description}</p><button type="button" disabled>Article coming soon</button></article>)}</div></section>
  </section>;
}

function DashboardLoading() { return <section className="dashboard-shell" aria-label="Loading dashboard" aria-busy="true"><div className="skeleton skeleton-heading" /><div className="skeleton-actions"><i /><i /><i /></div><div className="dashboard-grid"><i className="skeleton-card" /><i className="skeleton-card" /><i className="skeleton-card" /><i className="skeleton-card" /></div><span className="sr-only">Loading health dashboard</span></section>; }

function NoProfile() { return <div className="dashboard-empty"><span aria-hidden="true">+</span><h2>Create a health profile to personalize this dashboard.</h2><p>Start with only a name. Health and demographic details remain optional.</p><Link href="/profiles">Create a profile</Link></div>; }

function DashboardCard({ title, eyebrow, children, className = "", id }: { title: string; eyebrow: string; children: ReactNode; className?: string; id?: string }) { return <article className={`dashboard-card ${className}`} id={id}><p className="card-eyebrow">{eyebrow}</p><h2>{title}</h2>{children}</article>; }

function ItemList({ items, empty, detail }: { items: TimedItem[]; empty: string; detail: (item: TimedItem) => string }) { return items.length ? <ul className="dashboard-list">{items.map((item) => <li key={item.id}><span className="list-icon" aria-hidden="true">+</span><div><b>{item.title}</b><small>{detail(item)}</small></div></li>)}</ul> : <div className="card-empty"><span aria-hidden="true">OK</span><p>{empty}</p><small>New activity will appear here.</small></div>; }

function EmergencyCard({ items }: { items: Dashboard["emergency_shortcuts"] }) { return <article className="dashboard-card emergency-dashboard"><p className="card-eyebrow">Urgent help</p><h2>Emergency shortcuts</h2>{items.map((item) => <div key={item.action}><b>{item.label}</b><p>{item.description}</p>{item.action === "open-profile" ? <Link href="/profiles">Open profiles</Link> : <strong>Use your local emergency number</strong>}</div>)}</article>; }

function FamilyCard({ family }: { family: Family[] }) { return <DashboardCard title="Family summary" eyebrow="People you care for">{family.length ? <ul className="family-list">{family.map((member) => <li key={member.id}><span>{member.display_name.slice(0, 1).toUpperCase()}</span><div><b>{member.display_name}</b><small>{member.relationship || "Family"}{member.age === null ? "" : ` - ${member.age} years`}</small></div></li>)}</ul> : <div className="card-empty"><p>No family profiles yet</p><Link href="/profiles">Add a family member</Link></div>}</DashboardCard>; }

function PrivacyCard({ privacy }: { privacy: Dashboard["privacy"] }) { return <DashboardCard title="Privacy and sharing" eyebrow="Access status">{privacy ? <dl className="privacy-summary"><div><dt>Current access</dt><dd>{privacy.access_label}</dd></div><div><dt>People with access</dt><dd>{privacy.permission_count}</dd></div><div><dt>Doctor sharing</dt><dd>{privacy.doctor_sharing_enabled ? "Permitted explicitly" : "Off"}</dd></div><div><dt>Family sharing</dt><dd>{privacy.family_sharing_enabled ? "Permitted explicitly" : "Off"}</dd></div></dl> : <p>No active profile.</p>}</DashboardCard>; }
