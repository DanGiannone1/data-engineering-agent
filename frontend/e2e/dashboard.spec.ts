import { test, expect } from "@playwright/test";

test.describe("Dashboard page", () => {
  test("renders title, client ID input, and start button", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Data Engineering Agent" })).toBeVisible();
    await expect(page.getByText("Transform source data to DNAV format")).toBeVisible();

    const input = page.getByLabel("Client ID");
    await expect(input).toBeVisible();
    await expect(input).toHaveValue("CLIENT_001");

    const startBtn = page.getByRole("button", { name: "Start Transformation" });
    await expect(startBtn).toBeVisible();
    await expect(startBtn).toBeEnabled();
  });

  test("derives paths from client ID", async ({ page }) => {
    await page.goto("/");

    const input = page.getByLabel("Client ID");
    await input.fill("ACME_INC");

    await expect(page.getByText("mappings/ACME_INC/mapping.xlsm")).toBeVisible();
  });

  test("disables start button when client ID is empty", async ({ page }) => {
    await page.goto("/");

    const input = page.getByLabel("Client ID");
    await input.fill("");

    const startBtn = page.getByRole("button", { name: "Start Transformation" });
    await expect(startBtn).toBeDisabled();
  });

  test("calls API and navigates on start", async ({ page }) => {
    // Mock the transform API
    await page.route("**/api/transform", async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          instance_id: "test-instance-123",
          client_id: "CLIENT_001",
        }),
      });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Start Transformation" }).click();

    await page.waitForURL("**/transform/test-instance-123");
    expect(page.url()).toContain("/transform/test-instance-123");
  });

  test("sends correct payload with custom client ID", async ({ page }) => {
    let capturedBody: Record<string, string> | null = null;

    await page.route("**/api/transform", async (route) => {
      const request = route.request();
      capturedBody = JSON.parse(request.postData() || "{}");
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          instance_id: "inst-456",
          client_id: "CUSTOM_CO",
        }),
      });
    });

    await page.goto("/");
    await page.getByLabel("Client ID").fill("CUSTOM_CO");
    await page.getByRole("button", { name: "Start Transformation" }).click();

    await page.waitForURL("**/transform/inst-456");
    expect(capturedBody).toEqual({
      client_id: "CUSTOM_CO",
      mapping_path: "mappings/CUSTOM_CO/mapping.xlsm",
      data_path: "data/CUSTOM_CO/transactions.xlsx",
    });
  });

  test("shows error when API fails", async ({ page }) => {
    await page.route("**/api/transform", async (route) => {
      await route.fulfill({ status: 500, body: "Internal Server Error" });
    });

    await page.goto("/");
    await page.getByRole("button", { name: "Start Transformation" }).click();

    await expect(page.getByText(/Failed to start transform/)).toBeVisible();
  });
});
