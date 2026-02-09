"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startTransform } from "@/lib/api";
import TransformCard from "@/components/TransformCard";

interface Transform {
  instance_id: string;
  client_id: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [transforms, setTransforms] = useState<Transform[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [clientId, setClientId] = useState("");
  const [mappingPath, setMappingPath] = useState("");
  const [dataPath, setDataPath] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await startTransform({
        client_id: clientId,
        mapping_path: mappingPath,
        data_path: dataPath,
      });
      setTransforms((prev) => [result, ...prev]);
      setShowForm(false);
      setClientId("");
      setMappingPath("");
      setDataPath("");
      router.push(`/transform/${result.instance_id}`);
    } catch (err) {
      alert(`Failed to start transformation: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Data Engineering Agent
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          New Transformation
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-8 p-6 bg-white rounded-lg shadow"
        >
          <h2 className="text-lg font-semibold mb-4">Start Transformation</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client ID
              </label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="CLIENT_001"
                required
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mapping Path (ADLS)
              </label>
              <input
                type="text"
                value={mappingPath}
                onChange={(e) => setMappingPath(e.target.value)}
                placeholder="mappings/CLIENT_001/mapping.xlsx"
                required
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Path (ADLS)
              </label>
              <input
                type="text"
                value={dataPath}
                onChange={(e) => setDataPath(e.target.value)}
                placeholder="data/CLIENT_001/transactions.xlsx"
                required
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Starting..." : "Start"}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-4">
        {transforms.length === 0 && !showForm && (
          <p className="text-gray-500 text-center py-12">
            No transformations yet. Click &quot;New Transformation&quot; to get
            started.
          </p>
        )}
        {transforms.map((t) => (
          <TransformCard
            key={t.instance_id}
            instanceId={t.instance_id}
            clientId={t.client_id}
            onClick={() => router.push(`/transform/${t.instance_id}`)}
          />
        ))}
      </div>
    </div>
  );
}
