const PHASE_LABELS: Record<string, string> = {
  change_detection: "Change Detection",
  pseudocode_review: "Pseudocode Review",
  code_generation: "Code Generation",
  output_review: "Output Review",
};

const STATUS_COLORS: Record<string, string> = {
  Running: "bg-blue-100 text-blue-800",
  Completed: "bg-green-100 text-green-800",
  Failed: "bg-red-100 text-red-800",
  Pending: "bg-yellow-100 text-yellow-800",
};

interface Props {
  runtimeStatus: string | null;
  phase?: string;
}

export default function StatusBadge({ runtimeStatus, phase }: Props) {
  const statusColor = STATUS_COLORS[runtimeStatus ?? "Pending"] ?? "bg-gray-100 text-gray-800";
  const phaseLabel = phase ? PHASE_LABELS[phase] ?? phase : null;

  return (
    <div className="flex items-center gap-2">
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}>
        {runtimeStatus ?? "Pending"}
      </span>
      {phaseLabel && (
        <span className="text-xs text-gray-500">{phaseLabel}</span>
      )}
    </div>
  );
}
