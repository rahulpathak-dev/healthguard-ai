import { describe, expect, it } from "vitest";
import { formatDateTime, messages } from "@/lib/i18n";

describe("i18n architecture", () => {
  it("contains English and Hindi message catalogs", () => {
    expect(messages.en.privacyTitle).toMatch(/privacy/i);
    expect(messages.hi.privacyTitle).toContain("????????");
  });

  it("formats dates by locale", () => {
    expect(formatDateTime("2026-07-13T10:00:00Z", "en")).toContain("2026");
    expect(formatDateTime("2026-07-13T10:00:00Z", "hi")).toBeTruthy();
  });
});
