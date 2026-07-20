# Health dashboard

The browser loads the dashboard through one authenticated request: `GET /api/v1/dashboard`. An optional `profile_id` selects an accessible personal, family, or explicitly shared profile. If the requested profile is not accessible, the service returns `404` before querying any dashboard source table.

The response deliberately contains summaries only. It includes reminder labels and due dates, record titles and types, analysis status, conversation titles, notification labels, owned-family summaries, and sharing status. It does not return files, report contents, AI messages, private profile notes, medicines, conditions, allergies, or emergency-contact details.

Every activity query is scoped to the authorized active profile and limited to five rows or fewer. Composite indexes cover profile/date and user/unread access patterns. The family panel contains only profiles owned by the user, never unrelated profiles shared by other owners.

The active profile selection remains in component memory and each switch makes one replacement dashboard request. The interface includes skeleton loading, profile-free onboarding, section-level empty states, disabled future actions, and a non-diagnostic emergency shortcut that directs users to local emergency services without assuming a country-specific number.

Dashboard source tables are intentionally small summary boundaries for later reminder, record, report-analysis, conversation, and notification modules. Detailed domain data should remain in their owning services and must not be copied into the dashboard response.
