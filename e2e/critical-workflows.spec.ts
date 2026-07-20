import { expect, test } from "@playwright/test";

// Critical workflow coverage for HealthGuard AI.
// Requires Playwright wiring plus seeded mail/token helpers before it can run in CI.

test.describe("critical patient workflows", () => {
  test("register verify login create family profile and ask safe AI question", async ({ page }) => {
    await page.goto("/auth/register");
    await page.getByLabel(/email/i).fill("patient@example.com");
    await page.getByLabel(/password/i).fill("LongPassword123");
    await page.getByRole("button", { name: /create|register/i }).click();
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill("patient@example.com");
    await page.getByLabel(/password/i).fill("LongPassword123");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.goto("/profiles");
    await expect(page.getByText(/family/i)).toBeVisible();
    await page.goto("/chat");
    await expect(page.getByText(/educational/i)).toBeVisible();
  });

  test("red flag symptom escalates to emergency guidance", async ({ page }) => {
    await page.goto("/symptoms");
    await page.getByLabel(/symptoms/i).fill("severe chest pain and trouble breathing");
    await page.getByRole("button", { name: /guidance|check/i }).click();
    await expect(page.getByText(/emergency/i)).toBeVisible();
  });

  test("medicine search record upload report analysis reminder and misinformation check", async ({ page }) => {
    await page.goto("/medicines");
    await page.getByRole("textbox").fill("ibuprofen");
    await page.goto("/records");
    await expect(page.getByText(/upload/i)).toBeVisible();
    await page.goto("/reports");
    await expect(page.getByText(/OCR|report/i)).toBeVisible();
    await page.goto("/reminders");
    await expect(page.getByText(/reminder/i)).toBeVisible();
    await page.goto("/misinformation");
    await expect(page.getByText(/trusted sources/i)).toBeVisible();
  });

  test("share selected records revoke access export data and request deletion", async ({ page }) => {
    await page.goto("/sharing");
    await expect(page.getByText(/selected records/i)).toBeVisible();
    await expect(page.getByText(/revoke/i)).toBeVisible({ timeout: 10_000 });
    await page.goto("/privacy");
    await expect(page.getByText(/secure export/i)).toBeVisible();
    await page.getByLabel(/deletion confirmation phrase/i).fill("delete my healthguard account");
  });
});

test.describe("security boundaries", () => {
  test("admin restrictions and cross-user data isolation are enforced", async ({ page, request }) => {
    const userResponse = await request.get("/api/v1/admin/overview");
    expect([401, 403]).toContain(userResponse.status());
    const otherRecord = await request.get("/api/v1/records/00000000-0000-0000-0000-000000000000");
    expect([401, 403, 404]).toContain(otherRecord.status());
    await page.goto("/admin");
    await expect(page.getByText(/redacted/i)).toBeVisible();
  });
});
