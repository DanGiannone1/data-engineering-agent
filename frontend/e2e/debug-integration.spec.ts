import { test, expect } from "@playwright/test";

// This test hits the REAL backend on localhost:7071 (no mocks).
// It exercises the full frontend-backend integration.

test.setTimeout(120_000); // 2 min — orchestrator + Spark can take a while

test.describe("Integration: Dashboard → Start Transform", () => {
  test("start transform and verify messages load", async ({ page }) => {
    // Capture console errors
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });

    // Capture network failures
    const networkErrors: string[] = [];
    page.on("requestfailed", (req) => {
      networkErrors.push(`${req.method()} ${req.url()} - ${req.failure()?.errorText}`);
    });

    // 1. Load dashboard
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Data Engineering Agent" })).toBeVisible();
    await expect(page.getByLabel("Client ID")).toHaveValue("CLIENT_001");

    // 2. Click Start — capture the POST /api/transform request
    const [transformResponse] = await Promise.all([
      page.waitForResponse((r) => r.url().includes("/api/transform") && r.request().method() === "POST"),
      page.getByRole("button", { name: "Start Transformation" }).click(),
    ]);

    const transformStatus = transformResponse.status();
    const transformBody = await transformResponse.text();
    console.log(`POST /api/transform → ${transformStatus}: ${transformBody}`);

    if (transformStatus >= 400) {
      throw new Error(`Start transform failed: ${transformStatus} ${transformBody}`);
    }

    const { instance_id } = JSON.parse(transformBody);
    console.log(`Instance ID: ${instance_id}`);

    // 3. Should navigate to /transform/{id}
    await page.waitForURL(`**/transform/${instance_id}`, { timeout: 10000 });
    await expect(page.getByText("Transformation")).toBeVisible();

    // 4. Poll until we get at least one message with real content
    //    The frontend polls every 3s; give the orchestrator up to 30s to produce a message.
    let messages: Record<string, unknown>[] = [];
    await expect.poll(async () => {
      const resp = await page.waitForResponse(
        (r) => r.url().includes(`/api/transform/${instance_id}/messages`) && r.status() === 200,
        { timeout: 15000 }
      );
      messages = await resp.json();
      return messages.length;
    }, { timeout: 30000, message: "Waiting for messages to appear" }).toBeGreaterThan(0);

    console.log(`Got ${messages.length} messages`);
    for (const msg of messages) {
      console.log(`  [${msg.phase}] ${msg.role}: ${String(msg.content).substring(0, 120)}`);
    }

    // 5. Verify messages are NOT the broken [{"raw":""}] format
    for (const msg of messages) {
      expect(msg, "Message should not have 'raw' key (broken serialization)").not.toHaveProperty("raw");
    }

    // Verify message structure
    const first = messages[0];
    expect(first).toHaveProperty("thread_id");
    expect(first).toHaveProperty("content");
    expect(first).toHaveProperty("role");
    expect(first).toHaveProperty("phase");

    // 6. Verify the messages actually rendered in the UI
    const firstContent = String(first.content).substring(0, 40);
    await expect(page.getByText(firstContent, { exact: false })).toBeVisible({ timeout: 5000 });
    console.log("Messages rendered in UI successfully");

    // 7. Check status endpoint works
    const statusResp = await page.waitForResponse(
      (r) => r.url().includes(`/api/transform/${instance_id}/status`) && r.status() === 200,
      { timeout: 10000 }
    );
    const statusBody = await statusResp.json();
    console.log("Status:", JSON.stringify(statusBody, null, 2));
    expect(statusBody).toHaveProperty("runtime_status");

    // 8. Report any console/network errors
    if (consoleErrors.length > 0) {
      console.log("Console errors:", consoleErrors);
    }
    if (networkErrors.length > 0) {
      console.log("Network errors:", networkErrors);
    }
  });
});
