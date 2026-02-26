import { test, expect, Page } from "@playwright/test";

// Sample messages that mimic the C# backend output
const CHANGE_DETECTION_MSG = {
  id: "msg-1",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "agent",
  content: "No existing approved code found for CLIENT_001. This is a new client — proceeding with full profiling and pseudocode generation.",
  phase: "change_detection",
  timestamp: "2026-02-26T10:00:00Z",
};

const PSEUDOCODE_MSG = {
  id: "msg-2",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "agent",
  content: [
    "#### Transformation Pseudocode for CLIENT_001",
    "",
    "**Step 1: Load Source Data**",
    "- Read transactions.xlsx from ADLS",
    "- Parse date columns as integers (YYYYMMDD format)",
    "",
    "**Step 2: Apply Field Mappings**",
    "- Map ACCT_NUM → account_number",
    "- Map TXN_DATE → transaction_date",
    "- Map TXN_AMT → amount",
    "",
    "#### Validation Rules",
    "- Filter rows where TS-REV-FLAG is not in exclusion list",
    "- Null-guard on isin() to handle null flag values",
  ].join("\n"),
  phase: "pseudocode_review",
  timestamp: "2026-02-26T10:01:00Z",
};

const AUDITOR_APPROVAL_MSG = {
  id: "msg-3",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "auditor",
  content: "Approved",
  phase: "pseudocode_review",
  timestamp: "2026-02-26T10:02:00Z",
};

const CODE_GEN_MSG = {
  id: "msg-4",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "agent",
  content: "PySpark code generated and executed successfully on Databricks. Output written to abfss://output@deagentstorage2026.dfs.core.windows.net/CLIENT_001/output.parquet",
  phase: "code_generation",
  timestamp: "2026-02-26T10:05:00Z",
};

const INTEGRITY_MSG = {
  id: "msg-5",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "agent",
  content: "Integrity checks passed:\n- Row count: 1,234 (source) → 1,234 (output)\n- Schema: all 15 columns present\n- Duplicates: 0 found\n- Nulls: 2 columns with nulls (warning only — legitimate source nulls)",
  phase: "integrity_check",
  timestamp: "2026-02-26T10:06:00Z",
};

const OUTPUT_REVIEW_MSG = {
  id: "msg-6",
  thread_id: "test-instance-001",
  client_id: "CLIENT_001",
  role: "agent",
  content: "Please review the transformation output. 1,234 rows written with 15 columns. All integrity checks passed.",
  phase: "output_review",
  timestamp: "2026-02-26T10:07:00Z",
};

function makeStatus(runtimeStatus: string) {
  return {
    instance_id: "test-instance-001",
    runtime_status: runtimeStatus,
    custom_status: null,
    output: null,
    created_time: "2026-02-26T10:00:00Z",
    last_updated_time: "2026-02-26T10:07:00Z",
  };
}

/** Set up route mocks for the transform page */
async function mockAPIs(
  page: Page,
  messages: object[],
  status: ReturnType<typeof makeStatus>
) {
  await page.route("**/api/transform/test-instance-001/messages", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(messages),
    });
  });

  await page.route("**/api/transform/test-instance-001/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(status),
    });
  });
}

test.describe("Transform page — message display", () => {
  test("shows waiting message when no messages yet", async ({ page }) => {
    await mockAPIs(page, [], makeStatus("Running"));
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Waiting for agent to start processing")).toBeVisible();
  });

  test("renders agent messages with markdown formatting", async ({ page }) => {
    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG, PSEUDOCODE_MSG],
      makeStatus("Running")
    );
    await page.goto("/transform/test-instance-001");

    // Change detection message appears
    await expect(page.getByText(/No existing approved code found/)).toBeVisible();

    // Markdown heading rendered as bold text (not raw ####)
    await expect(page.getByText("Transformation Pseudocode for CLIENT_001")).toBeVisible();
    await expect(page.locator("text=####")).not.toBeVisible();

    // Bold text rendered
    await expect(page.locator("strong", { hasText: "Step 1: Load Source Data" })).toBeVisible();
    await expect(page.locator("strong", { hasText: "Step 2: Apply Field Mappings" })).toBeVisible();

    // Bullet items rendered in a list
    await expect(page.locator("li", { hasText: "Read transactions.xlsx from ADLS" })).toBeVisible();
    await expect(page.locator("li", { hasText: "Map ACCT_NUM" })).toBeVisible();
  });

  test("shows approval controls during pseudocode review", async ({ page }) => {
    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG, PSEUDOCODE_MSG],
      makeStatus("Running")
    );
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Review required")).toBeVisible();
    await expect(page.getByRole("button", { name: "Approve" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Reject" })).toBeVisible();
  });

  test("shows approval controls during output review", async ({ page }) => {
    await mockAPIs(
      page,
      [
        CHANGE_DETECTION_MSG,
        PSEUDOCODE_MSG,
        AUDITOR_APPROVAL_MSG,
        CODE_GEN_MSG,
        INTEGRITY_MSG,
        OUTPUT_REVIEW_MSG,
      ],
      makeStatus("Running")
    );
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Review required")).toBeVisible();
    await expect(page.getByRole("button", { name: "Approve" })).toBeVisible();
  });
});

test.describe("Transform page — review flow", () => {
  test("approve sends correct payload", async ({ page }) => {
    let capturedBody: Record<string, unknown> | null = null;

    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG, PSEUDOCODE_MSG],
      makeStatus("Running")
    );

    await page.route("**/api/transform/test-instance-001/review", async (route) => {
      capturedBody = JSON.parse(route.request().postData() || "{}");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "review submitted", approved: true }),
      });
    });

    await page.goto("/transform/test-instance-001");
    await page.getByRole("button", { name: "Approve" }).click();

    await expect.poll(() => capturedBody).not.toBeNull();
    expect(capturedBody).toEqual({ approved: true });
  });

  test("reject shows feedback textarea and sends feedback", async ({ page }) => {
    let capturedBody: Record<string, unknown> | null = null;

    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG, PSEUDOCODE_MSG],
      makeStatus("Running")
    );

    await page.route("**/api/transform/test-instance-001/review", async (route) => {
      capturedBody = JSON.parse(route.request().postData() || "{}");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "review submitted", approved: false }),
      });
    });

    await page.goto("/transform/test-instance-001");

    // First click shows textarea
    await page.getByRole("button", { name: "Reject" }).click();
    const textarea = page.getByPlaceholder("Describe what needs to change");
    await expect(textarea).toBeVisible();

    // Fill feedback and submit
    await textarea.fill("Please add currency conversion step");
    await page.getByRole("button", { name: "Submit Feedback" }).click();

    await expect.poll(() => capturedBody).not.toBeNull();
    expect(capturedBody).toEqual({
      approved: false,
      feedback: "Please add currency conversion step",
    });
  });
});

test.describe("Transform page — status display", () => {
  test("shows completed banner", async ({ page }) => {
    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG, PSEUDOCODE_MSG, AUDITOR_APPROVAL_MSG, CODE_GEN_MSG],
      makeStatus("Completed")
    );
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Transformation completed successfully")).toBeVisible();
  });

  test("shows failed banner", async ({ page }) => {
    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG],
      makeStatus("Failed")
    );
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Transformation failed")).toBeVisible();
  });

  test("shows status badge", async ({ page }) => {
    await mockAPIs(
      page,
      [CHANGE_DETECTION_MSG],
      makeStatus("Running")
    );
    await page.goto("/transform/test-instance-001");

    await expect(page.getByText("Running")).toBeVisible();
  });

  test("back button navigates to dashboard", async ({ page }) => {
    await mockAPIs(page, [], makeStatus("Running"));
    await page.goto("/transform/test-instance-001");

    await page.getByText("Back").click();
    await page.waitForURL("**/");
    expect(page.url()).toMatch(/\/$/);
  });
});
