import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EmergencyGuide } from "@/components/emergency-guide";
import { MisinformationChecker } from "@/components/misinformation-checker";
import { ToastProvider } from "@/components/toast-provider";

vi.mock("@/lib/api-client", () => ({
  apiRequest: vi.fn(() => Promise.resolve([])),
}));

describe("safety-critical public flows", () => {
  it("shows emergency action before long educational content", () => {
    render(<EmergencyGuide />);
    expect(screen.getByRole("link", { name: /call \d+/i })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /chest pain/i }),
    ).toBeInTheDocument();
  });

  it("keeps misinformation checker framed around evidence", () => {
    render(
      <ToastProvider>
        <MisinformationChecker />
      </ToastProvider>,
    );
    expect(
      screen.getByRole("heading", { name: /paste a health claim/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/approved sources/i)).toBeInTheDocument();
  });
});
