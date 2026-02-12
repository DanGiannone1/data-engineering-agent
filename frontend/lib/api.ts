const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

// ──────────────────────────────────────────
// Core Types
// ──────────────────────────────────────────

export interface Message {
  id: string;
  thread_id: string;
  client_id: string;
  role: "agent" | "auditor";
  content: string;
  phase: string;
  timestamp: string;
  // Structured pseudocode (when phase is pseudocode_review and role is agent)
  structured_pseudocode?: StructuredPseudocode;
}

export interface TransformStatus {
  instance_id: string;
  runtime_status: "Running" | "Completed" | "Failed" | "Pending" | null;
  custom_status: unknown;
  output: unknown;
  created_time: string | null;
  last_updated_time: string | null;
}

// ──────────────────────────────────────────
// Structured Pseudocode Types
// ──────────────────────────────────────────

export interface StructuredPseudocode {
  version: number;
  summary: string;
  steps: PseudocodeStep[];
  raw_text?: string; // Backwards compat
}

export type StepType = "field_mapping" | "lookup_join" | "business_rule" | "filter" | "calculation" | "output";

export interface BaseStep {
  id: string;
  type: StepType;
  title: string;
  description?: string;
}

export interface FieldMapping {
  source: string;
  target: string;
  transform: "direct" | "rename" | "formula" | "lookup";
  formula?: string;
}

export interface FieldMappingStep extends BaseStep {
  type: "field_mapping";
  mappings: FieldMapping[];
}

export interface LookupJoinStep extends BaseStep {
  type: "lookup_join";
  join_key: {
    source: string;
    lookup: string;
  };
  output_field: string;
  filter?: string;
  sample_mappings?: Array<{ from: string; to: string }>;
}

export interface BusinessRule {
  condition: string;
  action: string;
}

export interface BusinessRuleStep extends BaseStep {
  type: "business_rule";
  rules: BusinessRule[];
}

export interface FilterStep extends BaseStep {
  type: "filter";
  condition: string;
  exclude?: boolean;
}

export interface CalculationStep extends BaseStep {
  type: "calculation";
  output_field: string;
  formula: string;
}

export interface OutputStep extends BaseStep {
  type: "output";
  format: string;
  destination: string;
}

export type PseudocodeStep =
  | FieldMappingStep
  | LookupJoinStep
  | BusinessRuleStep
  | FilterStep
  | CalculationStep
  | OutputStep;

// ──────────────────────────────────────────
// Version History Types
// ──────────────────────────────────────────

export interface PseudocodeVersion {
  version: number;
  timestamp: string;
  changes: string[];
  pseudocode: StructuredPseudocode;
}

// ──────────────────────────────────────────
// Review Types
// ──────────────────────────────────────────

export interface StepComment {
  stepId: string;
  comment: string;
}

export interface ReviewPayload {
  approved: boolean;
  feedback?: string;
  step_comments?: StepComment[];
}

// ──────────────────────────────────────────
// API Functions
// ──────────────────────────────────────────

// Default paths for local development
const DEFAULT_CLIENT_ID = "MAF";
const DEFAULT_MAPPING_PATH = "data/MAF/mapping.xlsx";
const DEFAULT_DATA_PATH = "data/MAF/transactions.xlsx";

export async function startTransform(params?: {
  client_id?: string;
  mapping_path?: string;
  data_path?: string;
}): Promise<{ instance_id: string; client_id: string }> {
  const payload = {
    client_id: params?.client_id || DEFAULT_CLIENT_ID,
    mapping_path: params?.mapping_path || DEFAULT_MAPPING_PATH,
    data_path: params?.data_path || DEFAULT_DATA_PATH,
  };

  const res = await fetch(`${API_BASE}/transform`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to start transform: ${res.statusText}`);
  return res.json();
}

export async function getStatus(instanceId: string): Promise<TransformStatus> {
  const res = await fetch(`${API_BASE}/transform/${instanceId}/status`);
  if (!res.ok) throw new Error(`Failed to get status: ${res.statusText}`);
  return res.json();
}

export async function getMessages(instanceId: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE}/transform/${instanceId}/messages`);
  if (!res.ok) throw new Error(`Failed to get messages: ${res.statusText}`);
  const messages: Message[] = await res.json();

  // Parse structured pseudocode from content if present
  return messages.map((msg) => {
    if (msg.phase === "pseudocode_review" && msg.role === "agent") {
      try {
        const parsed = JSON.parse(msg.content);
        if (parsed.version && parsed.steps) {
          return { ...msg, structured_pseudocode: parsed };
        }
      } catch {
        // Not JSON, keep as plain text
      }
    }
    return msg;
  });
}

export async function submitReview(
  instanceId: string,
  payload: ReviewPayload
): Promise<{ status: string; approved: boolean }> {
  // Convert step_comments to a combined feedback string for backend compatibility
  let feedback = payload.feedback || "";
  if (payload.step_comments && payload.step_comments.length > 0) {
    const stepFeedback = payload.step_comments
      .map((c) => `[Step ${c.stepId}]: ${c.comment}`)
      .join("\n");
    feedback = feedback ? `${feedback}\n\n${stepFeedback}` : stepFeedback;
  }

  const res = await fetch(`${API_BASE}/transform/${instanceId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: payload.approved, feedback }),
  });
  if (!res.ok) throw new Error(`Failed to submit review: ${res.statusText}`);
  return res.json();
}

// ──────────────────────────────────────────
// Utility Functions
// ──────────────────────────────────────────

export function parseStructuredPseudocode(content: string): StructuredPseudocode | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed.version && parsed.steps) {
      return parsed as StructuredPseudocode;
    }
  } catch {
    // Not valid JSON
  }
  return null;
}

export function getStepStats(pseudocode: StructuredPseudocode): {
  fieldMappings: number;
  lookups: number;
  businessRules: number;
} {
  let fieldMappings = 0;
  let lookups = 0;
  let businessRules = 0;

  for (const step of pseudocode.steps) {
    if (step.type === "field_mapping") {
      fieldMappings += step.mappings.length;
    } else if (step.type === "lookup_join") {
      lookups += 1;
    } else if (step.type === "business_rule") {
      businessRules += step.rules.length;
    }
  }

  return { fieldMappings, lookups, businessRules };
}
