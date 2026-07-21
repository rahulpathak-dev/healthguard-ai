import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SharingConsentCenter } from "@/components/sharing-consent-center";
import { apiRequest } from "@/lib/api-client";

vi.mock("@/lib/api-client", () => ({ apiRequest: vi.fn() }));

describe("SharingConsentCenter", () => {
  it("defaults to read-only selected-record consent language", () => {
    render(<SharingConsentCenter />);
    expect(
      screen.getByText(/only selected records are shared/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/read-only/i).length).toBeGreaterThan(0);
  });

  it("shows a revocation confirmation for active grants", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        {
          id: "grant-1",
          doctor_user_id: "doctor",
          profile_id: "profile",
          record_ids: ["record"],
          scope: "read",
          expires_at: new Date(Date.now() + 60_000).toISOString(),
          revoked_at: null,
          created_at: new Date().toISOString(),
        },
      ])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);
    render(<SharingConsentCenter />);
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    expect(
      await screen.findByRole("button", { name: /revoke/i }),
    ).toBeInTheDocument();
  });
});
