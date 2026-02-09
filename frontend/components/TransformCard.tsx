"use client";

import { useEffect, useState } from "react";
import { getStatus, TransformStatus } from "@/lib/api";
import StatusBadge from "./StatusBadge";

interface Props {
  instanceId: string;
  clientId: string;
  onClick: () => void;
}

export default function TransformCard({ instanceId, clientId, onClick }: Props) {
  const [status, setStatus] = useState<TransformStatus | null>(null);

  useEffect(() => {
    getStatus(instanceId).then(setStatus).catch(() => {});
  }, [instanceId]);

  return (
    <div
      onClick={onClick}
      className="p-4 bg-white rounded-lg shadow hover:shadow-md cursor-pointer transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium text-gray-900">{clientId}</h3>
          <p className="text-xs text-gray-500 mt-1">{instanceId}</p>
        </div>
        <StatusBadge runtimeStatus={status?.runtime_status ?? null} />
      </div>
    </div>
  );
}
