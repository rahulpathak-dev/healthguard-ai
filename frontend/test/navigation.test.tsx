import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Navigation } from "@/components/navigation";
describe("Navigation", () => {
  it("identifies the primary navigation", () => {
    render(<Navigation />);
    expect(
      screen.getByRole("navigation", { name: /primary/i }),
    ).toBeInTheDocument();
  });
});
