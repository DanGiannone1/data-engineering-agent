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
// Review Types
// ──────────────────────────────────────────

export interface ReviewPayload {
  approved: boolean;
  feedback?: string;
}

// ──────────────────────────────────────────
// API Functions
// ──────────────────────────────────────────

// Default paths for local development
const DEFAULT_CLIENT_ID = "CLIENT_001";
const DEFAULT_MAPPING_PATH = "mappings/CLIENT_001/mapping.xlsm";
const DEFAULT_DATA_PATH = "data/CLIENT_001/transactions.xlsx";

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
  return res.json();
}

export async function submitReview(
  instanceId: string,
  payload: ReviewPayload
): Promise<{ status: string; approved: boolean }> {
  const res = await fetch(`${API_BASE}/transform/${instanceId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to submit review: ${res.statusText}`);
  return res.json();
}
