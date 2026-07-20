import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PrivacyCenter } from "@/components/privacy-center";
import { ToastProvider } from "@/components/toast-provider";
import { apiRequest } from "@/lib/api-client";

vi.mock("@/lib/api-client", () => ({ apiRequest: vi.fn() }));

describe("PrivacyCenter", () => {
  it("loads privacy counts and displays non-compliance disclaimer", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({ active_sessions: 1, active_sharing_grants: 2, consent_events: 3, pending_exports: 0, deletion_status: null, retention_documentation: ["Exports expire."], legal_compliance_note: "No automatic legal compliance." })
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);
    render(<ToastProvider><PrivacyCenter /></ToastProvider>);
    fireEvent.click(screen.getByRole("button", { name: /load my privacy center/i }));
    expect(await screen.findByText("1")).toBeInTheDocument();
    expect(screen.getByText(/does not claim automatic legal compliance/i)).toBeInTheDocument();
  });

  it("requires explicit deletion phrase input", () => {
    render(<ToastProvider><PrivacyCenter /></ToastProvider>);
    expect(screen.getByLabelText(/deletion confirmation phrase/i)).toBeInTheDocument();
    expect(screen.getByText(/delete my healthguard account/i)).toBeInTheDocument();
  });
});
