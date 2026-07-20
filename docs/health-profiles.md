# Personal and family health profiles

Health profiles are private, owner-scoped resources. A user may create one non-deletable personal profile and up to 24 additional family profiles. Exact normalized duplicates are rejected. Family deletion cascades to contacts, health records, and permissions in one database transaction.

All demographic and health fields are optional except the display name and, for family members, relationship. Dates of birth cannot be future dates or imply an age over 130. Diagnosis dates cannot be in the future. Avatar URLs require HTTPS and the current UI uses initials rather than loading third-party images.

Every read and write starts from the authenticated user ID. A profile is returned only when the user owns it or has a persisted `profile_permissions` row. View permission cannot edit. Only owners can delete profiles or manage permissions, and inaccessible resources return `404` to avoid confirming their existence. Privacy preference flags never grant access by themselves.

Health information is normalized into emergency contacts, allergies, current medicines, and chronic conditions. Updates replace only nested collections included in the request. The web editor preserves details such as reactions, dosage, schedules, reasons, summaries, diagnosis dates, and additional contacts.

The active profile is held only in React memory. It is not placed in local storage, session storage, URLs, or cookies. Backend authorization is repeated for every profile request; frontend route protection is navigation assistance only.

## API

- `GET/POST /api/v1/profiles`
- `GET/PATCH/DELETE /api/v1/profiles/{profile_id}`
- `GET/PUT /api/v1/profiles/{profile_id}/permissions`
- `DELETE /api/v1/profiles/{profile_id}/permissions/{grantee_user_id}`
